use genewire_core::{Category, Client, Configuration, Destination, Query, State};
use serde_json::json;
use std::{
    io::{Read, Write},
    net::{TcpListener, TcpStream},
    sync::{
        Arc, Mutex,
        atomic::{AtomicBool, AtomicUsize, Ordering},
    },
    thread,
    time::{Duration, Instant},
};

struct Server {
    origin: String,
    stop: Arc<AtomicBool>,
    requests: Arc<Mutex<Vec<String>>>,
    task: Option<thread::JoinHandle<()>>,
}
impl Server {
    fn new(handler: impl Fn(&str, &str) -> Vec<u8> + Send + Sync + 'static) -> Self {
        let listener = TcpListener::bind("127.0.0.1:0").unwrap();
        listener.set_nonblocking(true).unwrap();
        let origin = format!("http://{}", listener.local_addr().unwrap());
        let stop = Arc::new(AtomicBool::new(false));
        let requests = Arc::new(Mutex::new(Vec::new()));
        let (flag, seen, base, handler) = (
            stop.clone(),
            requests.clone(),
            origin.clone(),
            Arc::new(handler),
        );
        let task = thread::spawn(move || {
            let mut workers = Vec::new();
            while !flag.load(Ordering::SeqCst) {
                match listener.accept() {
                    Ok((mut socket, _)) => {
                        let (handler, seen, base) = (handler.clone(), seen.clone(), base.clone());
                        workers.push(thread::spawn(move || {
                            // Normalize accepted sockets before using a blocking reader.
                            // A nonblocking listener must not make fixture reads race
                            // the client's request write on platforms that inherit flags.
                            socket.set_nonblocking(false).unwrap();
                            socket
                                .set_read_timeout(Some(Duration::from_secs(2)))
                                .unwrap();
                            let request = request(&mut socket);
                            if !request.ends_with("\r\n\r\n") {
                                return;
                            }
                            seen.lock().unwrap().push(request.clone());
                            let _ = socket.write_all(&handler(&request, &base));
                        }));
                    }
                    Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                        thread::sleep(Duration::from_millis(1))
                    }
                    Err(e) => panic!("{e}"),
                }
            }
            for w in workers {
                w.join().unwrap();
            }
        });
        Self {
            origin,
            stop,
            requests,
            task: Some(task),
        }
    }
    fn config(&self) -> Configuration {
        let mut c = Configuration::new(
            &format!("{}/reads/", self.origin),
            vec![Destination::new(&self.origin, vec!["127.0.0.1".parse().unwrap()]).unwrap()],
        )
        .unwrap();
        c.loopback_http_for_tests = true;
        c
    }
    fn wait_requests(&self, count: usize) {
        let end = Instant::now() + Duration::from_secs(3);
        while self.requests.lock().unwrap().len() < count {
            assert!(Instant::now() < end, "request did not arrive");
            thread::sleep(Duration::from_millis(1));
        }
    }
}
impl Drop for Server {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::SeqCst);
        let joined = self.task.take().unwrap().join();
        if !thread::panicking() {
            joined.unwrap();
        }
    }
}
fn request(s: &mut TcpStream) -> String {
    let mut b = Vec::new();
    let mut byte = [0];
    while b.len() < 16384 {
        if s.read(&mut byte).unwrap_or(0) == 0 {
            break;
        }
        b.push(byte[0]);
        if b.ends_with(b"\r\n\r\n") {
            break;
        }
    }
    String::from_utf8(b).unwrap()
}
fn response(status: &str, headers: &str, body: &[u8]) -> Vec<u8> {
    let mut b = format!(
        "HTTP/1.1 {status}\r\nConnection: close\r\nContent-Length: {}\r\n{headers}\r\n",
        body.len()
    )
    .into_bytes();
    b.extend_from_slice(body);
    b
}
fn ticket(urls: serde_json::Value) -> Vec<u8> {
    response(
        "200 OK",
        "Content-Type: application/json\r\n",
        json!({"htsget":{"format":"BAM","urls":urls}})
            .to_string()
            .as_bytes(),
    )
}
fn query() -> Query {
    Query::new("synthetic", "chrSynthetic", 99, 100).unwrap()
}
fn inline() -> Server {
    Server::new(|_, _| ticket(json!([{"url":"data:;base64,QUJDRA=="}])))
}

