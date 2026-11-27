use crate::{Category, Error, Result, error::err, model::MAX_CHUNK};
use base64::{Engine, engine::general_purpose::STANDARD};
use bytes::Bytes;
use reqwest::header::{HeaderMap, HeaderName, HeaderValue};
use serde::{
    Deserialize, Deserializer,
    de::{self, MapAccess, SeqAccess, Visitor},
};
use serde_json::Value;
use std::{collections::HashSet, fmt};
use url::Url;

pub(crate) enum Block {
    Inline(Bytes),
    Http {
        url: Url,
        headers: HeaderMap,
        range: Option<(u64, u64)>,
    },
}

// Deserialize recursively before converting to Value so duplicate keys cannot be lost.
struct Unique(Value);
impl<'de> Deserialize<'de> for Unique {
    fn deserialize<D: Deserializer<'de>>(d: D) -> std::result::Result<Self, D::Error> {
        struct V;
        impl<'de> Visitor<'de> for V {
            type Value = Unique;
            fn expecting(&self, f: &mut fmt::Formatter) -> fmt::Result {
                f.write_str("JSON")
            }
            fn visit_map<M: MapAccess<'de>>(
                self,
                mut m: M,
            ) -> std::result::Result<Unique, M::Error> {
                let mut seen = HashSet::new();
                let mut out = serde_json::Map::new();
                while let Some(k) = m.next_key::<String>()? {
                    if !seen.insert(k.clone()) {
                        return Err(de::Error::custom("duplicate key"));
                    }
                    out.insert(k, m.next_value::<Unique>()?.0);
                }
                Ok(Unique(Value::Object(out)))
            }
            fn visit_seq<S: SeqAccess<'de>>(
                self,
                mut a: S,
            ) -> std::result::Result<Unique, S::Error> {
                let mut out = Vec::new();
                while let Some(v) = a.next_element::<Unique>()? {
                    out.push(v.0);
                }
                Ok(Unique(Value::Array(out)))
            }
            fn visit_str<E: de::Error>(self, s: &str) -> std::result::Result<Unique, E> {
                Ok(Unique(Value::String(s.into())))
            }
            fn visit_bool<E: de::Error>(self, v: bool) -> std::result::Result<Unique, E> {
                Ok(Unique(Value::Bool(v)))
            }
            fn visit_i64<E: de::Error>(self, v: i64) -> std::result::Result<Unique, E> {
                Ok(Unique(v.into()))
            }
            fn visit_u64<E: de::Error>(self, v: u64) -> std::result::Result<Unique, E> {
                Ok(Unique(v.into()))
            }
            fn visit_f64<E: de::Error>(self, v: f64) -> std::result::Result<Unique, E> {
                serde_json::Number::from_f64(v)
                    .map(|n| Unique(Value::Number(n)))
                    .ok_or_else(|| de::Error::custom("number"))
            }
            fn visit_unit<E: de::Error>(self) -> std::result::Result<Unique, E> {
                Ok(Unique(Value::Null))
            }
        }
        d.deserialize_any(V)
    }
}

fn depth(v: &Value, n: usize) -> bool {
    n <= 16
        && match v {
            Value::Object(m) => m.values().all(|v| depth(v, n + 1)),
            Value::Array(a) => a.iter().all(|v| depth(v, n + 1)),
            _ => true,
        }
}

pub(crate) fn range(s: &str) -> Result<(u64, u64)> {
    let r = s
        .strip_prefix("bytes=")
        .ok_or(Error::new(Category::Unsupported))?;
    let (a, b) = r.split_once('-').ok_or(Error::new(Category::Unsupported))?;
    if a.is_empty() || b.is_empty() || !a.bytes().chain(b.bytes()).all(|b| b.is_ascii_digit()) {
        return err(Category::Unsupported);
    }
    let a: u64 = a.parse().map_err(|_| Error::new(Category::Unsupported))?;
    let b: u64 = b.parse().map_err(|_| Error::new(Category::Unsupported))?;
    if a > b || b - a == u64::MAX {
        return err(Category::Unsupported);
    }
    Ok((a, b))
}

