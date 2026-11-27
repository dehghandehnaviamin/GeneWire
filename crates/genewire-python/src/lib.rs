use genewire_core as core;
use pyo3::{create_exception, exceptions::PyRuntimeError, prelude::*, types::PyBytes};
use std::{
    sync::atomic::{AtomicU64, Ordering},
    time::Duration,
};

create_exception!(_native, GeneWireError, PyRuntimeError);
fn error(e: core::Error) -> PyErr {
    GeneWireError::new_err(format!("{:?}", e.category))
}

#[pyclass(frozen, module = "genewire._native")]
struct NativeClient {
    inner: core::Client,
}
#[pymethods]
impl NativeClient {
    #[new]
    #[pyo3(signature = (service, destinations, token, loopback_http, limits, additional_ca_pem))]
    fn new(
        py: Python<'_>,
        service: String,
        destinations: Vec<(String, Vec<String>, bool)>,
        token: Option<String>,
        loopback_http: bool,
        limits: (u64, u64),
        additional_ca_pem: Option<Vec<u8>>,
    ) -> PyResult<Self> {
        py.detach(move || {
            let destinations = destinations
                .into_iter()
                .map(|(origin, ips, auth)| {
                    let mut d = core::Destination::new(
                        &origin,
                        ips.iter()
                            .map(|s| core::ip(s))
                            .collect::<core::Result<_>>()?,
                    )?;
                    d.allow_ticket_authorization = auth;
                    Ok(d)
                })
                .collect::<core::Result<Vec<_>>>()?;
            let mut c = core::Configuration::new(&service, destinations)?;
            c.control_token = token;
            c.loopback_http_for_tests = loopback_http;
            c.limits.query_timeout = Duration::from_millis(limits.0);
            c.limits.result_bytes = limits.1;
            c.additional_ca_pem = additional_ca_pem;
            core::Client::new(c).map(|inner| Self { inner })
        })
        .map_err(error)
    }
    fn open(
        &self,
        py: Python<'_>,
        object: String,
        reference: String,
        start: u64,
        end: u64,
    ) -> PyResult<NativeStream> {
        py.detach(|| {
            self.inner
                .open(core::Query::new(&object, &reference, start, end)?)
                .map(|inner| NativeStream {
                    inner,
                    python_copy_bytes: AtomicU64::new(0),
                })
        })
        .map_err(error)
    }
    fn close(&self, py: Python<'_>) -> PyResult<()> {
        py.detach(|| self.inner.close()).map_err(error)
    }
}

#[pyclass(frozen, module = "genewire._native")]
struct NativeStream {
    inner: core::Stream,
    python_copy_bytes: AtomicU64,
}
type MemorySnapshot = (u64, u64, u64, u64, u64);
type Snapshot = (
    String,
    u64,
    usize,
    bool,
    Option<String>,
    String,
    bool,
    String,
    Option<String>,
    String,
    String,
    MemorySnapshot,
);
fn snapshot(r: core::Report, python_copy_bytes: u64) -> Snapshot {
    (
        format!("{:?}", r.state),
        r.bytes_delivered,
        r.retries,
        r.cleanup_complete,
        r.error.map(|e| format!("{:?}", e.category)),
        format!("{:?}", r.phase),
        r.may_have_partial_output,
        format!("{:?}", r.cleanup),
        r.cleanup_error.map(|e| format!("{:?}", e.category)),
        format!("{:?}", r.upstream_profile),
        format!("{:?}", r.capability_evidence),
        (
            r.memory.current_payload_bytes,
            r.memory.peak_payload_bytes,
            r.memory.largest_http_fragment_bytes,
            r.memory.rust_output_copy_bytes,
            python_copy_bytes,
        ),
    )
}
#[pymethods]
impl NativeStream {
    fn read_chunk<'py>(&self, py: Python<'py>, max_bytes: usize) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = py
            .detach(|| self.inner.read_chunk(max_bytes))
            .map_err(error)?;
        let output = PyBytes::new(py, &bytes);
        self.python_copy_bytes
            .fetch_add(bytes.len() as u64, Ordering::Relaxed);
        Ok(output)
    }
    fn result(&self) -> Snapshot {
        snapshot(
            self.inner.result(),
            self.python_copy_bytes.load(Ordering::Relaxed),
        )
    }
    fn finish(&self) -> PyResult<Snapshot> {
        self.inner
            .finish()
            .map(|r| snapshot(r, self.python_copy_bytes.load(Ordering::Relaxed)))
            .map_err(error)
    }
    fn cancel(&self) {
        self.inner.cancel();
    }
    fn close(&self, py: Python<'_>) -> PyResult<()> {
        py.detach(|| self.inner.close()).map_err(error)
    }
}

#[pymodule(gil_used = true)]
fn _native(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<NativeClient>()?;
    m.add_class::<NativeStream>()?;
    m.add("GeneWireError", m.py().get_type::<GeneWireError>())?;
    Ok(())
}
