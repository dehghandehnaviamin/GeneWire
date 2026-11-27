# Regional access profile

**GW-M1-DRAFT-01 — Draft requirements.** The local M2 client implements a subset;
[the evidence ledger](../project/M2-LOCAL.md) is authoritative for current behavior. They are not amendments to upstream htsget.

## Input scope

**P01 — Explicit query.** Accept one configured reads-service base, opaque object
ID, named reference and interval [start, end), with explicit BAM output. Require
integer coordinates satisfying 0 ≤ start < end ≤ 2^32−1; reject booleans, floats,
overflow and empty intervals. These restrictions deliberately select a subset of
upstream inputs. Do not infer reference aliases or convert caller coordinates
implicitly. A convenience conversion, if later added, must be named and tested.

**P02 — No silent expansion.** Reject whole-file queries, unmapped-read queries,
multiple intervals, variants, CRAM, projections and unknown output modes in the
first subset. Do not drop unsupported parameters or fetch the entire object as
a fallback. Missing/unavailable service capability is an explicit condition.

The underlying htsget API supports more than this subset, including ordered block
retrieval and potentially extra records in a regional result. A valid empty result
still has format context. [Upstream specification](https://samtools.github.io/hts-specs/htsget.html).

## Request and ticket handling

**P03 — Upstream request.** Use the configured service's GET path for the object
and the existing format/reference/start/end parameters. Build the URI through a
reviewed encoder: an object ID is data, not permission to alter scheme, authority,
base path or query. Test embedded slashes, dot segments, percent signs and Unicode.
Do not introduce a GeneWire endpoint or header.

Service-info is advisory. A successful response may inform capability checking;
if absent, use an explicit administrator-selected upstream profile, not silent
version inference. An advertised contradiction (such as no BAM reads support)
fails before data access. Record the assumption without claiming server conformance.

**P04 — Bounded ticket.** Require a successful JSON ticket with the expected htsget
container, BAM format and at least one block. Check UTF-8/JSON validity, unique
object keys, nesting depth and all configured limits before issuing block fetches.
Reject ill-typed required fields. Ignore unknown optional fields within limits;
never treat them as instructions to expand supported features.

**P05 — Ordered content.** Support policy-approved HTTPS blocks and bounded
base64 inline data blocks. Concatenate block bytes in ticket order, including
header/body blocks. Each block is a fragment of the aggregate stream, not
necessarily an independently decodable BAM file. Optional class metadata must
not cause bytes to be dropped, reordered or treated as independently complete.

## HTTP adapter requirements

**P06 — Validate the response.** Require successful data status and intact HTTP
body completion. If a ticket supplies one explicit inclusive byte range a–b,
support only that range form initially and require a matching 206 Content-Range
with the same endpoints and exactly b−a+1 bytes. Reject multi/suffix/open-ended
ranges as unsupported locally. A full 200 response to that request is not safe
to append. Without a Range header, require 200; unexpected partial responses fail.

Check numeric Content-Length when present and detect body truncation. Counts
include encoded result bytes, not HTTP chunk framing. An empty individual fragment
does not prove an empty scientific result. HTTP validators are not genomic identity.
[RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html#section-14).

**P07 — Preserve representation bytes.** Disable automatic HTTP content
decompression and request identity content encoding. Reject a non-identity HTTP
Content-Encoding in this initial subset. BAM/BGZF compression inside the genomic
format is separate and passes through unchanged. Do not count a differently
decoded HTTP representation as the same ranged bytes.

**P08 — Apply network policy on every request.** Ticket, block and redirect
destinations must pass the [security policy](security-model.md). Do not inherit
control-service credentials into a general-purpose data client. Do not let the
HTTP library retry or follow redirects independently of lifecycle policy.

Reqwest exposes configuration for automatic decoding, proxies and redirects;
actual build features and behavior require tests rather than reliance on defaults.
[Candidate adapter controls](https://docs.rs/reqwest/0.13.5/reqwest/struct.ClientBuilder.html).

## Output and success meaning

**P09 — Encoded output.** Expose ordered, bounded encoded-byte chunks. Chunk
boundaries carry no genomic or upstream-block meaning and may change between
runs. The default output contract is explicitly an upstream regional response,
potentially a superset. It is not a Python record iterator or an exact filtered set.

**P10 — Completion levels.** Report these separately:

| Level | Meaning | Does not establish |
| --- | --- | --- |
| Transport complete | Ticket blocks were consumed in order, HTTP checks passed and delivery drained without a terminal error | Valid BAM, no omitted records, snapshot consistency or cryptographic authenticity |
| Analysis complete | Transport complete plus supervised decoder/filter consumed the full stream and exited successfully under a declared policy | That the upstream service returned every scientifically expected record |
| Oracle matched | A controlled test result matches independent expected records and multiplicities | General clinical correctness or arbitrary real-data correctness |
| Digest matched | A separately trusted expected digest matches the specified serialization, if that optional mechanism is designed later | Authorization or equivalence to a different serialization |

P0 does not implement a digest-matched or durable-checkpoint mode. Distinguish the
absence of that capability from a digest mismatch. Never label ordinary
transport completion "verified genomic data".

The proposed report states output_kind = UpstreamRegionalResponse,
source_consistency = Unverified by default, and integrity = TransportOnly.
An operator's separately documented snapshot attestation may be recorded as
configured evidence, not as a proof generated by the client. Matching validators
on some blocks do not establish a global multi-origin source snapshot.

**P11 — Provisional analysis.** The proposed first Python consumer streams bytes
into a supervised mature decoder/filter. Query-coordinate translation and exact
record selection belong to that adapter's declared policy. It must wait for
both transport and process outcomes; an early process exit, broken pipe, late
HTTP error or decoder failure invalidates output. Caller-owned staging/rollback
is required before exposing scientific artifacts as complete.

## Recovery and resource bounds

**P12 — No ambiguous replay.** Apply the exposure-based retry rule in
[stream-lifecycle.md](stream-lifecycle.md). No persistent checkpoints, cache reuse
across queries, new-ticket prefix splicing or exactly-once consumer effects are
part of this subset. All result bytes from a failed attempt remain provisional.

**P13 — Finite limits.** Proposed starting defaults below are engineering budgets,
not measured operating points or performance promises. Validate configurations
before work; there is no unlimited mode in the initial profile.

| Limit | Proposed default |
| --- | --- |
| Ticket body | 1 MiB; JSON depth 16; 1,024 blocks |
| Inline block | 256 KiB decoded; still subject to ticket/body limits |
| Ticket-supplied request headers per block | 64 entries / 32 KiB aggregate; deny unsafe names |
| Individual emitted chunk / caller read | At most 256 KiB; positive requested read size |
| Rust payload window per query | 2 MiB total across in-flight, pending-delivery and queued owned payload |
| Active block requests per query | One; no speculative block prefetch in P0 |
| Active queries per client | Four; proposed two runtime worker threads |
| Result bytes per query | 1 GiB, encoded output counted once before exposure |
| Connect / ticket / idle-read budgets | 10 s / 30 s / 30 s |
| Overall query deadline | 600 s, including caller backpressure |
| Cleanup wait budget | 5 s; a timeout reports unfinished cleanup |
| Redirects / attempts per block | Three policy-approved redirects / three attempts including the first |

HTTP/TLS library buffers, metadata and Python-retained output are additional
memory. Account for them in measured RSS; the payload window is not a process
memory cap. A full queue stops upstream polling where possible; total deadline
still bounds a paused query. Hold a client concurrency slot until actual task
cleanup completes, even after a failed/canceled outcome.

The idle-read clock applies while actively waiting for network data, not while
polling is intentionally stopped for payload credit; the overall deadline
continues in both cases. Separate wire-attempt bytes from unique accepted output.
Discarding an eligible undelivered attempt releases its payload/result
reservations; retransmission must not count the same logical output twice.

**P14 — Observable terminal result.** Provide one immutable terminal outcome
and separate cleanup status. No new output handoff may be committed after
terminal failure. A concurrent read committed earlier may finish and counts as
partial exposure. On success, queued bytes must be drained before terminal success/EOF;
see the lifecycle's success rule, not just worker task completion.

## Errors and privacy

**P15 — Stable local categories.** Proposed categories:

| Category | Trigger |
| --- | --- |
| InvalidQuery | Scope, type, interval or configuration violation |
| InvalidState | Local API precondition violation; does not overwrite an existing query outcome |
| Unsupported | Feature/format/header/range outside the supported local subset |
| TicketInvalid | Malformed, ambiguous or inconsistent ticket |
| AccessDenied | Authorization denial or expired access; no automatic token renewal |
| NetworkPolicy | Destination, redirect, credential or TLS policy rejection |
| ResponseInvalid | Status, range, length, content encoding or framing mismatch |
| TransportFailed | Network failure without eligible remaining retry |
| ResourceLimit | Ticket, result, buffer/concurrency or other finite budget exceeded |
| DeadlineExceeded | Query/request deadline exhausted |
| Cancelled | Caller cancellation or early close before completion |
| ConsumerFailed | Supervised decoder/filter failure or early exit |
| InternalFailure | Panic/worker failure translated without allowing success |

CleanupTimeout is a separate close/cleanup error, not proof a failed query became
successful. An error report contains category, phase, retry count and
may_have_partial_output; it excludes raw URLs, query IDs, coordinates, credentials,
remote error bodies and decoded records.

ConsumerFailed belongs to the supervisor's outcome when transport has already
completed. It must not rewrite an immutable successful transport report.

**P16 — Fail explicitly.** Preserve meaningful upstream status internally for
classification, but present a sanitized local category. Retry only transient
conditions under P12. An authorization or policy failure is not transient.

**P17 — No silent scientific claims.** Library callers choose whether to require
the analysis adapter; a transport-only caller cannot infer exact record selection.
Production source completeness needs a separate trust/service contract.

**P18 — Verification before promises.** No supported-platform, interoperability,
bounded-memory, cancellation-latency or performance claim becomes verified until
the applicable [conformance evidence](conformance.md) is recorded.
