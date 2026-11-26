# Technology direction: Rust core, Python integration

**Date:** 2026-11-26

**Owner decision:** Use a low-level, performance-oriented core with Rust as the
chosen direction; Python can provide convenient high-level access and integration.

This replaces the bootstrap's proposed Python/asyncio reference core. It does not
select a new wire protocol or prove a speed advantage. Implementation, dependency
versions, bindings and packaging remain future work.

## Proposed responsibility split

| Layer | Intended role | Boundary to evaluate |
| --- | --- | --- |
| Rust core | Network/data-path work, bounded buffers, streaming state, cancellation, recovery and integrity bookkeeping | Independently usable without embedding Python; exact APIs and runtime remain M1 choices |
| Genomic reader integration | Reuse reviewed format libraries through an evaluated Rust/native boundary | Correct decoding and index/reference semantics; no new parser merely to satisfy a language preference |
| Python high-level layer | Analysis/workflow API, orchestration and convenient access to the Rust core | Keep payload processing out of per-record Python callbacks when avoidable; preserve bounded consumption and error semantics |
| Packaging and CLI | Deliver usable artifacts for the approved deployment targets | Decide whether the CLI is Rust-native, Python-facing or both after user workflows are concrete |

The high-level Python API is planned, not an existing SDK. Rust is the language
direction, not a commitment to a particular async runtime, HTS library or binding.

## Connection options to evaluate

| Option | Why consider it? | Costs and questions |
| --- | --- | --- |
| PyO3 native extension, potentially packaged with maturin | Direct in-process Python/Rust integration | Interpreter attachment, ownership, cross-boundary copies, panic/error translation, cancellation and platform wheels |
| Rust process with a pipe-oriented Python wrapper | Explicit process lifetime and isolation; usable by other tools | Startup/IPC overhead, framing and backpressure across pipes, child cleanup and terminal status |
| Separate local/remote service | Could share work across consumers | Deployment, authorization and operational complexity; defer unless a concrete use case needs it |

PyO3 officially supports native Python modules written in Rust; its parallelism
guide explains detaching Rust work from the interpreter. Maturin supports Rust
extensions and mixed Python/Rust packaging. These facts establish integration
options, not that GeneWire has working bindings or that Python overhead vanishes.
[PyO3](https://docs.rs/pyo3/0.30.1/pyo3/),
[parallelism guide](https://pyo3.rs/main/parallelism.html),
[maturin](https://www.maturin.rs/).

Tokio is an async I/O/runtime candidate. Its documentation separates asynchronous
tasks from blocking work; an async API alone does not make decoding, compression
or hashing nonblocking. Runtime ownership and bounded blocking work must be
evaluated before combining Rust execution with a Python event loop.
[Tokio 1.54.1](https://docs.rs/tokio/1.54.1/tokio/).

## M1 questions and later evaluation

1. Which interface does the first analysis consumer need: byte stream, decoded
   records, bounded batches or a file-like handle? Ownership and allowed buffering
   must be explicit.
2. Can cancellation, late errors and incomplete results cross the boundary without
   misleading Python consumers? What happens if the consumer exits early?
3. How many copies, allocations and language crossings occur per block or batch?
   Do not promise zero-copy before verifying lifetimes and measurements.
4. Which interpreter builds and platforms are actually supported? Conventional
   and free-threaded Python configurations must not be conflated.
5. Which unsafe/native dependencies remain in the genomic path? Rust at the
   outer layer does not establish safety or scientific correctness of that path.
6. Are bottlenecks network, remote query generation, decoding, allocation, disk
   or language-boundary overhead? Profile the end-to-end workload before tuning.

Add two future candidate measurements to the regional evaluation: the Rust core
alone and the same core through the Python integration with identical settings.
Separate binding overhead from the existing-tool comparison. Keep content,
failure behavior and resource limits equal. Both measurements are currently
unrun; no language-based performance multiplier is claimed.
