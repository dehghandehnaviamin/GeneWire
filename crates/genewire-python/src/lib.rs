use genewire_core as core;
use pyo3::{create_exception, exceptions::PyRuntimeError, prelude::*, types::PyBytes};
use std::time::Duration;

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
    #[pyo3(signature = (service, destinations, token, loopback_http, timeout_ms, result_bytes))]
    fn new(
        py: Python<'_>,
        service: String,
        destinations: Vec<(String, Vec<String>, bool)>,
        token: Option<String>,
        loopback_http: bool,
        timeout_ms: u64,
        result_bytes: u64,
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
            c.limits.query_timeout = Duration::from_millis(timeout_ms);
            c.limits.result_bytes = result_bytes;
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
                .map(|inner| NativeStream { inner })
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
}
type Snapshot = (String, u64, usize, bool, Option<String>);
fn snapshot(r: core::Report) -> Snapshot {
    (
        format!("{:?}", r.state),
        r.bytes_delivered,
        r.retries,
        r.cleanup_complete,
        r.error.map(|e| format!("{:?}", e.category)),
    )
}
#[pymethods]
impl NativeStream {
    fn read_chunk<'py>(&self, py: Python<'py>, max_bytes: usize) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = py
            .detach(|| self.inner.read_chunk(max_bytes))
            .map_err(error)?;
        Ok(PyBytes::new(py, &bytes))
    }
    fn result(&self) -> Snapshot {
        snapshot(self.inner.result())
    }
    fn finish(&self) -> PyResult<Snapshot> {
        self.inner.finish().map(snapshot).map_err(error)
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
