# Local development

GeneWire now has an experimental Rust core and synchronous Python binding.
This is a local evaluation build, not a released package or production service.
Read the [implementation evidence and gaps](project/M2-LOCAL.md).

## Verified environment and setup

The initial checks used macOS 27.0 on arm64, Rust/Cargo 1.93.0, CPython 3.14.6,
uv 0.13.10 and maturin 1.16.0. Other operating systems/interpreters have not been
qualified. The abi3 wheel tag and Python metadata are not a tested support matrix.
Rust and uv must already be installed. From the repository root:

```bash
uv sync --locked --group test --python 3.14 --reinstall-package genewire
cargo test --workspace --locked
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo fmt --all -- --check
.venv/bin/python -m unittest discover -s tests -v
```

The first command creates/updates the local environment and builds the native
extension. Reinstalling the package ensures Rust source changes are rebuilt.
An alternative development rebuild, after that environment exists, is:

```bash
VIRTUAL_ENV="$PWD/.venv" .venv/bin/maturin develop --locked
```

The Python test group pins pysam 0.24.1, whose installed HTSlib/samtools reports
1.24. It is an evaluation decoder, not a production dependency of GeneWire.
The TLS rejection test also needs an OpenSSL CLI; it reports a skip if absent.
No test was skipped on the initial runner. Tests bind ephemeral loopback ports
and create synthetic BAM/certificate material only in temporary directories.
They require permission to open local sockets; they do not contact a genomic
service or send data outside the machine.

## Current public Python operations

Import Client, Destination, Stream, Report and GeneWireError from genewire.
Client takes a reads-service URL ending in a slash and a mapping from allowed
origin to Destination(addresses, allow_ticket_authorization=False). The IPs are
explicit connection pins; the core does not discover them through ambient DNS.
The hostname remains in the URL for HTTP authority and TLS validation.

Client.open(object_id, reference, start, end) accepts one BAM region with explicit
zero-based half-open coordinates. It returns a lazy Stream; network I/O starts
on the first read. Boolean/float/overflow/empty coordinates fail locally.
Only this supported query shape is exposed; there is no whole-file fallback.

Stream.read_chunk(max_bytes=262144) returns owned immutable bytes. Empty bytes
mean completed transport EOF. iter_chunks, result, finish, cancel and close are
available. finish requires exhaustion. Use client/stream context managers or
explicit close; cleanup status remains inspectable. A stream retains the runtime
if the client object is collected. Dropping a live stream is best-effort cleanup.

Reads block the calling Python thread while allowing other Python threads to
run. One reader per stream is supported; concurrent reads fail InvalidState.
There is no asyncio adapter, decoded-record iterator, file exporter or official
analysis-process supervisor. Do not reuse native clients after fork or during
interpreter shutdown. Blocking Rust entry points reject invocation from inside
an active Tokio runtime.

HTTPS requires valid certificates and TLS 1.2 or later. Plain HTTP is disabled
unless loopback_http_for_tests=True and every pinned target is loopback. Control
tokens are scoped to the configured service; data credentials require separate
explicit policy. Errors contain local categories, not URLs, IDs or remote bodies.

All bytes are provisional until transport finishes. The result is an upstream
regional response that may overreturn records. Decoding/filtering and invalidating
partial downstream effects remain the caller's responsibility. Report states
are CamelCase spellings of the draft states; source_consistency is Unverified
and integrity is TransportOnly. These are unstable pre-alpha interfaces.

## Source layout

- crates/genewire-core: query validation, strict tickets, pinned HTTP, ordered
  reads, retry admission, cancellation, deadlines and explicit close.
- crates/genewire-python: PyO3 bridge; blocking Rust work detaches from Python.
- python/genewire: typed Python convenience interface and context management.
- crates/genewire-core/tests and tests: loopback behavior/fault and native/BAM tests.
- Cargo.lock and uv.lock: dependency resolution for this development build.

Generated native libraries, virtual environments, build output, certificates and
genomic files must stay untracked. No CI workflow or published artifact exists.
