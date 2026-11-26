# Synthetic regional-streaming evaluation plan

**State:** Proposed plan, 2026-11-26. **Experiments executed:** none.

This document defines evidence to collect after design and tooling approval. It
does not provide runnable commands, generated datasets, a protocol implementation,
test results or performance claims. The primary scope is the owner's choice of
regional retrieval and streaming.

## Questions and hypotheses

| ID | Question | What would refute a need for extra GeneWire behavior? |
| --- | --- | --- |
| H1 | Can existing clients deliver the intended records with the required context? | Correct results and usable diagnostics with existing tools/configuration |
| H2 | Does an interrupted stream lead to ambiguity or unsafe downstream reuse? | Existing integration clearly rejects incomplete work and recovers under the chosen policy |
| H3 | Can latency and memory requirements be met without custom transport? | Baselines satisfy predeclared budgets under representative conditions |
| H4 | Is a small interoperable client/profile useful beyond documented options? | A short upstream contribution or integration guide solves the actual problem |
| H5 | Can the owner-selected Rust core remain efficient through the Python layer? | Binding overhead, copies or callback frequency erase the intended end-to-end benefit |

A failed configuration is not evidence that the protocol lacks a capability.
Diagnose, configure correctly and rerun before proposing a new mechanism.

## Workloads

All sizes and counts below are experimental design choices, not observations.
Record actual serialized sizes after fixture generation; compression makes them
different from sequence or uncompressed-text size.

| ID | Planned workload | Purpose / use cases | Initial scope |
| --- | --- | --- | --- |
| W1 | Tiny coordinate-sorted synthetic BAM with its matching index and hand-audited records | Boundary truth table and streaming correctness; UC01, UC03 | P0 |
| W2 | 100,000 and 1,000,000 synthetic alignment records; same query set with fast, throttled and canceled consumers | Bounded consumption and scaling; UC02 | P0 after W1 correctness |
| W3 | Synthetic CRAM/reference arrangement, missing/wrong reference, deliberately stale index and changed object identity | Dependency/source failures; UC04, UC06 | P0 negative cases, CRAM positive path P1 |
| W4 | Small VCF/BCF with simple variants, then reviewed indel/SV boundary cases; overlapping intervals | Variant semantics and output multiplicity; UC05 | P1; domain review first |
| W5 | Deterministic opaque 1 MiB, 64 MiB and optional 1 GiB objects, plus a declared small object set | Secondary full-object identity and interrupted-copy controls; UC07 | P2; not a regional-speed comparator |

Start with tiny fixtures and confirm disk/memory budgets before increasing size.
Do not create large files on the contributor's machine by default. Larger,
clinically realistic distributions are outside this initial study.

## Fixture provenance and reproducibility

Plan a synthetic reference named syn1 of length 10,000 for W1, with additional
contigs explicitly named syn2 and so on. Never use real sample identifiers or
human reference assemblies to seed these tests.

For future deterministic sequence/opaque-data generation, the proposed recipe is
to concatenate SHA-256 outputs over the UTF-8 strings
"GeneWire/M0/v1|seed=20261126|object=OBJECT_ID|block=BLOCK_NUMBER", substituting
the recorded object ID and decimal block number starting at zero, with no
trailing newline. Truncate to the requested byte length.
For reference bases, map each resulting byte modulo four to A, C, G, T.
This is a fixture recipe, not cryptographic protocol design or biological modeling.

Record the recipe version, seed, object ID, reference and file digests, source
revision, generator environment and compression settings. Hand-author and review
the tiny truth fixture independently of the bulk generator. Future code and
fixtures need license/provenance records; original contributions follow Apache-2.0,
and generated data's reuse terms must be declared explicitly. A seed alone is
not a complete reproducibility record.

For W2, propose single-end mapped records numbered i from zero to N−1 on syn1:
unique name synthetic_i, SAM POS = 1 + ((97 × i) mod 9901), CIGAR 100M, FLAG 0,
MAPQ 60, sequence copied from that reference interval and fixed quality I.
Sort by (POS, i) before indexing. This deliberately simple, repetitive workload
isolates scale; it does not model sequencing errors, coverage or clinical data.
Pin writer metadata/compression for byte-level replay and retain a separate
decoded-record oracle. W3/W4 need their own fully recorded generator and expected
results before execution; this plan does not treat them as already reproducible fixtures.

