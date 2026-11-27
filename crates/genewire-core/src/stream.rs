use crate::{
    Category, Configuration, Error, MAX_CHUNK, Query, Result, UpstreamProfile,
    error::err,
    network,
    ticket::{self, Block},
};
use bytes::Bytes;
use reqwest::{Response, header::HeaderMap};
use std::{
    collections::VecDeque,
    panic::{AssertUnwindSafe, catch_unwind},
    sync::{Arc, Mutex, MutexGuard, Weak},
    thread,
    time::{Duration, Instant, SystemTime},
};
use tokio::{runtime::Runtime, task::JoinHandle};
use tokio_util::sync::CancellationToken;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum State {
    New,
    Ticketing,
    Fetching,
    RetryWait,
    Draining,
    TransportComplete,
    Failed,
    Cancelled,
}
impl State {
    pub fn terminal(self) -> bool {
        matches!(
            self,
            Self::TransportComplete | Self::Failed | Self::Cancelled
        )
    }
}
#[derive(Clone, Debug)]
pub struct Report {
    pub state: State,
    pub error: Option<Error>,
    pub bytes_delivered: u64,
    pub retries: usize,
    pub cleanup_complete: bool,
    /// Last active phase; retained unchanged after a terminal outcome.
    pub phase: Phase,
    /// An unsuccessful query exposed bytes that callers must invalidate.
    pub may_have_partial_output: bool,
    pub cleanup: Cleanup,
    pub cleanup_error: Option<Error>,
    pub upstream_profile: UpstreamProfile,
    pub capability_evidence: CapabilityEvidence,
    pub memory: MemoryReport,
}
/// Logical data-plane byte accounting, not allocator/TLS/process memory.
#[derive(Clone, Debug, Default)]
pub struct MemoryReport {
    pub current_payload_bytes: u64,
    pub peak_payload_bytes: u64,
    pub largest_http_fragment_bytes: u64,
    pub rust_output_copy_bytes: u64,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum CapabilityEvidence {
    Configured,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Cleanup {
    NotStarted,
    InProgress,
    Complete,
    Failed,
}
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Phase {
    Admission,
    Ticketing,
    Fetching,
    Draining,
}
fn lock<T>(m: &Mutex<T>) -> MutexGuard<'_, T> {
    m.lock().unwrap_or_else(|e| e.into_inner())
}
struct Shared {
    report: Mutex<Report>,
    cancel: CancellationToken,
}
impl Shared {
    fn payload(&self, retained: usize, output_copy: usize, fragment: usize) {
        let mut r = lock(&self.report);
        r.memory.current_payload_bytes = (retained + output_copy) as u64;
        r.memory.peak_payload_bytes = r
            .memory
            .peak_payload_bytes
            .max(r.memory.current_payload_bytes);
        r.memory.largest_http_fragment_bytes =
            r.memory.largest_http_fragment_bytes.max(fragment as u64);
        r.memory.rust_output_copy_bytes = r
            .memory
            .rust_output_copy_bytes
            .saturating_add(output_copy as u64);
    }
    fn fail(&self, error: Error) {
        let mut r = lock(&self.report);
        if !r.state.terminal() {
            r.state = if error.category == Category::Cancelled {
                State::Cancelled
            } else {
                State::Failed
            };
            r.error = Some(error);
            r.may_have_partial_output = r.bytes_delivered > 0;
        }
        self.cancel.cancel();
    }
    fn state(&self, state: State) {
        let mut r = lock(&self.report);
        if !r.state.terminal() {
            r.state = state;
            r.phase = match state {
                State::Ticketing => Phase::Ticketing,
                State::Fetching => Phase::Fetching,
                State::Draining => Phase::Draining,
                _ => r.phase,
            };
        }
    }
}
struct Admission {
    closed: bool,
    queries: Vec<Weak<Inner>>,
}
struct Owner {
    runtime: Runtime,
    config: Configuration,
    admission: Mutex<Admission>,
}
pub struct Client {
    owner: Arc<Owner>,
}
impl Client {
    pub fn new(config: Configuration) -> Result<Self> {
        config.limits.validate()?;
        if let Some(pem) = &config.additional_ca_pem {
            if pem.is_empty() || pem.len() > 65536 {
                return err(Category::InvalidQuery);
            }
            let certs = reqwest::Certificate::from_pem_bundle(pem)
                .map_err(|_| Error::new(Category::InvalidQuery))?;
            if certs.len() != 1 {
                return err(Category::InvalidQuery);
            }
            // PEM decoding is lazy under rustls. Validate DER in a root store
            // before admitting a query; no network request is made here.
            reqwest::Client::builder()
                .no_proxy()
                .tls_certs_only(certs)
                .build()
                .map_err(|_| Error::new(Category::InvalidQuery))?;
        }
        if config.destinations.is_empty() || tokio::runtime::Handle::try_current().is_ok() {
            return err(Category::InvalidQuery);
        }
        if let Some(t) = &config.control_token {
            reqwest::header::HeaderValue::from_str(&format!("Bearer {t}"))
                .map_err(|_| Error::new(Category::InvalidQuery))?;
        }
        let runtime = tokio::runtime::Builder::new_multi_thread()
            .worker_threads(2)
            .enable_all()
            .build()
            .map_err(|_| Error::new(Category::InternalFailure))?;
        Ok(Self {
            owner: Arc::new(Owner {
                runtime,
                config,
                admission: Mutex::new(Admission {
                    closed: false,
                    queries: Vec::new(),
                }),
            }),
        })
    }
    pub fn open(&self, query: Query) -> Result<Stream> {
        if tokio::runtime::Handle::try_current().is_ok() {
            return err(Category::InvalidState);
        }
        let mut admission = lock(&self.owner.admission);
        admission.queries.retain(|q| {
            q.upgrade()
                .is_some_and(|q| !lock(&q.shared.report).cleanup_complete)
        });
        if admission.closed {
            return err(Category::InvalidState);
        }
        if admission.queries.len() >= self.owner.config.limits.max_queries {
            return err(Category::ResourceLimit);
        }
        let shared = Arc::new(Shared {
            report: Mutex::new(Report {
                state: State::New,
                error: None,
                bytes_delivered: 0,
                retries: 0,
                cleanup_complete: false,
                phase: Phase::Admission,
                may_have_partial_output: false,
                cleanup: Cleanup::NotStarted,
                cleanup_error: None,
                upstream_profile: self.owner.config.upstream_profile,
                capability_evidence: CapabilityEvidence::Configured,
                memory: MemoryReport::default(),
            }),
            cancel: CancellationToken::new(),
        });
        let task_shared = shared.clone();
        let timeout = self.owner.config.limits.query_timeout;
        let expires = tokio::time::Instant::now() + timeout;
        let watchdog = self.owner.runtime.spawn(async move {
            tokio::select! {
                _ = task_shared.cancel.cancelled() => {},
                _ = tokio::time::sleep_until(expires) => task_shared.fail(Error::new(Category::DeadlineExceeded)),
            }
        });
        let inner = Arc::new(Inner {
            owner: self.owner.clone(),
            shared,
            reader: Mutex::new(Reader {
                query,
                blocks: None,
                current: None,
                pending: Bytes::new(),
                pending_storage_bytes: 0,
                accepted: 0,
                exposed: false,
                block_received: 0,
                attempts: 0,
                validator: None,
                expected: None,
            }),
            watchdog: Mutex::new(Some(watchdog)),
            cleanup: Mutex::new(()),
            #[cfg(test)]
            hooks: TestHooks::default(),
        });
        admission.queries.push(Arc::downgrade(&inner));
        Ok(Stream { inner })
    }
    pub fn close(&self) -> Result<()> {
        if tokio::runtime::Handle::try_current().is_ok() {
            return err(Category::InvalidState);
        }
        let queries = {
            let mut a = lock(&self.owner.admission);
            a.closed = true;
            a.queries
                .iter()
                .filter_map(Weak::upgrade)
                .collect::<Vec<_>>()
        };
        for q in &queries {
            q.shared.fail(Error::new(Category::Cancelled));
        }
        let deadline = Instant::now() + self.owner.config.limits.cleanup_timeout;
        for q in queries {
            Stream { inner: q }.close_until(deadline)?;
        }
        Ok(())
    }
}
struct Inner {
    owner: Arc<Owner>,
    shared: Arc<Shared>,
    reader: Mutex<Reader>,
    watchdog: Mutex<Option<JoinHandle<()>>>,
    cleanup: Mutex<()>,
    #[cfg(test)]
    hooks: TestHooks,
}
#[cfg(test)]
#[derive(Default)]
struct TestHooks {
    panic_read: std::sync::atomic::AtomicBool,
    before_handoff: Mutex<Option<Box<dyn FnOnce() + Send>>>,
    after_handoff: Mutex<Option<Box<dyn FnOnce() + Send>>>,
}
impl Drop for Inner {
    fn drop(&mut self) {
        self.shared.fail(Error::new(Category::Cancelled));
        if let Some(task) = lock(&self.watchdog).take() {
            task.abort();
        }
    }
}
#[derive(Clone)]
pub struct Stream {
    inner: Arc<Inner>,
}
impl Stream {
    pub fn result(&self) -> Report {
        lock(&self.inner.shared.report).clone()
    }
    pub fn cancel(&self) {
        self.inner.shared.fail(Error::new(Category::Cancelled));
    }
    pub fn finish(&self) -> Result<Report> {
        let report = self.result();
        if let Some(e) = report.error {
            return Err(e);
        }
        if report.state != State::TransportComplete {
            return err(Category::InvalidState);
        }
        Ok(report)
    }
    pub fn read_chunk(&self, max_bytes: usize) -> Result<Vec<u8>> {
        if max_bytes == 0 || max_bytes > MAX_CHUNK {
            return err(Category::InvalidQuery);
        }
        if tokio::runtime::Handle::try_current().is_ok() {
            return err(Category::InvalidState);
        }
        let mut reader = self
            .inner
            .reader
            .try_lock()
            .map_err(|_| Error::new(Category::InvalidState))?;
        let shared = &self.inner.shared;
        {
            let r = lock(&shared.report);
            if let Some(e) = &r.error {
                return Err(e.clone());
            }
            if r.state == State::TransportComplete {
                return Ok(Vec::new());
            }
        }
        let output = catch_unwind(AssertUnwindSafe(|| {
            #[cfg(test)]
            if self.inner.hooks.panic_read.swap(false, std::sync::atomic::Ordering::SeqCst) {
                panic!("injected native reader failure");
            }
            self.inner.owner.runtime.block_on(async {
            tokio::select! { biased;
                _ = shared.cancel.cancelled() => Err(lock(&shared.report).error.clone().unwrap_or(Error::new(Category::Cancelled))),
                result = reader.read(&self.inner.owner.config, shared, max_bytes) => result,
            }
        })})).unwrap_or_else(|_| err(Category::InternalFailure));
        #[cfg(test)]
        if let Some(hook) = lock(&self.inner.hooks.before_handoff).take() {
            hook();
        }
        match output {
            Ok(data) => {
                let mut r = lock(&shared.report);
                // This lock is the public handoff's linearization point.
                r.memory.current_payload_bytes = reader.retained_payload() as u64;
                if let Some(e) = &r.error {
                    return Err(e.clone());
                }
                if data.is_empty() {
                    r.state = State::TransportComplete;
                    shared.cancel.cancel();
                } else {
                    reader.exposed = reader.current.is_some();
                    r.bytes_delivered += data.len() as u64;
                }
                drop(r);
                #[cfg(test)]
                if let Some(hook) = lock(&self.inner.hooks.after_handoff).take() {
                    hook();
                }
                Ok(data)
            }
            Err(error) => {
                shared.payload(reader.retained_payload(), 0, 0);
                shared.fail(error);
                Err(lock(&shared.report)
                    .error
                    .clone()
                    .unwrap_or(Error::new(Category::InternalFailure)))
            }
        }
    }
    pub fn close(&self) -> Result<()> {
        self.close_until(Instant::now() + self.inner.owner.config.limits.cleanup_timeout)
    }
    fn close_until(&self, deadline: Instant) -> Result<()> {
        if tokio::runtime::Handle::try_current().is_ok() {
            return err(Category::InvalidState);
        }
        self.cancel();
        {
            let mut report = lock(&self.inner.shared.report);
            if report.cleanup_complete {
                return Ok(());
            }
            report.cleanup = Cleanup::InProgress;
        }
        // A competing close must not wait on an unbounded mutex acquisition.
        let _cleanup = loop {
            if let Ok(guard) = self.inner.cleanup.try_lock() {
                break guard;
            }
            if Instant::now() >= deadline {
                return self.cleanup_failed(Category::CleanupTimeout);
            }
            thread::sleep(Duration::from_millis(1));
        };
        loop {
            if let Ok(mut reader) = self.inner.reader.try_lock() {
                reader.current = None;
                reader.pending = Bytes::new();
                reader.pending_storage_bytes = 0;
                reader.blocks = None;
                self.inner.shared.payload(0, 0, 0);
                break;
            }
            if Instant::now() >= deadline {
                return self.cleanup_failed(Category::CleanupTimeout);
            }
            thread::sleep(Duration::from_millis(1));
        }
        let mut task = lock(&self.inner.watchdog);
        if let Some(handle) = task.as_mut() {
            let left = deadline.saturating_duration_since(Instant::now());
            let joined = self
                .inner
                .owner
                .runtime
                .block_on(async { tokio::time::timeout(left, handle).await });
            match joined {
                Ok(Ok(())) => {}
                Ok(Err(_)) => {
                    task.take();
                    return self.cleanup_failed(Category::InternalFailure);
                }
                Err(_) => return self.cleanup_failed(Category::CleanupTimeout),
            }
            task.take();
        }
        let mut report = lock(&self.inner.shared.report);
        report.cleanup_complete = true;
        report.cleanup = Cleanup::Complete;
        report.cleanup_error = None;
        Ok(())
    }
    fn cleanup_failed(&self, category: Category) -> Result<()> {
        let mut report = lock(&self.inner.shared.report);
        if !report.cleanup_complete {
            report.cleanup = if category == Category::CleanupTimeout {
                Cleanup::InProgress
            } else {
                Cleanup::Failed
            };
            report.cleanup_error = Some(Error::new(category));
        }
        err(category)
    }
}

struct Reader {
    query: Query,
    blocks: Option<VecDeque<Block>>,
    current: Option<Response>,
    pending: Bytes,
    // A sliced Bytes view retains the whole accepted fragment allocation extent.
    pending_storage_bytes: usize,
    accepted: u64,
    exposed: bool,
    block_received: u64,
    attempts: usize,
    validator: Option<(Option<String>, Option<String>)>,
    expected: Option<u64>,
}
impl Reader {
    fn inline_bytes(&self) -> usize {
        self.blocks
            .as_ref()
            .into_iter()
            .flatten()
            .map(|block| match block {
                Block::Inline(data) => data.len(),
                _ => 0,
            })
            .sum()
    }
    fn retained_payload(&self) -> usize {
        self.pending_storage_bytes + self.inline_bytes()
    }
    async fn read(
        &mut self,
        config: &Configuration,
        shared: &Shared,
        max: usize,
    ) -> Result<Vec<u8>> {
        if self.blocks.is_none() {
            shared.state(State::Ticketing);
            // One phase budget covers all attempts, body reads, parsing and waits.
            self.blocks = Some(
                tokio::time::timeout(config.limits.ticket_timeout, self.ticket(config, shared))
                    .await
                    .map_err(|_| Error::new(Category::DeadlineExceeded))??
                    .into(),
            );
            shared.payload(self.retained_payload(), 0, 0);
            shared.state(State::Fetching);
        }
        loop {
            if !self.pending.is_empty() {
                let output = self.pending.split_to(max.min(self.pending.len())).to_vec();
                shared.payload(self.retained_payload(), output.len(), 0);
                return Ok(output);
            }
            // An empty Bytes view may still retain its entire prior allocation.
            // Release it before awaiting the next library-owned HTTP fragment.
            self.pending = Bytes::new();
            self.pending_storage_bytes = 0;
            shared.payload(self.retained_payload(), 0, 0);
            if let Some(response) = self.current.as_mut() {
                // Start the idle clock for this active poll, excluding caller pauses.
                let chunk = tokio::time::timeout(config.limits.idle_timeout, response.chunk())
                    .await
                    .map_err(|_| Error::new(Category::DeadlineExceeded))?;
                match chunk {
                    Ok(Some(bytes)) => {
                        shared.payload(self.retained_payload(), 0, bytes.len());
                        // Library body fragments are not public chunk boundaries.
                        // Reserve space for remaining inline bytes and one owned
                        // public read copy in the draft 2 MiB payload window.
                        let inline_bytes = self.inline_bytes();
                        if bytes.len() > 2 * 1024 * 1024 - MAX_CHUNK - inline_bytes {
                            return err(Category::ResourceLimit);
                        }
                        self.accepted = self
                            .accepted
                            .checked_add(bytes.len() as u64)
                            .ok_or(Error::new(Category::ResourceLimit))?;
                        self.block_received += bytes.len() as u64;
                        if self.accepted > config.limits.result_bytes
                            || self.expected.is_some_and(|n| self.block_received > n)
                        {
                            return err(if self.accepted > config.limits.result_bytes {
                                Category::ResourceLimit
                            } else {
                                Category::ResponseInvalid
                            });
                        }
                        self.pending_storage_bytes = bytes.len();
                        self.pending = bytes;
                        shared.payload(self.retained_payload(), 0, 0);
                    }
                    Ok(None) => {
                        if self.expected.is_some_and(|n| self.block_received != n) {
                            return err(Category::ResponseInvalid);
                        }
                        self.current = None;
                        self.blocks.as_mut().expect("validated blocks").pop_front();
                        self.reset_block();
                    }
                    Err(error) => {
                        if error.is_timeout() {
                            return err(Category::DeadlineExceeded);
                        }
                        // A declared length failure is a validation failure, never a replay.
                        if self.expected.is_some() {
                            return err(Category::ResponseInvalid);
                        }
                        let error = network::classify(error);
                        if self.exposed {
                            return Err(error);
                        }
                        self.current = None;
                        self.accepted -= self.block_received;
                        self.block_received = 0;
                        self.retry(shared, None).await?;
                    }
                }
                continue;
            }
            let Some(block) = self.blocks.as_mut().and_then(VecDeque::front_mut) else {
                shared.state(State::Draining);
                return Ok(Vec::new());
            };
            match block {
                Block::Inline(bytes) => {
                    if self.accepted + bytes.len() as u64 > config.limits.result_bytes {
                        return err(Category::ResourceLimit);
                    }
                    self.accepted += bytes.len() as u64;
                    self.pending = std::mem::take(bytes);
                    self.pending_storage_bytes = self.pending.len();
                    self.blocks.as_mut().expect("validated blocks").pop_front();
                    shared.payload(self.retained_payload(), 0, 0);
                    self.reset_block();
                }
                Block::Http {
                    url,
                    headers,
                    range,
                } => {
                    self.attempts += 1;
                    let response = network::get(config, url.clone(), headers.clone(), false).await;
                    let response = match response {
                        Ok(r) => r,
                        Err(e) if e.category == Category::TransportFailed && !self.exposed => {
                            self.retry(shared, None).await?;
                            continue;
                        }
                        Err(e) => return Err(e),
                    };
                    if transient_status(&response) {
                        let wait = server_wait(&response);
                        drop(response);
                        self.retry(shared, wait).await?;
                        continue;
                    }
                    status(&response)?;
                    network::identity(&response)?;
                    let length = network::length(&response)?;
                    if let Some((a, b)) = *range {
                        if response.status() != 206 {
                            return err(Category::ResponseInvalid);
                        }
                        let cr = response
                            .headers()
                            .get("content-range")
                            .and_then(|h| h.to_str().ok())
                            .ok_or(Error::new(Category::ResponseInvalid))?;
                        let (prefix, total) = cr
                            .split_once('/')
                            .ok_or(Error::new(Category::ResponseInvalid))?;
                        if prefix != format!("bytes {a}-{b}")
                            || (total != "*" && total.parse::<u64>().ok().is_none_or(|n| n <= b))
                            || length.is_some_and(|n| n != b - a + 1)
                        {
                            return err(Category::ResponseInvalid);
                        }
                        self.expected = Some(b - a + 1);
                    } else {
                        if response.status() != 200 {
                            return err(Category::ResponseInvalid);
                        }
                        self.expected = length;
                    }
                    if self
                        .expected
                        .is_some_and(|n| n > config.limits.result_bytes - self.accepted)
                    {
                        return err(Category::ResourceLimit);
                    }
                    let validator = (
                        header(&response, "etag"),
                        header(&response, "last-modified"),
                    );
                    if let Some(old) = &self.validator {
                        if (old.0.is_some() && old.0 != validator.0)
                            || (old.1.is_some() && old.1 != validator.1)
                        {
                            return err(Category::ResponseInvalid);
                        }
                    } else {
                        self.validator = Some(validator);
                    }
                    self.current = Some(response);
                }
            }
        }
    }
    async fn ticket(&self, config: &Configuration, shared: &Shared) -> Result<Vec<Block>> {
        let url = self.query.url(&config.service)?;
        for attempt in 1..=3 {
            let response = network::get(config, url.clone(), HeaderMap::new(), true).await;
            let response = match response {
                Ok(response) => response,
                Err(error) if error.category == Category::TransportFailed => {
                    retry_wait(shared, attempt, None, State::Ticketing).await?;
                    continue;
                }
                Err(error) => return Err(error),
            };
            if transient_status(&response) {
                let wait = server_wait(&response);
                // Release the unsuccessful response before waiting or retrying.
                drop(response);
                retry_wait(shared, attempt, wait, State::Ticketing).await?;
                continue;
            }
            match ticket_body(config, response).await {
                Ok(bytes) => return ticket::parse(&bytes),
                Err(error) if error.category == Category::TransportFailed => {
                    retry_wait(shared, attempt, None, State::Ticketing).await?;
                }
                Err(error) => return Err(error),
            }
        }
        err(Category::TransportFailed)
    }
    fn reset_block(&mut self) {
        self.exposed = false;
        self.block_received = 0;
        self.attempts = 0;
        self.validator = None;
        self.expected = None;
    }
    async fn retry(&self, shared: &Shared, server_wait: Option<Duration>) -> Result<()> {
        if self.exposed {
            return err(Category::TransportFailed);
        }
        retry_wait(shared, self.attempts, server_wait, State::Fetching).await
    }
}

async fn ticket_body(config: &Configuration, mut response: Response) -> Result<Vec<u8>> {
    status(&response)?;
    network::identity(&response)?;
    if response.status() != 200 {
        return err(Category::ResponseInvalid);
    }
    let expected = network::length(&response)?;
    if expected.is_some_and(|n| n > config.limits.ticket_bytes as u64) {
        return err(Category::ResourceLimit);
    }
    let mut data = Vec::new();
    loop {
        let chunk = tokio::time::timeout(config.limits.idle_timeout, response.chunk())
            .await
            .map_err(|_| Error::new(Category::DeadlineExceeded))?;
        match chunk {
            Ok(Some(chunk)) => {
                if data.len() + chunk.len() > config.limits.ticket_bytes {
                    return err(Category::ResourceLimit);
                }
                data.extend_from_slice(&chunk);
            }
            Ok(None) => break,
            // A declared-length violation is not an eligible transient.
            Err(_) if expected.is_some() => return err(Category::ResponseInvalid),
            Err(error) => return Err(network::classify(error)),
        }
    }
    if expected.is_some_and(|n| n != data.len() as u64) {
        return err(Category::ResponseInvalid);
    }
    Ok(data)
}

async fn retry_wait(
    shared: &Shared,
    attempts: usize,
    server_wait: Option<Duration>,
    target: State,
) -> Result<()> {
    if attempts >= 3 {
        return err(Category::TransportFailed);
    }
    shared.state(State::RetryWait);
    // The phase/overall timeout and outer select also bound and cancel this wait.
    let wait = server_wait.unwrap_or(Duration::from_secs(attempts.max(1) as u64));
    let until = tokio::time::Instant::now()
        .checked_add(wait)
        .ok_or(Error::new(Category::DeadlineExceeded))?;
    tokio::time::sleep_until(until).await;
    // Count an admitted new attempt, not an interrupted retry wait.
    let mut report = lock(&shared.report);
    if let Some(error) = &report.error {
        return Err(error.clone());
    }
    report.retries += 1;
    report.state = target;
    Ok(())
}

fn transient_status(response: &Response) -> bool {
    matches!(response.status().as_u16(), 429 | 500 | 502 | 503 | 504)
}
fn server_wait(response: &Response) -> Option<Duration> {
    response
        .headers()
        .get("retry-after")
        .and_then(|s| s.to_str().ok())
        .and_then(retry_after)
}
fn status(response: &Response) -> Result<()> {
    match response.status().as_u16() {
        401 | 403 => err(Category::AccessDenied),
        200 | 206 => Ok(()),
        _ => err(Category::ResponseInvalid),
    }
}
fn header(r: &Response, key: &str) -> Option<String> {
    r.headers()
        .get(key)
        .and_then(|v| v.to_str().ok())
        .map(str::to_owned)
}
fn retry_after(s: &str) -> Option<Duration> {
    s.parse::<u64>().ok().map(Duration::from_secs).or_else(|| {
        httpdate::parse_http_date(s)
            .ok()
            .map(|t| t.duration_since(SystemTime::now()).unwrap_or_default())
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::Destination;
    use std::sync::{Barrier, atomic::Ordering};

    fn local() -> (Client, Stream) {
        let mut config = Configuration::new(
            "https://synthetic.invalid/reads/",
            vec![
                Destination::new(
                    "https://synthetic.invalid",
                    vec!["127.0.0.1".parse().unwrap()],
                )
                .unwrap(),
            ],
        )
        .unwrap();
        config.limits.cleanup_timeout = Duration::from_millis(20);
        config.limits.max_queries = 1;
        let client = Client::new(config).unwrap();
        let stream = client.open(Query::new("s", "chr", 0, 1).unwrap()).unwrap();
        lock(&stream.inner.reader).blocks =
            Some(VecDeque::from([Block::Inline(Bytes::from_static(b"AB"))]));
        stream.inner.shared.state(State::Fetching);
        (client, stream)
    }

    #[test]
    fn cleanup_timeout_keeps_the_slot_and_can_be_retried() {
        let (client, stream) = local();
        let reader = lock(&stream.inner.reader);
        assert_eq!(
            stream.close().unwrap_err().category,
            Category::CleanupTimeout
        );
        let report = stream.result();
        assert_eq!(report.cleanup, Cleanup::InProgress);
        assert!(!report.cleanup_complete);
        assert_eq!(
            report.cleanup_error.unwrap().category,
            Category::CleanupTimeout
        );
        assert_eq!(
            client
                .open(Query::new("s", "chr", 0, 1).unwrap())
                .err()
                .unwrap()
                .category,
            Category::ResourceLimit
        );
        drop(reader);
        stream.close().unwrap();
        assert_eq!(stream.result().cleanup, Cleanup::Complete);
        assert!(stream.result().cleanup_error.is_none());
        assert_eq!(stream.result().state, State::Cancelled);
        let next = client.open(Query::new("s", "chr", 0, 1).unwrap()).unwrap();
        next.close().unwrap();
    }

    #[test]
    fn competing_close_obeys_its_own_cleanup_budget() {
        let (_client, stream) = local();
        let cleanup = lock(&stream.inner.cleanup);
        assert_eq!(
            stream.close().unwrap_err().category,
            Category::CleanupTimeout
        );
        assert_eq!(stream.result().cleanup, Cleanup::InProgress);
        drop(cleanup);
        stream.close().unwrap();
        assert_eq!(stream.result().cleanup, Cleanup::Complete);
    }

    #[test]
    fn reader_panic_becomes_sanitized_failure_and_remains_closable() {
        let (_client, stream) = local();
        stream.inner.hooks.panic_read.store(true, Ordering::SeqCst);
        assert_eq!(
            stream.read_chunk(8).unwrap_err().category,
            Category::InternalFailure
        );
        assert_eq!(stream.result().state, State::Failed);
        assert!(!stream.result().may_have_partial_output);
        assert_eq!(
            stream.read_chunk(8).unwrap_err().category,
            Category::InternalFailure
        );
        stream.close().unwrap();
        assert_eq!(stream.result().cleanup, Cleanup::Complete);
        assert_eq!(
            stream.result().error.unwrap().category,
            Category::InternalFailure
        );
    }

    #[test]
    fn partial_reads_account_for_the_entire_retained_storage_and_output_copy() {
        let (_client, stream) = local();
        assert_eq!(stream.read_chunk(1).unwrap(), b"A");
        let memory = stream.result().memory;
        assert_eq!(memory.current_payload_bytes, 2);
        assert_eq!(memory.peak_payload_bytes, 3);
        assert_eq!(memory.rust_output_copy_bytes, 1);
        assert_eq!(stream.read_chunk(1).unwrap(), b"B");
        // An empty slice still retains the original two-byte backing storage.
        assert_eq!(stream.result().memory.current_payload_bytes, 2);
        assert!(stream.read_chunk(1).unwrap().is_empty());
        assert_eq!(stream.result().memory.current_payload_bytes, 0);
        assert_eq!(stream.result().memory.rust_output_copy_bytes, 2);
        stream.close().unwrap();
    }

    #[test]
    fn watchdog_join_failure_is_separate_from_the_transport_outcome() {
        let (_client, stream) = local();
        let old = lock(&stream.inner.watchdog).take().unwrap();
        old.abort();
        stream.inner.owner.runtime.block_on(async {
            let _ = old.await;
        });
        let failed = stream
            .inner
            .owner
            .runtime
            .spawn(async { panic!("injected worker failure") });
        lock(&stream.inner.watchdog).replace(failed);
        assert_eq!(
            stream.close().unwrap_err().category,
            Category::InternalFailure
        );
        assert_eq!(stream.result().state, State::Cancelled);
        assert_eq!(stream.result().cleanup, Cleanup::Failed);
        assert_eq!(
            stream.result().cleanup_error.unwrap().category,
            Category::InternalFailure
        );
        stream.close().unwrap();
        assert_eq!(stream.result().cleanup, Cleanup::Complete);
    }

    fn gate() -> (Arc<Barrier>, Arc<Barrier>, Box<dyn FnOnce() + Send>) {
        let arrived = Arc::new(Barrier::new(2));
        let resume = Arc::new(Barrier::new(2));
        let (a, r) = (arrived.clone(), resume.clone());
        (
            arrived,
            resume,
            Box::new(move || {
                a.wait();
                r.wait();
            }),
        )
    }

    #[test]
    fn cancellation_before_handoff_prevents_new_exposure() {
        let (_client, stream) = local();
        let (arrived, resume, hook) = gate();
        lock(&stream.inner.hooks.before_handoff).replace(hook);
        let reader = stream.clone();
        let task = thread::spawn(move || reader.read_chunk(8));
        arrived.wait();
        stream.cancel();
        resume.wait();
        assert_eq!(
            task.join().unwrap().unwrap_err().category,
            Category::Cancelled
        );
        assert_eq!(stream.result().bytes_delivered, 0);
        assert!(!stream.result().may_have_partial_output);
        stream.close().unwrap();
    }

    #[test]
    fn a_committed_handoff_can_finish_after_cancellation_is_observed() {
        let (_client, stream) = local();
        let (arrived, resume, hook) = gate();
        lock(&stream.inner.hooks.after_handoff).replace(hook);
        let reader = stream.clone();
        let task = thread::spawn(move || reader.read_chunk(8));
        arrived.wait();
        stream.cancel();
        assert_eq!(stream.result().bytes_delivered, 2);
        assert!(stream.result().may_have_partial_output);
        resume.wait();
        assert_eq!(task.join().unwrap().unwrap(), b"AB");
        assert_eq!(
            stream.read_chunk(8).unwrap_err().category,
            Category::Cancelled
        );
        stream.close().unwrap();
    }
}