#[test]
fn ordered_inline_and_ranged_fragments_own_their_output() {
    let s = Server::new(|req, origin| {
        if req.starts_with("GET /reads/") {
            ticket(
                json!([{"url":"data:;base64,QUI="},{"url":format!("{origin}/block"),"headers":{"Range":"bytes=2-3"}}]),
            )
        } else {
            assert!(
                req.to_lowercase().contains("range: bytes=2-3"),
                "unexpected synthetic request: {req:?}"
            );
            response(
                "206 Partial Content",
                "Content-Range: bytes 2-3/4\r\n",
                b"CD",
            )
        }
    });
    let client = Client::new(s.config()).unwrap();
    let stream = client.open(query()).unwrap();
    let retained = stream.read_chunk(1).unwrap();
    let mut out = retained.clone();
    loop {
        let b = stream.read_chunk(1).unwrap();
        if b.is_empty() {
            break;
        }
        out.extend(b);
    }
    assert_eq!(out, b"ABCD");
    assert_eq!(retained, b"A");
    assert_eq!(stream.finish().unwrap().bytes_delivered, 4);
    stream.cancel();
    assert_eq!(stream.result().state, State::TransportComplete);
    stream.close().unwrap();
    assert!(stream.result().cleanup_complete);
}

#[test]
fn query_encoding_preserves_authority_and_half_open_coordinates() {
    let s = inline();
    let c = Client::new(s.config()).unwrap();
    let q = Query::new("../a/b%?ü", "chr&x", 0, 1).unwrap();
    let r = c.open(q).unwrap();
    r.read_chunk(1).unwrap();
    r.close().unwrap();
    let requests = s.requests.lock().unwrap();
    let path = requests[0].split_whitespace().nth(1).unwrap();
    assert!(path.starts_with("/reads/..%2Fa%2Fb%25%3F%C3%BC?"));
    assert!(path.contains("referenceName=chr%26x&start=0&end=1"));
    assert!(Query::new("..", "chr", 0, 1).is_err());
    assert!(Query::new("a", "chr", 1, 1).is_err());
    assert!(Query::new("a", "chr", 0, u32::MAX as u64 + 1).is_err());
}

#[test]
fn premature_finish_and_invalid_reads_do_not_erase_outcomes() {
    let s = inline();
    let c = Client::new(s.config()).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(r.finish().unwrap_err().category, Category::InvalidState);
    assert_eq!(
        r.read_chunk(0).unwrap_err().category,
        Category::InvalidQuery
    );
    assert_eq!(r.result().state, State::New);
    r.cancel();
    assert_eq!(r.read_chunk(1).unwrap_err().category, Category::Cancelled);
    r.close().unwrap();
}