Use mature format writers/readers for encoding, indexing and full decoding,
pinning their actual versions before running. Reading a current manual is not
proof that a tool is installed or supports a generated format version. The
reviewed format baselines are SAM/BAM 1.6, CRAM 3.1 and VCF 4.5/BCF 2.2; choosing
a narrower writer/server-compatible version requires recording that choice.
[SAM/BAM](https://samtools.github.io/hts-specs/SAMv1.pdf),
[CRAM](https://samtools.github.io/hts-specs/CRAMv3.pdf),
[VCF/BCF](https://samtools.github.io/hts-specs/VCFv4.5.pdf).

Do not copy published datasets into the repository. Keep generated files outside
tracked source. Synthetic content is useful for deterministic correctness and
controlled load; it does not justify general performance claims about real cohorts.

## Tiny independent truth fixture

For W1, propose four mapped records on syn1, with otherwise valid SAM fields,
matching reference bases, unique record identifiers and no additional filters:

| Record | SAM POS | CIGAR | Reference positions occupied (one-based) |
| --- | --- | --- | --- |
| A | 1 | 1M | 1 |
| B | 100 | 1M | 100 |
| C | 101 | 1M | 101 |
| D | 95 | 10M | 95–104 |

The following expected subsets are derived directly from those simple intervals,
not by querying the retrieval implementation under test:

| Query | syn1 interval (zero-based, half-open) | Intended filtered records |
| --- | --- | --- |
| Q1 | [0, 1) | A |
| Q2 | [99, 100) | B, D |
| Q3 | [100, 101) | C, D |
| Q4 | [499, 500) | Empty, with a valid result context |
| Q5 | [99, 101) | B, C, D |
| Q6 | Two overlapping requests: Q2 and Q5 | Evaluate union and per-request multiplicity separately; policy not yet selected |

The oracle is the declared analysis subset. A standards-compliant response that
includes extra records must be assessed separately from any future client-side
filtering. Do not declare the service nonconformant merely because the raw
transport result is larger. Do not deduplicate records only by read name: that
would discard legitimate distinct alignments.

Add unmapped/placed-unmapped records, spliced/deletion CIGARs, contig-end cases,
invalid intervals, missing contigs and variant boundaries as separate reviewed
fixtures. The simple table does not define those semantics. Get a domain review
before extending it or claiming scientific correctness beyond this subset.

## Baselines and fair comparison

| Baseline | Role | Comparison conditions |
| --- | --- | --- |
| B0: local fully decoded fixture | Independent content/oracle sanity check | Not a network-latency competitor |
| B1: existing htsget server and supported client | Primary protocol reuse baseline | Record implementation, revision, advertised formats, authentication, filtering and retry configuration |
| B2: direct indexed remote access through HTSlib/samtools | Existing analysis-access alternative | Same immutable data, index, reference, query and intended output; translate input coordinates explicitly |
| B3: full-object HTTPS copy then local extraction | Coarse comparison for byte movement and repeated queries | Include full download, validation and extraction costs; never label it the only existing solution |
| B4: future GeneWire client/profile candidate | Optional after an accepted design | Same correctness oracle and resource/accounting rules as B1/B2 |

For B4, measure the Rust core directly and the same core through the proposed
Python integration. Record buffer copies, batch sizes, language crossings,
interpreter/build configuration and total process memory. Measure actual
end-to-end latency as well as isolated boundary costs. Neither variant exists
yet. The owner's language direction is documented in
[technology-direction.md](technology-direction.md).

For B1, first prove ordinary server/client interoperability without any GeneWire
extension. Do not create a deliberately weak client just to beat it. If a real
htsget baseline cannot be provisioned, mark B1 unavailable and withhold comparative
conclusions. Mock servers are suitable for fault cases, not interoperability claims.

Keep output formats, compression and parsing work comparable. If the service
re-encodes data, compare the specified decoded records rather than identical
compressed bytes. Count server work separately when source processing differs.
Record cold and warm caches separately, including index and reference caches.

## Faults and acceptance observations

| ID | Planned injection in an isolated environment | Required observation; not a current guarantee |
| --- | --- | --- |
| F1 | Drop connection during a data block, including a partial record | Failed or recovered attempt is explicit; final oracle holds; no silent partial success |
| F2 | Kill/restart the client at selected consumption points, including after local progress persistence | Recovery revalidates identity; downstream provisional effects are handled under a documented policy |
| F3 | Change source/index or return a different ticket/output after interruption | Do not splice incompatible cached prefixes or mix versions |
| F4 | Expire/deny temporary access during retry | Bounded reauthorization/retry or explicit failure; secrets remain absent from logs |
| F5 | Wrong reference, stale index, truncated data, changed block order or corrupted bytes | No success for an incorrect intended result; record the detection layer and cases it cannot detect |
| F6 | Slow consumer, cancellation, peer stall, exhausted memory/disk budget | Bounded queued work, cancellation/timeout outcome and observed cleanup |
| F7 | Off-origin credential trap, redirect loop, disallowed destination or oversized ticket | Policy rejects unsafe fetches; no unrelated credential transmission or uncontrolled resource growth |
| F8 | Range request answered with a full response or mismatching identity/range | No blind append; explicit restart/rejection according to the selected adapter policy |
| F9 | Python caller abandons iteration, cancels or receives a late native failure | Rust work terminates or is accounted for; errors, provisional output and buffer lifetimes remain explicit |

Faults are deterministic where possible, keyed by byte/record progress and a
recorded schedule; use 10%, 50%, 90% of a known transfer as exploratory points.
Use synthetic test credentials and controlled endpoints only. Do not follow
arbitrary ticket URLs during testing.

## Correctness gates

- C1: complete decoding, valid context and exact intended record multiplicities
  after the declared filtering policy; compare against W1's independent truth.
- C2: for exact-object tests, final byte length and independently computed digest
  equal the immutable source. Do not apply that oracle to transformed results.
- C3: dependency identities match the declared fixture; negative reference/index
  cases cannot be counted as successful usable output.
- C4: interrupted or canceled work is never presented as a completed analysis.
- C5: resource and credential policies are checked independently of data correctness.

A quick structural check, an EOF marker or successful parser startup is not
sufficient. Full decoding also cannot prove that an upstream service omitted no
records; the independent oracle matters. Where trusted integrity metadata is
unavailable, report that limit rather than claiming cryptographic verification.

## Metrics and execution record

Measure from a monotonic clock with precisely identified event boundaries:

| Metric | Definition |
| --- | --- |
| Ticket time | Request dispatch to a complete usable ticket/control response |
| Time to first decodable record | Query dispatch to first record accepted by the decoder; not first verified completion |
| Time to completed result | Query dispatch to terminal success after the applicable correctness and completion checks |
| Data movement | Request/response body bytes, retransmitted bytes and total connection traffic separately when observable |
| Useful throughput | Declared result bytes or records per second over a specified interval; do not mix wire and decoded units |
| Resources | Client/server peak RSS, CPU time, queue/prefetch high-water marks and temporary storage |
| Recovery | Fault-to-terminal time, repeated work, bytes/records replayed and final correctness outcome |

Record failure counts and censored/timeout runs alongside successful runs. No
metric is currently measured. No SLO was supplied by the owner. Gather baseline
observations first; predeclare tolerances and meaningful improvement thresholds
before assessing B4 to avoid choosing a favorable threshold afterward.

Proposed exploratory network profiles: 1 Gbit/s with 2 ms RTT; 100 Mbit/s with
50 ms RTT; and the latter with 0.5% injected loss. These are artificial conditions,
not descriptions of real research networks. Apply only on an isolated future
runner and verify actual shaping. Limit the initial matrix to W1/W2, B1/B2 and
single-region queries rather than a costly full Cartesian product.

For each eligible cell, plan 10 independent measured runs after two disclosed
warm-up runs; randomize baseline order using a recorded seed. Separate cold/warm
conditions and faulty/successful runs. Report individual observations, median,
range and failure rate; do not use 10 observations for a persuasive tail-latency
claim. A later confirmatory study needs a sample-size rationale.

The run record must include source/fixture digests, tool and server revisions,
OS/kernel/hardware, CPU/memory/storage, TLS and credential configuration (without
secrets), effective concurrency/buffer limits, network profile, cache state,
query set, fault schedule, timeouts, raw observations and exclusions. Preserve
negative results. AWS/Globus service runs require separate cost and access approval;
no such run is part of this local plan.

## Decision rule

Passing correctness is a prerequisite to performance comparison. Any silent
misleading success is a blocking finding for that candidate. If existing clients
satisfy the requirements, prefer integration/documentation or upstream work.
Consider a wire extension only after identifying a specific unmet requirement
that cannot reasonably be addressed in that way.
