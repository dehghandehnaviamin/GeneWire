# Rust core and Python boundary

**GW-M1-DRAFT-01 — Design architecture and API sketches.**
The working partial interface is documented in [local development](../development.md);
these responsibility sketches are not a complete implemented API contract.
The owner chose Rust for the core and Python for convenient high-level integration.

## Logical components

| Component | Proposed responsibility |
| --- | --- |
| Query/policy model | Validate the supported interval, capabilities, finite limits and trusted configuration |
| htsget adapter | Construct the existing request; validate bounded tickets and ordered fragments |
| Network policy/HTTP adapter | Destination checks, credential separation, explicit redirects, deadlines and representation checks |
| Stream engine | Own bounded payload, exposure accounting, retry eligibility, cancellation and terminal state |
| Runtime owner | Own worker tasks, joins, query slots and client shutdown |
| Python bridge | Convert typed inputs/errors; expose owned byte chunks and explicit result/cleanup status |
| Consumer supervisor | Feed a mature decoder/filter and combine transport/process outcomes |

These are responsibilities, not selected crate names or an existing package tree.
The core has no dependency on Python objects or callbacks. Python integration
would be a separate optional build surface over the same Rust semantics.

## Proposed choices

Prefer Tokio for the native execution runtime, a reviewed HTTPS client such as
reqwest, and PyO3/maturin for the first Python binding/package workflow. These are
design preferences; dependency pins, Rust MSRV, interpreter versions, supported
platforms and feature audits must be established during M2 setup.

Prefer a synchronous Python chunk reader initially. An asyncio bridge, async
iterator, service daemon and native decoded-record API are deferred. Callers
needing async integration must not run blocking reads on their event-loop thread;
an official adapter requires a later cancellation/lifetime design.

The process-wrapper alternative remains available if native packaging makes the
first consumer impractical. Changing that choice must preserve the lifecycle
contract and be recorded, not create a second inconsistent core.

## API responsibility sketches

The following names are proposals for discussion, not importable modules or
compilable Rust/Python signatures:

| Concept / operation | Proposed behavior |
| --- | --- |
| Client(configuration) | Own one runtime and admission policy; configure trusted services and credential scopes |
| Query(object, reference, start, end, BAM) | Validated single-region input; no implicit coordinate translation |
| Client.open(query) | Create one independent query attempt and a stream handle |
| Stream.read_chunk(max_bytes) | Positive finite size ≤ 256 KiB; return nonempty owned bytes, terminal EOF, or a typed error |
| Stream.iter_chunks() | Convenience over bounded reads; stop only on transport EOF; failures raise |
| Stream.result() | Inspect current/terminal transport outcome and separate cleanup status |
| Stream.finish() | Obtain the final report only after exhaustion; do not silently discard unconsumed bytes |
| Stream.cancel() | Signal cancellation; do not claim synchronous cleanup |
| Stream.close() | Cancel if incomplete, join under budget and report cleanup outcome |
| Client.close() | Prevent new queries and close owned streams/runtime under the same explicit policy |

Use an explicit terminal EOF result in Rust and empty bytes only for completed
EOF in the proposed Python convenience reader. Never return an empty chunk for
"not ready", cancellation or a data error. Reject unbounded/read-all operations.
Calling finish before exhaustion is a local InvalidState error and does not
magically complete or discard the query. Invalid operations on a terminal handle
cannot overwrite its recorded outcome.

A context manager is proposed for deterministic cleanup. Closing a partially read
stream is cancellation, even if the network worker has already buffered the rest.
Repeated close is safe, and result remains inspectable afterward. A failed close
must preserve an exception already raised by the body while still making its
cleanup status accessible.

## Ownership and copying

Rust owns mutable network and queue buffers. The initial bridge would return
immutable Python-owned bytes with an explicit copy as needed, not a borrowed view
into a reusable native buffer. Drop/reuse of Rust storage must never invalidate
returned Python output. No zero-copy performance claim is made.

Reserve the entire native payload window across in-flight, queued and pending
handoff storage. Stop producing when credit is exhausted. The bridge's temporary
copy and user-retained Python chunks are additional memory; instrument both.
Keeping arbitrarily many returned objects is caller-owned memory, not evidence
that the core queue's bound failed.

Permit only one active reader per stream. Concurrent reads fail InvalidState;
cancel/status/close are coordinated separately. A handoff committed before a
concurrent failure may complete and is recorded as partial exposure. No new
handoff commits after terminal failure.

## Interpreter and runtime lifetime

Copy/validate Python inputs while attached, execute blocking waits/Rust-only work
without holding interpreter attachment, then reacquire only to create Python
outputs/errors. Workers must not invoke arbitrary Python callbacks or hold
Python-borrowed references. PyO3's detachment API has explicit boundary constraints.
[PyO3 Python token](https://docs.rs/pyo3/0.30.1/pyo3/marker/struct.Python.html).

A client owns its runtime; active query handles retain that owner. Do not destroy
the runtime while a query is still joined, producing or releasing buffers. Do
not hold Python attachment or a global bridge lock while waiting for a task that
needs Python progress. Panics/worker failures become sanitized InternalFailure,
never success and never uncontrolled unwinding across a foreign ABI.

Started blocking work cannot be treated as terminated merely because an async
task was aborted. Avoid blocking parsing in network workers; keep the first
decoder in the supervised consumer boundary and define its termination policy.
[Tokio cancellation](https://docs.rs/tokio/1.54.1/tokio/task/#cancellation).

Initial support targets conventional CPython on controlled Linux/macOS evaluation
runners; this is a proposed target, not verified support. Free-threaded Python,
subinterpreters, inherited clients after fork, pickling live handles and use
during interpreter shutdown are outside the first subset. Create clients in
their owning process. A consumer subprocess must use a reviewed spawn path;
do not execute an inherited native runtime inside a forked child.

## Packaging and measured evidence

Maturin began as the design candidate; the local M2 workflow now uses version
1.16.0. See the development guide for commands exercised on the current runner.
M1 did not create a package or Cargo workspace. The subsequent local M2 increment
now contains both; wheel/support qualification remains incomplete. [Packaging option](https://www.maturin.rs/).

Future M2 evidence must cover native ownership, interpreter shutdown, explicit
close, consumer failure, simultaneous cancel/read and error translation. Compare
core-only and Python-integrated latency, RSS, copies and language crossings under
the same result and resource policy. No Rust-versus-Python speedup is inferred
from this component diagram.
