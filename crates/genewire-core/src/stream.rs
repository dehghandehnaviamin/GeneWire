use crate::{
    Category, Configuration, Error, MAX_CHUNK, Query, Result,
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
}
fn lock<T>(m: &Mutex<T>) -> MutexGuard<'_, T> {
    m.lock().unwrap_or_else(|e| e.into_inner())
}
struct Shared {
    report: Mutex<Report>,
    cancel: CancellationToken,
}
impl Shared {
    fn fail(&self, error: Error) {
        let mut r = lock(&self.report);
        if !r.state.terminal() {
            r.state = if error.category == Category::Cancelled {
                State::Cancelled
            } else {
                State::Failed
            };
            r.error = Some(error);
        }
        self.cancel.cancel();
    }
    fn state(&self, state: State) {
        let mut r = lock(&self.report);
        if !r.state.terminal() {
            r.state = state;
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
                accepted: 0,
                exposed: false,
                block_received: 0,
                attempts: 0,
                validator: None,
                expected: None,
            }),
            watchdog: Mutex::new(Some(watchdog)),
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
        let output = catch_unwind(AssertUnwindSafe(|| self.inner.owner.runtime.block_on(async {
            tokio::select! { biased;
                _ = shared.cancel.cancelled() => Err(lock(&shared.report).error.clone().unwrap_or(Error::new(Category::Cancelled))),
                result = reader.read(&self.inner.owner.config, shared, max_bytes) => result,
            }
        }))).unwrap_or_else(|_| err(Category::InternalFailure));
        match output {
            Ok(data) => {
                let mut r = lock(&shared.report);
                // This lock is the public handoff's linearization point.
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
                Ok(data)
            }
            Err(error) => {
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
        loop {
            if let Ok(mut reader) = self.inner.reader.try_lock() {
                reader.current = None;
                reader.pending = Bytes::new();
                reader.blocks = None;
                break;
            }
            if Instant::now() >= deadline {
                return err(Category::CleanupTimeout);
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
                    return err(Category::InternalFailure);
                }
                Err(_) => return err(Category::CleanupTimeout),
            }
            task.take();
        }
        lock(&self.inner.shared.report).cleanup_complete = true;
        Ok(())
    }
}

struct Reader {
    query: Query,
    blocks: Option<VecDeque<Block>>,
    current: Option<Response>,
    pending: Bytes,
    accepted: u64,
    exposed: bool,
    block_received: u64,
    attempts: usize,
    validator: Option<(Option<String>, Option<String>)>,
    expected: Option<u64>,
}
impl Reader {
    async fn read(
        &mut self,
        config: &Configuration,
        shared: &Shared,
        max: usize,
    ) -> Result<Vec<u8>> {
        if self.blocks.is_none() {
            shared.state(State::Ticketing);
            let url = self.query.url(&config.service)?;
            let bytes = tokio::time::timeout(config.limits.ticket_timeout, async {
                let mut response = network::get(config, url, HeaderMap::new(), true).await?;
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
                while let Some(chunk) =
                    tokio::time::timeout(config.limits.idle_timeout, response.chunk())
                        .await
                        .map_err(|_| Error::new(Category::DeadlineExceeded))?
                        .map_err(network::classify)?
                {
                    if data.len() + chunk.len() > config.limits.ticket_bytes {
                        return err(Category::ResourceLimit);
                    }
                    data.extend_from_slice(&chunk);
                }
                if expected.is_some_and(|n| n != data.len() as u64) {
                    return err(Category::ResponseInvalid);
                }
                Ok(data)
            })
            .await
            .map_err(|_| Error::new(Category::DeadlineExceeded))??;
            self.blocks = Some(ticket::parse(&bytes)?.into());
            shared.state(State::Fetching);
        }
        loop {
            if !self.pending.is_empty() {
                return Ok(self.pending.split_to(max.min(self.pending.len())).to_vec());
            }
            if let Some(response) = self.current.as_mut() {
                // Start the idle clock for this active poll, excluding caller pauses.
                let chunk = tokio::time::timeout(config.limits.idle_timeout, response.chunk())
                    .await
                    .map_err(|_| Error::new(Category::DeadlineExceeded))?;
                match chunk {
                    Ok(Some(bytes)) => {
                        // An unusually large HTTP frame is rejected rather than exceeding
                        // our initial native payload policy. HTTP/2 is disabled.
                        if bytes.len() > MAX_CHUNK {
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
                        self.pending = bytes;
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
                    self.blocks.as_mut().expect("validated blocks").pop_front();
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
                    if matches!(response.status().as_u16(), 429 | 500 | 502 | 503 | 504) {
                        let wait = response
                            .headers()
                            .get("retry-after")
                            .and_then(|s| s.to_str().ok())
                            .and_then(retry_after);
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
    fn reset_block(&mut self) {
        self.exposed = false;
        self.block_received = 0;
        self.attempts = 0;
        self.validator = None;
        self.expected = None;
    }
    async fn retry(&self, shared: &Shared, server_wait: Option<Duration>) -> Result<()> {
        if self.attempts >= 3 || self.exposed {
            return err(Category::TransportFailed);
        }
        shared.state(State::RetryWait);
        lock(&shared.report).retries += 1;
        tokio::time::sleep(server_wait.unwrap_or(Duration::from_secs(self.attempts.max(1) as u64)))
            .await;
        shared.state(State::Fetching);
        Ok(())
    }
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
