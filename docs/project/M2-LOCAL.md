# M2 local implementation evidence

**Evaluation:** 2026-11-26; final local checks refreshed 2026-11-27. **State:** First working increment; M2 remains in progress.
The owner instructed local continuation and delegated product/business choices.
No GitHub push, merge, issue update, package publication or deployment is authorized
by that instruction. M1 is accepted as the direction for this local prototype;
the complete draft is not claimed conformant or scientifically reviewed.

Implementation revision: b741872933b746c04e184ae4f76ad3c4b66721a3 (local commit).

## Implemented path and engineering choices

A two-crate Cargo workspace separates the Python-independent Rust core from its
PyO3 binding. Tokio 1.54.1, reqwest 0.13.5 and PyO3 0.30.1 are pinned direct
dependencies. Cargo.lock records the resolved graph. Maturin 1.16.0 builds the
local extension; Python runtime code has no third-party Python dependency.

The initial design is implemented as a synchronous pull reader over async HTTP.
It has no producer queue or speculative prefetch. One network-body fragment and
a bounded output copy are handled at a time; all inline blocks fit within the
bounded ticket. An individual HTTP fragment larger than 256 KiB fails explicitly.
This extra restriction is not an upstream protocol rule. Payload/RSS behavior
has not been measured or certified against the draft 2 MiB budget.

Query handles retain the runtime. A query watchdog enforces the overall deadline
even during caller pauses. A serialized public handoff, immutable terminal report,
one-reader guard, cancellation token and explicit close coordinate read/close.
close waits for the reader and the owned watchdog under its cleanup budget.
Library-internal task behavior and process/interpreter shutdown need more review.

Ticket JSON rejects duplicate keys, excessive depth/count/size, ill-typed fields,
invalid base64 and unsafe headers. Bytes concatenate in ticket order. Only BAM,
one named nonempty interval, HTTPS and bounded base64 inline data are exposed.
Exact selection and reference aliases are not inferred.

HTTP uses explicit origin/port and operator-supplied IP pins, without ambient DNS,
proxies, cookies, automatic redirects/retries, HTTP content decoding or TLS key
logging. The connector receives the pins and the observed socket peer is checked.
Hostname/certificate verification remains enabled. Same-origin redirects are
bounded; cross-origin redirects fail. Direct data origins can be authorized
separately. Data Authorization headers require explicit per-origin permission.

GET block retries cover selected transient failures and 429/500/502/503/504 before
any current-block output is exposed. Earlier output is preserved without replay;
changed observed validators fail. A positive Retry-After is waited in full or
interrupted by the query deadline. Ticket retries are not yet implemented.
Connection-setup failures are conservatively nonretryable NetworkPolicy errors
because they can include TLS failures. HTTP/2 is disabled and a fresh HTTP client
is built for each hop; connection reuse/performance tuning is deferred.

## Checks observed

Environment: macOS 27.0 arm64; rustc/cargo 1.93.0; CPython 3.14.6; uv 0.13.10;
maturin 1.16.0; pysam 0.24.1 with reported HTSlib/samtools 1.24. This differs from
the 1.25 manual reviewed during design. It is not a cross-platform support claim.

| Check | Observed scope |
| --- | --- |
| Rust behavior tests | 28 passed; loopback request/response, malformed tickets, ranges/lengths/encoding, credentials, retry, cancellation, deadlines and admission |
| Python/native tests | 12 passed; no skips; ownership, runtime lifetime, detached waits, concurrent reader, context cleanup, error sanitization and TLS rejection |
| Synthetic regional truth | Q1–Q5 matched handwritten expected names and multiplicities through 7-byte Python reads and a separate HTSlib decoder subprocess |
| Invalid BAM negative control | Transport complete; mature decoder exits unsuccessfully |
| Omitted-record negative control | Valid BAM decodes and transport completes, but controlled expected B,D differs from returned B |
| Build/setup | Locked Cargo builds; local abi3 extension; locked uv setup and maturin editable rebuild |

The fixture deliberately overreturns all four A/B/C/D records. The analysis
process performs the declared overlap filter. This checks separation of raw
transport and exact selection, not a real server's region-selection behavior.
All payload is original synthetic data generated in temporary directories;
no BAM or private genomic data is committed. This is a tiny oracle, not domain
sign-off or evidence about arbitrary CIGARs, references, variants or clinical use.

## Relationship to the 30 draft scenarios

The executable tests are not a claim that all 30 candidate scenarios pass.
Their concrete observations address parts of C01–C05, C07–C11, C13–C19,
C21, C23–C24, C27 and C29–C30. Examples are first-response 503 retry, an exposed
chunked disconnect, validator change, a rejected full response to a Range request,
and cross-origin control-token separation. Consult the test names for exact scope.

C06 cross-query recovery policy, C12 full memory accounting, C20 committed-handoff
race, C22 cleanup timeout, C25 panic injection, C26 a product analysis supervisor,
and C28 unsupported-mode error behavior still need dedicated evidence. Additional
variants of addressed scenarios also remain. The candidate JSON is retained as
design input rather than falsely relabeled as a runnable/fully passing suite.

## Remaining M2 gates

- Qualify and run an independent real htsget server on the synthetic fixture;
  mock HTTP endpoints do not establish interoperability.
- Pin an independent existing client and indexed baseline before comparison.
- Implement bounded ticket retries, capability assumptions/reporting and the
  remaining concurrency, cleanup, panic and malformed-response variants.
- Extend structured reports with failure phase, explicit partial-output flag and
  richer cleanup status; current reports expose state, category, counts and a
  cleanup-complete boolean.
- Build a reviewed analysis supervisor with bounded process shutdown; current
  process supervision exists only in the tiny integration test.
- Measure payload/RSS, Python retained memory, copies and latency; inspect native
  dependencies/features and TLS/address policy, including IPv6 and valid HTTPS.
- Qualify interpreter/process shutdown and additional build environments; add and
  exercise CI before claiming M2 exit or supported platforms.

No comparative benchmark, full conformance, security audit, durable resume,
production approval or release is claimed. See [local commands](../development.md)
and [the draft exit gates](../spec/conformance.md#m2-entry-and-exit-evidence).