pub(crate) fn parse(data: &[u8]) -> Result<Vec<Block>> {
    let root = serde_json::from_slice::<Unique>(data)
        .map_err(|_| Error::new(Category::TicketInvalid))?
        .0;
    if !depth(&root, 0) {
        return err(Category::ResourceLimit);
    }
    let h = root
        .get("htsget")
        .and_then(Value::as_object)
        .ok_or(Error::new(Category::TicketInvalid))?;
    if h.get("format").and_then(Value::as_str) != Some("BAM") {
        return err(Category::TicketInvalid);
    }
    let urls = h
        .get("urls")
        .and_then(Value::as_array)
        .ok_or(Error::new(Category::TicketInvalid))?;
    if urls.is_empty() {
        return err(Category::TicketInvalid);
    }
    if urls.len() > 1024 {
        return err(Category::ResourceLimit);
    }
    urls.iter()
        .map(|b| {
            let text = b
                .get("url")
                .and_then(Value::as_str)
                .ok_or(Error::new(Category::TicketInvalid))?;
            if let Some(c) = b.get("class")
                && c.as_str().is_none()
            {
                return err(Category::TicketInvalid);
            }
            let mut headers = HeaderMap::new();
            let mut header_bytes = 0;
            if let Some(h) = b.get("headers") {
                let h = h.as_object().ok_or(Error::new(Category::TicketInvalid))?;
                if h.len() > 64 {
                    return err(Category::ResourceLimit);
                }
                for (k, v) in h {
                    let v = v.as_str().ok_or(Error::new(Category::TicketInvalid))?;
                    header_bytes += k.len() + v.len();
                    if header_bytes > 32 * 1024 {
                        return err(Category::ResourceLimit);
                    }
                    let name = HeaderName::from_bytes(k.as_bytes())
                        .map_err(|_| Error::new(Category::TicketInvalid))?;
                    if matches!(
                        name.as_str(),
                        "host"
                            | "cookie"
                            | "proxy-authorization"
                            | "connection"
                            | "proxy-connection"
                            | "keep-alive"
                            | "te"
                            | "trailer"
                            | "transfer-encoding"
                            | "upgrade"
                            | "content-length"
                            | "accept-encoding"
                            | "referer"
                    ) {
                        return err(Category::NetworkPolicy);
                    }
                    if headers.contains_key(&name) {
                        return err(Category::TicketInvalid);
                    }
                    headers.insert(
                        name,
                        HeaderValue::from_str(v)
                            .map_err(|_| Error::new(Category::TicketInvalid))?,
                    );
                }
            }
            if text.starts_with("data:") {
                if !headers.is_empty() {
                    return err(Category::Unsupported);
                }
                let (meta, data) = text
                    .split_once(',')
                    .ok_or(Error::new(Category::TicketInvalid))?;
                if !meta.ends_with(";base64") {
                    return err(Category::Unsupported);
                }
                if data.len() > MAX_CHUNK.div_ceil(3) * 4 {
                    return err(Category::ResourceLimit);
                }
                let bytes = STANDARD
                    .decode(data)
                    .map_err(|_| Error::new(Category::TicketInvalid))?;
                if bytes.len() > MAX_CHUNK {
                    return err(Category::ResourceLimit);
                }
                Ok(Block::Inline(bytes.into()))
            } else {
                let url = Url::parse(text).map_err(|_| Error::new(Category::TicketInvalid))?;
                let range = headers
                    .get("range")
                    .map(|v| {
                        v.to_str()
                            .map_err(|_| Error::new(Category::TicketInvalid))
                            .and_then(range)
                    })
                    .transpose()?;
                Ok(Block::Http {
                    url,
                    headers,
                    range,
                })
            }
        })
        .collect()
}
