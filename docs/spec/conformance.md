# Conformance and validation plan

**GW-M1-DRAFT-01 — Candidate tests only.** No case below has run against GeneWire.
Validating the JSON/Markdown does not validate network behavior or scientific
correctness. Requirements P01–P18 remain draft client requirements.

## Evidence layers

| Layer | What later evidence must demonstrate |
| --- | --- |
| Contract/unit | Query validation, bounded parsing, range/encoding checks, state transitions and typed errors |
| HTTP/fault integration | Actual wire responses, delays, retries, destination decisions and byte exposure match the contract |
| Python/native integration | Ownership, error propagation, cancellation, close and process/interpreter lifetime behave correctly |
| Real interoperability | Selected client works with a real existing htsget service under the declared subset |
| Genomic oracle | Full decode and intended record multiplicities match independently prepared synthetic truth |
| Performance/resource | Effective RSS, buffers, latency and repeated work are measured under a pinned configuration |

Do not substitute an in-memory mock for real-server interoperability, or a
successful decoder exit for an independent completeness oracle.

## Requirement-to-case map

| Requirement | Candidate cases |
| --- | --- |
| P01 explicit inputs | C27: coordinate/type boundaries, one-base translations |
| P02 limited scope | C28: reject unsupported inputs without broadening |
| P03 upstream request | C29: opaque IDs cannot alter URI authority/path semantics |
| P04 ticket parsing | C02: size/depth/block limits, duplicate keys and wrong types |
| P05 ordered fragments | C01: mixed fragments preserve order; no per-block BAM assumption |
| P06 response validation | C08, C09: ignored/mismatching ranges and truncation |
| P07 encoded-byte preservation | C10: HTTP encoding differs from BAM compression |
| P08 network/credential policy | C13–C15: credential separation, redirect and DNS checks |
| P09 byte output | C01, C24: content/chunk ownership and terminal EOF |
| P10 completion levels | C17, C18: transport, decoder and oracle distinguishable |
| P11 provisional consumer | C17, C26: downstream failure cannot become analysis success |
| P12 exposure-based retry | C03–C07: eligible/forbidden replay paths |
| P13 finite limits | C02, C11, C12, C19: parsing/result/payload/time budgets |
| P14 terminal outcomes | C20–C23: serialized outcomes and truthful cleanup |
| P15 errors/privacy | C16, C21, C25: sanitized reports and API/native failures |
| P16 failure classification | C03, C05, C07–C10, C30: bounded transient retry and nonretryable denial |
| P17 scientific limits | C18: missing record is not magically detected by transport |
| P18 evidence before claims | Entire matrix; require a result ledger before verification labels |

The [JSON vectors](vectors/cases.json) carry stable case IDs, expected outcomes,
requirement references and selected abstract traces. Their fragments are symbolic
transport payload, not valid BAM fixtures. They do not define new htsget fields,
an executable mock server, or a test harness.

Expand each scenario into concrete inputs, response bytes, scheduling points,
expected observations and negative controls before counting it as executed.
Test code must challenge implementation behavior, not merely repeat this table.

## Scientific and baseline setup

Use [M0 W1 and Q1–Q5](../research/evaluation-plan.md#tiny-independent-truth-fixture)
as the first narrow oracle, with independent domain review still required for
expanded semantics. Test exact filtered records separately from the raw upstream
superset. Recompression need not preserve file bytes; do not use a compressed-file
hash as the sole record-equivalence oracle.

Proposed evaluation candidates:

| Role | Candidate | Qualification still required |
| --- | --- | --- |
| Real htsget server | [umccr/htsget-rs](https://github.com/umccr/htsget-rs), local Axum deployment | Pin release/source and configuration; use generated synthetic fixtures rather than bundled datasets |
| Direct indexed baseline and decoder/filter | [samtools/HTSlib](https://www.htslib.org/doc/samtools.html), reviewed manual 1.25 | Pin actual build/features; confirm HTTPS, indices, chosen BAM format and query translation |
| Existing htsget client comparator | Select a maintained independent implementation during M2 setup | Confirm documented subset/version and correct configuration before any ranking |
| Fault harness | Controlled local endpoints with synthetic credentials | Deterministic redirects, DNS/address policy, delays, disconnects and response corruption |

The server README describes its Rust implementation and local-server support.
No server was installed or started here, and its upstream tests/benchmarks are not
GeneWire evidence. A missing independent client comparator prevents comparative
product claims; it does not justify inventing an intentionally weak baseline.

Before use, record versions, licenses, generated-fixture provenance, feature flags,
TLS roots, allowed origins, effective limits and run environment. No production
endpoint, public dataset, external credential or paid service is needed.

## M2 entry and exit evidence

M1 review must resolve the consumer assumption, subset, preferred native binding,
resource budgets and conservative recovery policy. Security/network review must
decide how the actual connection is bound to destination policy. Expanded query
semantics need domain review. Owner approval of implementation remains separate.

A future M2 result ledger should record case ID, implementation/source revision,
environment, exact fixture/configuration, observed output/status, pass/fail,
limitations and raw evidence location. Keep client, server and consumer findings
separate; report unsupported valid upstream behavior as such.

Minimum exits for the narrow reference path: successful real-server query and
full decode; independent tiny truth match; all applicable P0 failures exercised;
Python ownership/close/cancel tests; measured payload/RSS accounting; dependency
and outbound-policy review; working build and CI. No throughput target is set.

Durable checkpoint recovery, variants, CRAM, multi-region semantics, async Python
and release-level compatibility are later work, not implicit P0 completion criteria.
