# M2 local implementation evidence

**Evaluation:** 2026-11-26 through 2026-11-27. **State:** Working local M2 path;
remaining qualification and remote CI gates are open.

**D016/D017 follow-up:** The owner approved remaining engineering checks,
commit/push and actual CI verification. The prepared D015 state is preserved at
f4d8866; later payload/copy instrumentation and process-failure checks passed
47 Rust and 34 Python/native tests locally. Publication/CI verification is now
authorized; remote results will be recorded after observation.

The owner instructed continued development and will arrange the final university
review. This defers external scientific review; it does not establish scientific
sign-off, production readiness, release approval or new publication authorization.
D010/D014/D015 in [the decision register](DECISIONS.md) define local scope.

Initial implementation b741872 was integrated with the prepared M1/M2 history
at e9be690 and published under D012. D014/D015 are later local working-tree
changes. Raw reports bind the evaluated implementation inputs to SHA-256 file
hashes without claiming those changes have been committed or published.

## Implemented transport

The Python-independent Rust core uses pinned Tokio 1.54.1 and reqwest 0.13.5;
the separate bridge uses PyO3 0.30.1 and maturin 1.16.0. Cargo.lock and uv.lock
record resolution. The byte API has no third-party Python runtime dependency;
the optional `analysis` extra adds pysam 0.24.1 for supervised BAM decode/filter.

The core is a synchronous pull reader over asynchronous HTTP, without a producer
queue or speculative prefetch. Public reads are positive and at most 256 KiB.
Ticket JSON rejects duplicate keys, excessive depth/count/size, invalid types,
base64 and unsafe headers. Bytes concatenate in ticket order. Input supports one
named nonempty zero-based half-open BAM interval, not whole-file/CRAM/variants.

The first 64 MiB opaque probe found that reqwest can yield body fragments larger
than the original 256 KiB restriction. The core now admits a fragment only if it
fits the remaining draft 2 MiB payload window after reserving remaining inline
bytes and one maximum-sized read copy. An empty Bytes view is released before
the next body poll so it does not retain its old allocation. Public chunk limits
are unchanged. HTTP/library buffers, metadata, parse-time allocations and retained
caller output remain additional memory. This is not a complete allocation audit
or a proven process-memory ceiling; unusually large library fragments still fail.

HTTP uses explicit origin/port and operator-supplied IP pins, with no ambient
DNS, proxies, cookies, library retries/redirects, content decoding or TLS key logs.
The connector receives pins and the observed peer is checked. HTTPS certificate
and hostname verification remain enabled. One additional operator-configured PEM
trust anchor (≤64 KiB) is validated before queries; tickets cannot choose roots.
Same-origin redirects are bounded; cross-origin redirects fail. Separate data
origins and ticket-supplied Authorization require explicit operator policy.
HTTP/2 and connection reuse remain deferred; each hop builds a fresh HTTP client.

Ticket/block retries cover selected transient failures and 429/500/502/503/504.
Tickets retry only before acceptance; blocks only before any current-block output
is exposed. Each has three total attempts. Earlier blocks are preserved without
replay; observed validator changes fail. Unaccepted partial ticket bytes are
discarded. One ticket deadline covers all requests, body reads and waits.
Retry-After is waited in full or a deadline/cancellation prevents the next attempt;
unrepresentable timer durations fail explicitly. Default waits are 1 s and 2 s.
Counts include admitted retries after completed waits, excluding interrupted waits.
Policy, authorization, JSON, encoding, resource and declared-length failures do
not retry. Connection setup includes TLS and is conservatively nonretryable.

## Ownership, outcomes and cleanup

Query handles retain the runtime. A watchdog enforces the overall deadline during
caller pauses. One-reader admission and a serialized public handoff coordinate
reads, cancellation and terminal outcome. A committed handoff can finish after
another thread observes cancellation; no new handoff commits afterward.