#[test]
fn duplicate_keys_rejected_before_data_fetch() {
    let s = Server::new(|_, _| {
        response("200 OK","",br#"{"htsget":{"format":"BAM","format":"BAM","urls":[{"url":"https://secret.invalid/"}]}}"#)
    });
    let c = Client::new(s.config()).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(
        r.read_chunk(1).unwrap_err().category,
        Category::TicketInvalid
    );
    assert_eq!(s.requests.lock().unwrap().len(), 1);
    r.close().unwrap();
}

#[test]
fn whole_response_to_range_is_rejected() {
    let s = Server::new(|req, o| {
        if req.starts_with("GET /reads/") {
            ticket(json!([{"url":format!("{o}/block"),"headers":{"Range":"bytes=2-3"}}]))
        } else {
            response("200 OK", "", b"ABCD")
        }
    });
    let c = Client::new(s.config()).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(
        r.read_chunk(10).unwrap_err().category,
        Category::ResponseInvalid
    );
    assert_eq!(r.result().bytes_delivered, 0);
    r.close().unwrap();
}

#[test]
fn http_content_decoding_is_not_confused_with_bam_compression() {
    let s = Server::new(|req, o| {
        if req.starts_with("GET /reads/") {
            ticket(json!([{"url":format!("{o}/block")}]))
        } else {
            response("200 OK", "Content-Encoding: gzip\r\n", b"not-gzip")
        }
    });
    let c = Client::new(s.config()).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(
        r.read_chunk(10).unwrap_err().category,
        Category::ResponseInvalid
    );
    r.close().unwrap();
}

#[test]
fn retry_after_prior_inline_output_does_not_replay_prefix() {
    let count = Arc::new(AtomicUsize::new(0));
    let requests = count.clone();
    let s = Server::new(move |req, o| {
        if req.starts_with("GET /reads/") {
            ticket(json!([{"url":"data:;base64,QUI="},{"url":format!("{o}/block")}]))
        } else if requests.fetch_add(1, Ordering::SeqCst) == 0 {
            response("503 Unavailable", "Retry-After: 0\r\n", b"")
        } else {
            response("200 OK", "", b"CD")
        }
    });
    let c = Client::new(s.config()).unwrap();
    let r = c.open(query()).unwrap();
    let mut all = Vec::new();
    loop {
        let b = r.read_chunk(32).unwrap();
        if b.is_empty() {
            break;
        }
        all.extend(b);
    }
    assert_eq!(all, b"ABCD");
    assert_eq!(r.finish().unwrap().retries, 1);
    assert_eq!(count.load(Ordering::SeqCst), 2);
    r.close().unwrap();
}

#[test]
fn exposed_chunked_prefix_is_never_retried() {
    let s = Server::new(|req, o| {
        if req.starts_with("GET /reads/") {
            ticket(json!([{"url":format!("{o}/block")}]))
        } else {
            b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n2\r\nAB\r\n"
                .to_vec()
        }
    });
    let c = Client::new(s.config()).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(r.read_chunk(10).unwrap(), b"AB");
    assert_eq!(
        r.read_chunk(10).unwrap_err().category,
        Category::TransportFailed
    );
    assert_eq!(r.result().retries, 0);
    assert_eq!(s.requests.lock().unwrap().len(), 2);
    r.close().unwrap();
}

#[test]
fn truncated_known_length_fails_without_success() {
    let s = Server::new(|req, o| {
        if req.starts_with("GET /reads/") {
            ticket(json!([{"url":format!("{o}/block")}]))
        } else {
            b"HTTP/1.1 200 OK\r\nContent-Length: 4\r\nConnection: close\r\n\r\nAB".to_vec()
        }
    });
    let c = Client::new(s.config()).unwrap();
    let r = c.open(query()).unwrap();
    let error = loop {
        match r.read_chunk(32) {
            Ok(b) => assert!(!b.is_empty()),
            Err(e) => break e,
        }
    };
    assert_eq!(error.category, Category::ResponseInvalid);
    assert_eq!(r.result().state, State::Failed);
    r.close().unwrap();
}

#[test]
fn authentication_denial_is_sanitized_and_not_retried() {
    let s = Server::new(|_, _| response("403 Forbidden", "", b"signed-url-secret-token"));
    let c = Client::new(s.config()).unwrap();
    let r = c.open(query()).unwrap();
    let e = r.read_chunk(10).unwrap_err();
    assert_eq!(e.to_string(), "AccessDenied");
    assert_eq!(s.requests.lock().unwrap().len(), 1);
    r.close().unwrap();
}

#[test]
fn control_authorization_is_not_inherited_by_data_requests() {
    let s = Server::new(|req, o| {
        if req.starts_with("GET /reads/") {
            assert!(req.contains("Bearer synthetic-token"));
            ticket(json!([{"url":format!("{o}/block")}]))
        } else {
            assert!(!req.to_lowercase().contains("authorization:"));
            response("200 OK", "", b"AB")
        }
    });
    let mut config = s.config();
    config.control_token = Some("synthetic-token".into());
    let c = Client::new(config).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(r.read_chunk(8).unwrap(), b"AB");
    r.close().unwrap();
}

#[test]
fn destination_ip_must_match_the_operator_policy() {
    let s = inline();
    let mut config = s.config();
    config.destinations[0].addresses = vec!["127.0.0.2".parse().unwrap()];
    let c = Client::new(config).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(
        r.read_chunk(8).unwrap_err().category,
        Category::NetworkPolicy
    );
    assert!(s.requests.lock().unwrap().is_empty());
    r.close().unwrap();
}

#[test]
fn plaintext_http_is_disabled_without_explicit_test_mode() {
    let s = inline();
    let mut config = s.config();
    config.loopback_http_for_tests = false;
    let c = Client::new(config).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(
        r.read_chunk(8).unwrap_err().category,
        Category::NetworkPolicy
    );
    r.close().unwrap();
}

#[test]
fn unapproved_redirect_never_receives_the_control_token() {
    let other = inline();
    let target = format!("{}/leak", other.origin);
    let s = Server::new(move |_, _| response("302 Found", &format!("Location: {target}\r\n"), b""));
    let mut cfg = s.config();
    cfg.control_token = Some("synthetic".into());
    let c = Client::new(cfg).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(
        r.read_chunk(8).unwrap_err().category,
        Category::NetworkPolicy
    );
    assert!(other.requests.lock().unwrap().is_empty());
    r.close().unwrap();
}

#[test]
fn ticket_header_override_cannot_bypass_host_policy() {
    let s = Server::new(|_, o| {
        ticket(json!([{"url":format!("{o}/block"),"headers":{"hOsT":"secret.invalid"}}]))
    });
    let c = Client::new(s.config()).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(
        r.read_chunk(8).unwrap_err().category,
        Category::NetworkPolicy
    );
    assert_eq!(s.requests.lock().unwrap().len(), 1);
    r.close().unwrap();
}

#[test]
fn finite_result_limit_is_failure_not_truncated_success() {
    let s = inline();
    let mut config = s.config();
    config.limits.result_bytes = 3;
    let c = Client::new(config).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(
        r.read_chunk(8).unwrap_err().category,
        Category::ResourceLimit
    );
    assert_eq!(r.result().state, State::Failed);
    r.close().unwrap();
}

#[test]
fn deadline_expires_even_when_caller_does_not_read() {
    let s = inline();
    let mut cfg = s.config();
    cfg.limits.query_timeout = Duration::from_millis(20);
    let c = Client::new(cfg).unwrap();
    let r = c.open(query()).unwrap();
    let end = Instant::now() + Duration::from_secs(2);
    while r.result().error.is_none() {
        assert!(Instant::now() < end);
        thread::sleep(Duration::from_millis(1));
    }
    assert_eq!(
        r.read_chunk(8).unwrap_err().category,
        Category::DeadlineExceeded
    );
    r.close().unwrap();
    assert!(s.requests.lock().unwrap().is_empty());
}

#[test]
fn cancel_wakes_a_blocked_reader_and_close_joins_it() {
    let s = Server::new(|_, _| {
        thread::sleep(Duration::from_millis(200));
        ticket(json!([{"url":"data:;base64,QUI="}]))
    });
    let c = Client::new(s.config()).unwrap();
    let r = c.open(query()).unwrap();
    let worker = r.clone();
    let task = thread::spawn(move || worker.read_chunk(8));
    s.wait_requests(1);
    assert_eq!(
        r.read_chunk(8).unwrap_err().category,
        Category::InvalidState
    );
    r.cancel();
    r.close().unwrap();
    assert_eq!(
        task.join().unwrap().unwrap_err().category,
        Category::Cancelled
    );
    assert!(r.result().cleanup_complete);
}

#[test]
fn slots_are_held_until_explicit_cleanup_and_client_close_is_final() {
    let s = inline();
    let mut cfg = s.config();
    cfg.limits.max_queries = 1;
    let c = Client::new(cfg).unwrap();
    let r = c.open(query()).unwrap();
    r.cancel();
    assert!(matches!(c.open(query()),Err(e) if e.category==Category::ResourceLimit));
    r.close().unwrap();
    let next = c.open(query()).unwrap();
    c.close().unwrap();
    assert_eq!(next.result().state, State::Cancelled);
    assert!(matches!(c.open(query()),Err(e) if e.category==Category::InvalidState));
}

#[test]
fn malformed_ticket_variants_never_start_data_fetches() {
    let cases = vec![
        (
            json!({"htsget":{"format":"BAM","urls":[]}}),
            Category::TicketInvalid,
        ),
        (
            json!({"htsget":{"format":"CRAM","urls":[{"url":"data:;base64,QUI="}]}}),
            Category::TicketInvalid,
        ),
        (
            json!({"htsget":{"format":"BAM","urls":[{"url":"data:;base64,!!!!"}]}}),
            Category::TicketInvalid,
        ),
        (
            json!({"htsget":{"format":"BAM","urls":[{"url":"https://unapproved.invalid/","headers":{"Range":"bytes=1-"}}]}}),
            Category::Unsupported,
        ),
        (
            json!({"htsget":{"format":"BAM","urls":[{"url":"https://unapproved.invalid/","headers":{"Range":"bytes=-1"}}]}}),
            Category::Unsupported,
        ),
        (
            json!({"htsget":{"format":"BAM","urls":[{"url":"https://unapproved.invalid/","headers":{"Range":"bytes=0-1,3-4"}}]}}),
            Category::Unsupported,
        ),
        (
            json!({"htsget":{"format":"BAM","urls":[{"url":"https://unapproved.invalid/","headers":{"range":"bytes=0-1","Range":"bytes=2-3"}}]}}),
            Category::TicketInvalid,
        ),
        (
            json!({"htsget":{"format":"BAM","urls":vec![json!({"url":"data:;base64,QUI="});1025]}}),
            Category::ResourceLimit,
        ),
    ];
    for (value, expected) in cases {
        let body = value.to_string();
        let s = Server::new(move |_, _| response("200 OK", "", body.as_bytes()));
        let c = Client::new(s.config()).unwrap();
        let r = c.open(query()).unwrap();
        assert_eq!(r.read_chunk(32).unwrap_err().category, expected);
        assert_eq!(s.requests.lock().unwrap().len(), 1);
        r.close().unwrap();
    }
}

#[test]
fn ticket_size_and_depth_are_bounded() {
    let mut deep = json!(0);
    for _ in 0..20 {
        deep = json!([deep]);
    }
    let data = json!({"htsget":{"format":"BAM","urls":[{"url":"data:;base64,QUI="}]},"extra":deep})
        .to_string();
    let s = Server::new(move |_, _| response("200 OK", "", data.as_bytes()));
    let c = Client::new(s.config()).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(
        r.read_chunk(8).unwrap_err().category,
        Category::ResourceLimit
    );
    r.close().unwrap();
    let s = inline();
    let mut cfg = s.config();
    cfg.limits.ticket_bytes = 8;
    let c = Client::new(cfg).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(
        r.read_chunk(8).unwrap_err().category,
        Category::ResourceLimit
    );
    r.close().unwrap();
}

#[test]
fn a_stalled_body_obeys_the_idle_deadline() {
    let s = Server::new(|req, o| {
        if req.starts_with("GET /reads/") {
            ticket(json!([{"url":format!("{o}/block")}]))
        } else {
            thread::sleep(Duration::from_millis(300));
            response("200 OK", "", b"AB")
        }
    });
    let mut cfg = s.config();
    cfg.limits.idle_timeout = Duration::from_millis(100);
    let c = Client::new(cfg).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(
        r.read_chunk(8).unwrap_err().category,
        Category::DeadlineExceeded
    );
    assert_eq!(r.result().retries, 0);
    assert_eq!(s.requests.lock().unwrap().len(), 2);
    r.close().unwrap();
}

#[test]
fn declared_range_endpoints_and_lengths_must_match() {
    for cr in ["bytes 0-1/4", "bytes 2-3/3", "bytes 2-3/bad"] {
        let extra = format!("Content-Range: {cr}\r\n");
        let s = Server::new(move |req, o| {
            if req.starts_with("GET /reads/") {
                ticket(json!([{"url":format!("{o}/block"),"headers":{"Range":"bytes=2-3"}}]))
            } else {
                response("206 Partial Content", &extra, b"CD")
            }
        });
        let c = Client::new(s.config()).unwrap();
        let r = c.open(query()).unwrap();
        assert_eq!(
            r.read_chunk(8).unwrap_err().category,
            Category::ResponseInvalid
        );
        r.close().unwrap();
    }
}

#[test]
fn a_hostname_uses_only_its_explicit_ip_pins_without_ambient_dns() {
    let s = inline();
    let port = s.origin.rsplit(':').next().unwrap();
    let origin = format!("http://synthetic.invalid:{port}");
    let mut cfg = Configuration::new(
        &format!("{origin}/reads/"),
        vec![Destination::new(&origin, vec!["127.0.0.1".parse().unwrap()]).unwrap()],
    )
    .unwrap();
    cfg.loopback_http_for_tests = true;
    let c = Client::new(cfg).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(r.read_chunk(8).unwrap(), b"ABCD");
    r.close().unwrap();
    assert!(s.requests.lock().unwrap()[0].contains("synthetic.invalid"));
}

#[test]
fn control_credentials_do_not_cross_into_a_separate_allowed_data_origin() {
    let data = Server::new(|request, _| {
        assert!(!request.to_lowercase().contains("authorization:"));
        response("200 OK", "", b"AB")
    });
    let data_url = format!("{}/block", data.origin);
    let control = Server::new(move |request, _| {
        assert!(request.contains("Bearer synthetic-token"));
        ticket(json!([{"url":data_url}]))
    });
    let mut cfg = control.config();
    cfg.control_token = Some("synthetic-token".into());
    cfg.destinations
        .push(Destination::new(&data.origin, vec!["127.0.0.1".parse().unwrap()]).unwrap());
    let c = Client::new(cfg).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(r.read_chunk(8).unwrap(), b"AB");
    r.close().unwrap();
    assert_eq!(data.requests.lock().unwrap().len(), 1);
}

#[test]
fn changed_validator_on_an_unexposed_retry_is_rejected() {
    let count = Arc::new(AtomicUsize::new(0));
    let seen = count.clone();
    let s = Server::new(move |req, o| {
        if req.starts_with("GET /reads/") {
            ticket(json!([{"url":format!("{o}/block")}]))
        } else if seen.fetch_add(1, Ordering::SeqCst) == 0 {
            b"HTTP/1.1 200 OK\r\nETag: old\r\nTransfer-Encoding: chunked\r\nConnection: close\r\n\r\n".to_vec()
        } else {
            response("200 OK", "ETag: new\r\n", b"AB")
        }
    });
    let c = Client::new(s.config()).unwrap();
    let r = c.open(query()).unwrap();
    let outcome = r.read_chunk(8);
    assert_eq!(
        outcome.as_ref().err().map(|e| e.category),
        Some(Category::ResponseInvalid),
        "outcome={outcome:?}; blocks={}; requests={:?}",
        count.load(Ordering::SeqCst),
        s.requests.lock().unwrap()
    );
    assert_eq!(r.result().bytes_delivered, 0);
    assert_eq!(count.load(Ordering::SeqCst), 2);
    r.close().unwrap();
}

#[test]
fn caller_backpressure_does_not_consume_the_idle_read_budget() {
    let s = Server::new(|req, o| {
        if req.starts_with("GET /reads/") {
            ticket(json!([{"url":format!("{o}/block")}]))
        } else {
            response("200 OK", "", b"ABCD")
        }
    });
    let mut cfg = s.config();
    cfg.limits.idle_timeout = Duration::from_millis(50);
    let c = Client::new(cfg).unwrap();
    let r = c.open(query()).unwrap();
    assert_eq!(r.read_chunk(1).unwrap(), b"A");
    thread::sleep(Duration::from_millis(100));
    let mut out = vec![b'A'];
    loop {
        let bytes = r.read_chunk(1).unwrap();
        if bytes.is_empty() {
            break;
        }
        out.extend(bytes);
    }
    assert_eq!(out, b"ABCD");
    assert_eq!(r.finish().unwrap().state, State::TransportComplete);
    r.close().unwrap();
}

#[test]
fn rejecting_nested_runtime_close_does_not_cancel_queries() {
    let cfg = Configuration::new(
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
    let client = Client::new(cfg).unwrap();
    let stream = client.open(query()).unwrap();
    let caller_runtime = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .unwrap();
    let error = caller_runtime
        .block_on(async { client.close() })
        .unwrap_err();
    assert_eq!(error.category, Category::InvalidState);
    assert_eq!(stream.result().state, State::New);
    client.close().unwrap();
    assert!(stream.result().cleanup_complete);
}
