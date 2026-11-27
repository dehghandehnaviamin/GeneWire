use crate::error::{Category, Result, err};
use std::{net::IpAddr, time::Duration};
use url::Url;

pub const MAX_CHUNK: usize = 256 * 1024;

#[derive(Clone)]
pub struct Limits {
    pub ticket_bytes: usize,
    pub result_bytes: u64,
    pub query_timeout: Duration,
    pub idle_timeout: Duration,
    pub ticket_timeout: Duration,
    pub connect_timeout: Duration,
    pub cleanup_timeout: Duration,
    pub max_queries: usize,
}
impl Default for Limits {
    fn default() -> Self {
        Self {
            ticket_bytes: 1024 * 1024,
            result_bytes: 1024 * 1024 * 1024,
            query_timeout: Duration::from_secs(600),
            idle_timeout: Duration::from_secs(30),
            ticket_timeout: Duration::from_secs(30),
            connect_timeout: Duration::from_secs(10),
            cleanup_timeout: Duration::from_secs(5),
            max_queries: 4,
        }
    }
}
impl Limits {
    pub(crate) fn validate(&self) -> Result<()> {
        if self.ticket_bytes == 0
            || self.ticket_bytes > 1024 * 1024
            || self.result_bytes == 0
            || self.max_queries == 0
            || self.max_queries > 4
            || [
                self.query_timeout,
                self.idle_timeout,
                self.ticket_timeout,
                self.connect_timeout,
                self.cleanup_timeout,
            ]
            .iter()
            .any(|d| d.is_zero() || *d > Duration::from_secs(86400))
        {
            return err(Category::InvalidQuery);
        }
        Ok(())
    }
}

/// An operator must explicitly authorize each origin and its resolved IPs.
#[derive(Clone)]
pub struct Destination {
    pub origin: Url,
    pub addresses: Vec<IpAddr>,
    pub allow_ticket_authorization: bool,
}
impl Destination {
    pub fn new(origin: &str, addresses: Vec<IpAddr>) -> Result<Self> {
        let u = Url::parse(origin).map_err(|_| crate::Error::new(Category::InvalidQuery))?;
        if !matches!(u.scheme(), "https" | "http")
            || u.host_str().is_none()
            || !u.username().is_empty()
            || u.password().is_some()
            || u.query().is_some()
            || u.fragment().is_some()
            || u.path() != "/"
            || addresses.is_empty()
        {
            return err(Category::InvalidQuery);
        }
        Ok(Self {
            origin: u,
            addresses,
            allow_ticket_authorization: false,
        })
    }
}

#[derive(Clone)]
pub struct Configuration {
    pub service: Url,
    pub destinations: Vec<Destination>,
    pub control_token: Option<String>,
    pub limits: Limits,
    pub upstream_profile: UpstreamProfile,
    /// Additional operator-configured trust anchors, never read from tickets.
    pub additional_ca_pem: Option<Vec<u8>>,
    /// Only loopback HTTP destinations can use this explicit test mode.
    pub loopback_http_for_tests: bool,
}
impl Configuration {
    pub fn new(service: &str, destinations: Vec<Destination>) -> Result<Self> {
        let u = Url::parse(service).map_err(|_| crate::Error::new(Category::InvalidQuery))?;
        if !matches!(u.scheme(), "https" | "http")
            || !u.path().ends_with('/')
            || !u.username().is_empty()
            || u.password().is_some()
            || u.host_str().is_none()
            || u.query().is_some()
            || u.fragment().is_some()
        {
            return err(Category::InvalidQuery);
        }
        Ok(Self {
            service: u,
            destinations,
            control_token: None,
            limits: Limits::default(),
            upstream_profile: UpstreamProfile::HtsgetBamRegional,
            additional_ca_pem: None,
            loopback_http_for_tests: false,
        })
    }
}

/// A configured subset assumption, never inferred from a successful request.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum UpstreamProfile {
    HtsgetBamRegional,
}

#[derive(Clone)]
pub struct Query {
    object: String,
    reference: String,
    start: u32,
    end: u32,
}
impl Query {
    pub fn new(object: &str, reference: &str, start: u64, end: u64) -> Result<Self> {
        if object.is_empty() || object.len() > 4096 || reference.is_empty() || reference == "*"
            || reference.len() > 4096 || start >= end || end > u32::MAX as u64
            || object.chars().chain(reference.chars()).any(char::is_control)
            // URL dot-segment normalization cannot faithfully preserve these IDs.
            || matches!(object, "." | "..")
        {
            return err(Category::InvalidQuery);
        }
        Ok(Self {
            object: object.into(),
            reference: reference.into(),
            start: start as u32,
            end: end as u32,
        })
    }
    pub(crate) fn url(&self, base: &Url) -> Result<Url> {
        let mut u = base.clone();
        u.path_segments_mut()
            .map_err(|_| crate::Error::new(Category::InvalidQuery))?
            .pop_if_empty()
            .push(&self.object);
        u.query_pairs_mut()
            .append_pair("format", "BAM")
            .append_pair("referenceName", &self.reference)
            .append_pair("start", &self.start.to_string())
            .append_pair("end", &self.end.to_string());
        Ok(u)
    }
}