Rust/Python reports expose state, sanitized category, bytes/retries, retained
phase, `may_have_partial_output`, configured upstream profile and capability basis.
`HtsgetBamRegional` / `Configured` describes an assumption selected by the client;
the core does not fetch service-info, infer a version or claim server conformance.
Unsupported Python profiles fail locally. Scientific consistency is Unverified
and integrity is TransportOnly even after successful transport.

Cleanup is separate: NotStarted, InProgress, Complete or Failed, with a separate
cleanup error and the retained compatibility boolean `cleanup_complete`.
Concurrent closes use bounded admission to cleanup. A timeout retains InProgress
and the query slot; a later close can finish cleanup. Worker-join failure reports
Failed without rewriting transport. Reader panic becomes sanitized InternalFailure.
Normal interpreter exit with a retained stream has local subprocess evidence;
use during interpreter teardown, inherited handles after fork, subinterpreters
and free-threaded Python remain outside the qualified subset.

## Supervised BAM analysis

`genewire.analysis.filter_bam` consumes and closes an original query stream.
Its explicit filter region must match that query. A new subprocess fully decodes
using pysam/HTSlib, selects mapped records overlapping the declared interval and
writes BAM. Source aliases, arbitrary CIGAR semantics and record completeness
are not inferred or scientifically certified.

The POSIX supervisor has one queued 64 KiB input chunk plus producer/pending
chunks, nonblocking child pipes, a finite output budget and a 64 KiB diagnostic
budget. Diagnostics are discarded, not included in reports. A separate analysis
deadline cancels transport and shuts down the child session. TERM/KILL waits,
input-thread join and native stream close each have explicit cleanup policies;
the child and pump waits can add up to twice `cleanup_timeout_s`, followed by the
core's own close budget. This is cooperative library/process cleanup, not a hard
wall-clock guarantee against blocked filesystem/kernel operations. Only owned
child/input-thread/native cleanup is reported; arbitrary daemonized descendants
are not a supported decoder contract.

Output is staged in the destination directory, initially mode 0600. Only after
transport EOF, full built-in decoder success and owned cleanup does atomic hard
link creation expose the final name. Existing destinations are refused; failure
removes provisional files. No durable transaction, arbitrary external rollback
or exactly-once effects are promised. A terminal successful transport remains
successful if the decoder subsequently fails; the analysis result is Failed.

## Checks observed

Runner: macOS 27.0 arm64; Rust/Cargo 1.93.0; CPython 3.14.6; uv 0.13.10;
maturin 1.16.0; pysam 0.24.1 reporting HTSlib/samtools 1.24. This differs from
the 1.25 manual reviewed during M1 and is not a platform support matrix.

| Check | Observed scope |
| --- | --- |
| Rust tests | 45 passed: 39 HTTP/fault tests plus six private lifecycle tests; no skips |
| Python/native tests | 31 passed without skips; byte ownership, lifetime, profiles, TLS/IPv6, normal process exit and supervised BAM success/failure/cleanup |
| Static/build | Locked setup with analysis extra, editable native rebuild, clippy with warnings denied, formatting |
| Tiny oracle | Q1–Q5 matched A/B/C/D handwritten names and multiplicities; invalid-BAM and decodable-omission controls retained |
| Independent server | Q1–Q5 through real local htsget-rs; full supervised decode and exact declared filtering matched truth |
| Independent baselines | HTSlib's own htsget ticket/block retrieval and direct indexed HTSlib both matched the same five cases |
| Resource probe | One 64 MiB opaque transfer in each of two fresh client processes; byte count/SHA-256 matched, server RSS excluded |
| CI | Immutable-action-pinned Linux/macOS workflow prepared and YAML parsed; no remote execution result |
| Documentation/assets | 158 local Markdown file links resolved; SVG structure/accessibility and evidence source hashes checked; updated architecture/lifecycle PNG renders inspected |

