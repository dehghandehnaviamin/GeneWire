# Local development

GeneWire now has an experimental Rust core and synchronous Python binding.
This is a local evaluation build, not a released package or production service.
Read the [implementation evidence and gaps](project/M2-LOCAL.md).

## Verified environment and setup

The initial checks used macOS 27.0 on arm64, Rust/Cargo 1.93.0, CPython 3.14.6,
uv 0.13.10 and maturin 1.16.0. [Actual CI](project/CI-VALIDATION.md) also passed on
Ubuntu 26.04.1 x86_64 and macOS 26.7.2 arm64 with CPython 3.14.10. This records
those runners; the abi3 wheel tag/Python metadata do not establish broader support.
Rust and uv must already be installed. From the repository root:

```bash
uv sync --locked --group test --extra analysis --python 3.14 --reinstall-package genewire
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
1.24. It is also the optional `analysis` extra; the byte reader alone does not
require it. TLS fixture tests need an OpenSSL CLI and report a skip if absent.
No test was skipped on the recorded runner. Tests bind ephemeral loopback ports
and create synthetic BAM/certificate material only in temporary directories.
They require permission to open local sockets; they do not contact a genomic
service or send data outside the machine.

## Current public Python operations

Import Client, Destination, Stream, Report and GeneWireError from genewire.
Client takes a reads-service URL ending in a slash and a mapping from allowed
origin to Destination(addresses, allow_ticket_authorization=False). The IPs are
explicit connection pins; the core does not discover them through ambient DNS.
The hostname remains in the URL for HTTP authority and TLS validation.
The explicit default upstream_profile is HtsgetBamRegional; other profiles fail
Unsupported. Reports label its capability_evidence Configured. The core does not
fetch service-info or infer server support/version from successful requests.

Client.open(object_id, reference, start, end) accepts one BAM region with explicit
zero-based half-open coordinates. It returns a lazy Stream; network I/O starts
on the first read. Boolean/float/overflow/empty coordinates fail locally.
Only this supported query shape is exposed; there is no whole-file fallback.

Stream.read_chunk(max_bytes=262144) returns owned immutable bytes. Empty bytes
mean completed transport EOF. iter_chunks, result, finish, cancel and close are
available. finish requires exhaustion. Use client/stream context managers or
explicit close; cleanup status remains inspectable. A stream retains the runtime
if the client object is collected. Dropping a live stream is best-effort cleanup.

Ticket GETs and each data block have independent limits of three attempts for
eligible transient failures. Ticket requests and retry waits share one ticket
phase deadline; the overall deadline and cancellation interrupt waits as well.
Malformed tickets, authorization/policy failures and declared-length violations
do not retry. A retry never refreshes a ticket after data has been exposed.

Reads block the calling Python thread while allowing other Python threads to
run. One reader per stream is supported; concurrent reads fail InvalidState.
There is no asyncio adapter or decoded-record iterator. The optional supervised
BAM file adapter is described below. Do not reuse native clients after fork or during
interpreter shutdown. Blocking Rust entry points reject invocation from inside
an active Tokio runtime.

HTTPS requires valid certificates and TLS 1.2 or later. Plain HTTP is disabled
unless loopback_http_for_tests=True and every pinned target is loopback. Control
tokens are scoped to the configured service; data credentials require separate
explicit policy. Errors contain local categories, not URLs, IDs or remote bodies.
For an operator-controlled private CA, additional_ca_pem accepts one PEM
certificate as bytes (≤64 KiB) and extends platform trust. It is validated before
queries. Hostname verification remains active; tickets cannot change trust roots.

All bytes are provisional until transport finishes. The result is an upstream
regional response that may overreturn records. Decoding/filtering and invalidating
partial downstream effects remain the caller's responsibility. Report states
are CamelCase spellings of the draft states; source_consistency is Unverified
and integrity is TransportOnly. These are unstable pre-alpha interfaces.

Reports also expose phase (Admission, Ticketing, Fetching or Draining), retained
after completion/failure and during retry waits. may_have_partial_output is true
when a failed/cancelled query has already exposed bytes. Invalidate those bytes
and their downstream effects; close cannot retract them. The retries count
includes admitted attempts after completed waits, excluding an interrupted wait.
cleanup is NotStarted, InProgress, Complete or Failed with separate cleanup_error;
cleanup_complete is retained for compatibility. CleanupTimeout leaves InProgress
and occupies the client slot until a later close actually completes. A terminal
transport error is preserved even if a later cleanup operation also fails.

Report.memory exposes current_payload_bytes, peak_payload_bytes,
largest_http_fragment_bytes, rust_output_copy_bytes and python_output_copy_bytes.
Payload counts include retained inline blocks, the original accepted extent of
a sliced pending fragment, and a native output Vec until handoff. The largest
HTTP fragment is observed even if admission rejects it. Copy counters name the
Rust read-Vec and Python-owned-bytes operations, excluding JSON/base64/TLS/HTTP
internals and allocator slack. Read after exhaustion/close for stable comparison;
concurrent handoff can temporarily precede the corresponding Python copy count.

## Optional supervised BAM output

Import filter_bam and AnalysisReport from genewire.analysis. With an open stream,
call filter_bam(stream, destination, reference, start, end). It fully consumes and
closes the stream and returns an AnalysisReport; inspect its state, error,
transport, exit_code, output_committed and cleanup_complete fields. The filter
region must match stream.region, the tuple from the original Client.open call.
Local invalid configuration raises GeneWireError before altering the stream.

The built-in subprocess decodes all BAM through pysam/HTSlib and writes mapped
records whose reference matches and whose alignment overlaps [start, end).
AnalysisComplete requires both transport and decoder success. Existing output
paths are refused. Output is written to a mode-0600 temporary file in the target
directory and exposed by atomic no-overwrite hard-link creation after the gates.
Failure removes staging; it does not undo unrelated caller effects.

Defaults: 600 s analysis deadline, 5 s child-cleanup policy, 1 GiB output budget,
64 KiB discarded diagnostics and one queued 64 KiB input chunk. Child TERM/KILL
waits share cleanup_timeout_s; input-thread join gets another such budget, then
stream.close uses its native cleanup budget. Reports identify unfinished cleanup.
Blocking filesystem/kernel operations are not given a hard termination guarantee.
The supervisor currently requires POSIX and passed on the recorded macOS/Linux
runners. Windows, arbitrary spawned descendants and clinical analysis are
outside this adapter's qualification. No general-purpose subprocess API is public.
SIGINT cleanup and abrupt decoder death have dedicated checks. A hard-killed
supervisor cannot run finalizers or promise removal of its provisional files;
crash recovery is outside the current contract.

## Optional recoverable BAM jobs

Import `recover_bam` and `RecoveryReport` from `genewire.recovery`. This separate
local M3 adapter takes `(client, object_id, reference, start, end, destination,
workspace, *, expected_sha256=...)`. Pass an expected lowercase SHA-256 for the
exact encoded upstream regional response obtained through a trusted external
channel. It is not the digest of a separately re-encoded filtered BAM. Digest
discovery and server manifest support are not implemented.

Use an absent destination and an absent or existing private mode-0700 workspace
in the same parent directory on a local POSIX filesystem. Keep both outside the
repository. Reinvoke with the same service/object/region/destination/limits/digest
to recover. Incomplete downloads restart from zero. A synced, complete, verified
source is reused for supervised decoding without another network request. The
verified result and receipt remain retained after publication to recognize a
post-link crash or retry without creating a new output inode. Do not remove or
replace the workspace/lock while another job owns it.

Inspect `state`, `error`, `phase`, `source_reused`, `source_bytes`, `output_bytes`,
`output_committed`, `sync_confirmed` and `transport`. Complete means the required
sync calls and original output publication were confirmed. A post-link failure
can report `output_committed=True`, `sync_confirmed=False`; retry the same job.
False does not assert no conflicting path exists. A recovered invocation has
`transport=None`; it does not invent a network attempt. Local invalid scalar
options raise GeneWireError before touching disk; runtime failures return
categories including CheckpointInvalid, CheckpointMismatch, IntegrityFailed,
DestinationExists, RecoveryBusy, StorageFailure and the existing stream/consumer
categories. KeyboardInterrupt propagates; the next invocation can recover.

Defaults are 1 GiB each for `max_source_bytes` and `max_output_bytes`, plus the
same decoder deadline/cleanup defaults as `filter_bam`. Network deadlines still
come from Client. File payload is bounded separately from filesystem metadata,
device caches and process memory. Sync confirmation is not proof against power
loss. The local recovery harness and its source-bound report were exercised:

```bash
.venv/bin/python tools/check_recovery.py --report /tmp/genewire-recovery.json
```

It uses synthetic loopback data, fresh child clients and actual SIGKILL plus
injected storage errors. See [M3 evidence and remaining gates](project/M3-LOCAL.md).
The full unittest discovery command above also includes the recovery tests.

## Independent server and resource checks

The recorded htsget-axum build uses MIT-licensed
[htsget-rs source 2a91e661](https://github.com/umccr/htsget-rs/tree/2a91e661e6a287e3adf30e65c26a8f47697f3548),
Rust 1.93.0, its Cargo.lock and `-p htsget-axum --no-default-features`.
Build it separately from this workspace. Keep the upstream checkout/build outside
the repository and exclude bundled data; the prepared CI workflow records the
source checkout/build steps. Set HTSGET_AXUM_BIN to that build's executable.

These commands were exercised with a separately built binary:

```bash
.venv/bin/python tools/check_interop.py --server "$HTSGET_AXUM_BIN" --report /tmp/genewire-interop.json
.venv/bin/python tools/check_resources.py --report /tmp/genewire-resources.json
```

The interoperability runner starts two loopback HTTP listeners, generates original
synthetic BAM/BAI, checks Q1–Q5 through the supervised adapter and compares with
HTSlib's independent htsget retrieval and indexed local reads. It stops the server
and removes genomic/config files. The configured server source pin is a build
input; the harness records the supplied binary hash, not a verified source-to-
binary attestation. Source hashes and raw reports are in the M2 ledger.

The resource runner serves 64 MiB of opaque pattern bytes from a separate process
context and measures fresh clients that discard or retain returned chunks. It
checks byte count and SHA-256. It records RSS high-water marks, Python tracemalloc
and elapsed time once per mode. The payload is not valid BAM, and timings are not
a benchmark or advantage claim. Native allocation/copy accounting remains open.

## Continuous integration evidence

[checks.yml](../.github/workflows/checks.yml) pins action commits, Rust/uv versions,
the Python minor line and the independent server source. Its Linux/macOS jobs run
native, Python, server and resource checks without publishing packages. The
[recorded run](project/CI-VALIDATION.md) passed and its synthetic JSON artifacts
were downloaded, source-checked and archived. This qualifies the tested revision
and observed runners, not future changes or all Python/OS versions.

## Source layout

- crates/genewire-core: query validation, strict tickets, pinned HTTP, ordered
  reads, retry admission, cancellation, deadlines and explicit close.
- crates/genewire-python: PyO3 bridge; blocking Rust work detaches from Python.
- python/genewire: typed Python convenience interface and context management.
- crates/genewire-core/tests and tests: loopback behavior/fault and native/BAM tests.
- Cargo.lock and uv.lock: dependency resolution for this development build.

Generated native libraries, virtual environments, build output, certificates and
genomic files must stay untracked. Evaluation JSON contains synthetic outputs and
method/source hashes only. No published artifact exists.
