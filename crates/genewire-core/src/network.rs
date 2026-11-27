use crate::{Category, Configuration, Error, Result, error::err};
use reqwest::{
    Response,
    header::{HeaderMap, HeaderValue},
};
use std::net::{IpAddr, SocketAddr};
use url::Url;

/// Pin the connector to operator-supplied IPs; do not invoke ambient DNS.
/// No proxy, ambient credentials, automatic redirect, retry or content decoding.
pub(crate) async fn get(
    config: &Configuration,
    mut url: Url,
    mut headers: HeaderMap,
    control: bool,
) -> Result<Response> {
    let original_origin = url.origin();
    for hop in 0..=3 {
        if !url.username().is_empty() || url.password().is_some() || url.fragment().is_some() {
            return err(Category::NetworkPolicy);
        }
        let destination = config
            .destinations
            .iter()
            .find(|d| d.origin.origin() == url.origin())
            .ok_or(Error::new(Category::NetworkPolicy))?;
        if control && url.origin() != config.service.origin() {
            return err(Category::NetworkPolicy);
        }
        // Cross-origin credential remapping is deliberately unsupported in this increment.
        if url.origin() != original_origin {
            return err(Category::NetworkPolicy);
        }
        if !control
            && headers.contains_key("authorization")
            && !destination.allow_ticket_authorization
        {
            return err(Category::NetworkPolicy);
        }
        let host = url.host_str().ok_or(Error::new(Category::NetworkPolicy))?;
        let port = url
            .port_or_known_default()
            .ok_or(Error::new(Category::NetworkPolicy))?;
        let addresses: Vec<SocketAddr> = match url.host() {
            Some(url::Host::Ipv4(a)) => vec![SocketAddr::new(a.into(), port)],
            Some(url::Host::Ipv6(a)) => vec![SocketAddr::new(a.into(), port)],
            _ => destination
                .addresses
                .iter()
                .map(|ip| SocketAddr::new(*ip, port))
                .collect(),
        };
        if addresses.is_empty()
            || addresses
                .iter()
                .any(|a| !destination.addresses.contains(&a.ip()))
        {
            return err(Category::NetworkPolicy);
        }
        if url.scheme() != "https"
            && !(url.scheme() == "http"
                && config.loopback_http_for_tests
                && addresses.iter().all(|a| a.ip().is_loopback()))
        {
            return err(Category::NetworkPolicy);
        }
        let mut builder = reqwest::Client::builder()
            .no_proxy()
            .no_gzip()
            .no_brotli()
            .no_deflate()
            .no_zstd()
            .redirect(reqwest::redirect::Policy::none())
            .retry(reqwest::retry::never())
            .referer(false)
            .http1_only()
            .pool_max_idle_per_host(0)
            .connect_timeout(config.limits.connect_timeout)
            .tls_version_min(reqwest::tls::Version::TLS_1_2)
            .tls_sslkeylogfile(false)
            .resolve_to_addrs(host, &addresses);
        if let Some(pem) = &config.additional_ca_pem {
            builder = builder.tls_certs_merge(
                reqwest::Certificate::from_pem_bundle(pem)
                    .map_err(|_| Error::new(Category::InvalidQuery))?,
            );
        }
        let client = builder
            .build()
            .map_err(|_| Error::new(Category::InternalFailure))?;
        headers.insert("accept-encoding", HeaderValue::from_static("identity"));
        if control && let Some(token) = &config.control_token {
            headers.insert(
                "authorization",
                HeaderValue::from_str(&format!("Bearer {token}"))
                    .map_err(|_| Error::new(Category::InvalidQuery))?,
            );
        }
        let response = tokio::time::timeout(
            config.limits.idle_timeout,
            client.get(url.clone()).headers(headers.clone()).send(),
        )
        .await
        .map_err(|_| Error::new(Category::DeadlineExceeded))?
        .map_err(|e| {
            // Connection setup includes TLS validation. Fail closed rather than
            // retry a certificate failure as an ordinary dropped body.
            if e.is_timeout() {
                Error::new(Category::DeadlineExceeded)
            } else if e.is_connect() {
                Error::new(Category::NetworkPolicy)
            } else {
                classify(e)
            }
        })?;
        // Pinning is authoritative; checking the peer also detects connector regressions.
        if response
            .remote_addr()
            .is_none_or(|a| !addresses.contains(&a))
        {
            return err(Category::NetworkPolicy);
        }
        if response.status().is_redirection() {
            if hop == 3 {
                return err(Category::NetworkPolicy);
            }
            let location = response
                .headers()
                .get("location")
                .and_then(|h| h.to_str().ok())
                .ok_or(Error::new(Category::ResponseInvalid))?;
            url = url
                .join(location)
                .map_err(|_| Error::new(Category::ResponseInvalid))?;
            continue;
        }
        return Ok(response);
    }
    err(Category::NetworkPolicy)
}

pub(crate) fn classify(error: reqwest::Error) -> Error {
    // Never include reqwest's Display/Debug: it can contain a signed URL.
    Error::new(if error.is_timeout() {
        Category::DeadlineExceeded
    } else {
        Category::TransportFailed
    })
}

pub(crate) fn identity(response: &Response) -> Result<()> {
    if response
        .headers()
        .get_all("content-encoding")
        .iter()
        .any(|h| h.as_bytes() != b"identity")
    {
        return err(Category::ResponseInvalid);
    }
    Ok(())
}

pub(crate) fn length(response: &Response) -> Result<Option<u64>> {
    response
        .headers()
        .get("content-length")
        .map(|h| {
            h.to_str()
                .ok()
                .filter(|s| !s.is_empty() && s.bytes().all(|c| c.is_ascii_digit()))
                .and_then(|s| s.parse().ok())
                .ok_or(Error::new(Category::ResponseInvalid))
        })
        .transpose()
}

pub fn ip(s: &str) -> Result<IpAddr> {
    s.parse().map_err(|_| Error::new(Category::InvalidQuery))
}