Source and method details: [interoperability report](evidence/2026-11-27-interop.json),
[resource report](evidence/2026-11-27-resources.json),
[dependency features/licenses](evidence/2026-11-27-dependencies.json),
[working commands](../development.md). The htsget-rs source is MIT licensed,
pinned at [2a91e661](https://github.com/umccr/htsget-rs/tree/2a91e661e6a287e3adf30e65c26a8f47697f3548),
built without default features and run on two loopback HTTP origins with generated
BAM/BAI only. No bundled upstream data is used. The binary reports CLI version
0.23.0 while package/service-info says 0.10.0; the raw report preserves both.
Neither upstream's own tests nor its feature claims are GeneWire evidence.

The local mock fixture and real server can overreturn all four records. Exact
selection belongs to the declared downstream adapter. The omitted-record control
still demonstrates that successful transport/full decoding cannot prove scientific
completeness. No private genomic data, BAM/BAI, certificates or keys are committed.

The sandbox initially blocked loopback sockets and uv's global cache; successful
runs used permitted loopback access and a task-local cache. No external genomic
service received data. Raw resource timings are single-run observations with no
baseline timing comparison, repetitions or ranking; they are not benchmarks.

The raw resource report retains baseline/peak RSS, current/peak Python-traced
memory and timing. These are process high-water marks and Python measurements,
not isolated native allocation counts or portable limits.

The 128-node Rust metadata graph was inspected for the current macOS target.
Reqwest enables rustls/stream, with default/native-tls/cookies/decompression/http2
features absent; Hyper enables HTTP/1, and Rustls enables TLS 1.2 plus its normal
TLS 1.3 path. The configured minimum is TLS 1.2. PyO3 enables abi3 and extension
module support; its feature labels do not establish interpreter compatibility.
The dependency report records declared licenses and effective features without
machine paths. It is not a vulnerability scan or a redistribution-license audit.

## Candidate scenarios and remaining gates

The [follow-up resource report](evidence/2026-11-27-followup-resources.json)
checks current/peak accepted payload, original pending storage extents and
both named output-copy boundaries. In each 64 MiB retention mode, accepted peak
was 483,328 bytes, each copy counter was 67,108,864 bytes, and retained payload
was zero after close. This excludes allocator slack, TLS/HTTP/JSON buffers and
caller retention. Those exclusions are not silently represented as zero memory.
The [follow-up server report](evidence/2026-11-27-followup-interop.json) records
the same five matched cases with the instrumented implementation.

Actual process-failure checks now cover decoder SIGKILL, supervisor SIGINT
(child reaped, native stream closed and staging removed), and native os._exit
with provisional output. SIGKILL of the supervisor itself cannot execute cleanup;
staging files/daemonized descendants after such a crash are outside this contract.
The initial D015 reports above carry source_commit=f4d8866; follow-up hashes are
checked against the later source. Do not relabel an old measurement as a new run.

Executable tests address selected variants across C01–C30; the draft JSON remains
design input rather than a runnable or fully passing suite. D015 adds dedicated
C06 fresh-query separation, C20 handoff orderings, C22 cleanup timeout/retry,
C25 panic translation, C26 supervised consumer and one C28 unsupported-profile
case. C12 full native allocation/copy accounting and other variants remain open.

Before M2 exit:

- Qualify the accepted-payload accounting and process checks on CI runners. Do
  not reinterpret those counters as allocator/TLS/HTTP/JSON/decoder RSS limits.
- Retain explicit exclusions for interpreter teardown, hard-killed supervisors,
  arbitrary descendants and other failure variants beyond the narrow P0 path.
- Exercise the prepared CI on actual Linux/macOS runners after authorized remote
  publication. Local YAML/command checks do not supply a passing GitHub run.
- Keep domain/scientific review deferred to the owner's university process and
  record actual findings before making wider scientific or release claims.

No comparative performance advantage, full conformance, security audit, durable
resume, production approval or release is claimed. M3–M6 remain planned.
