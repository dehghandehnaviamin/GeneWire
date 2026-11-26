# Regional retrieval: use cases and requirements

**State:** Proposed M0 requirements, 2026-11-26.

**Owner priority:** Regional retrieval and streaming for analysis tools.

The actors and deployments below are design assumptions to validate, not evidence
of customer interviews, a deployed service, or existing GeneWire functionality.

## Actors and deployment assumptions

| Actor | Role and authority |
| --- | --- |
| Analysis caller | Requests records from an identified dataset and reference interval; decides whether provisional output may be consumed |
| Retrieval client | Resolves capabilities, fetches data, applies the agreed result policy and reports completion/failure |
| Data custodian / ticket service | Authorizes requests and describes permitted data access; owns source identity and availability |
| Data endpoint | Serves serialized data, potentially through another origin or object store |
| Reference provider | Supplies explicitly identified reference sequence when decoding requires it |
| Pipeline operator | Sets resource, credential, storage and retention policies; handles incomplete downstream results |

Assume a command-line or workflow consumer first, not a browser UI. A source may
be immutable or may expose a changing logical identifier. The client must know
which case applies before reusing progress or cached material. No endpoint,
credential provider, cloud account or deployment environment has been selected.

## Scenarios

| ID | Priority | Scenario | Proposed acceptance condition | Evaluation |
| --- | --- | --- | --- | --- |
| UC01 | P0 | Stream alignments overlapping one region into an analysis consumer | Decode a coherent result; preserve required context; detect missing expected records and incomplete output | W1, Q1–Q4, C1 |
| UC02 | P0 | A slow consumer pauses or cancels while the source is active | Memory, outstanding work and queues remain bounded; cancellation has an observable terminal outcome | W2, F6 |
| UC03 | P0 | Connection fails mid-result and the caller tries again | Either safely recover or restart explicitly; never silently skip or duplicate consumed output | W1, F1–F4 |
| UC04 | P0 | Source, index, credentials or reference become invalid | Fail or reauthorize under explicit policy; never combine unrelated versions or report success | W3, F3–F5 |
| UC05 | P1 | Retrieve variants or several overlapping intervals | Use a reviewed overlap/multiplicity policy and a matching oracle; do not infer it from read-start positions | W4, Q5–Q6 |
| UC06 | P1 | Retrieve CRAM with external-reference dependencies | Resolve the correct allowed reference or fail; do not silently substitute a similarly named sequence | W3, C3 |
| UC07 | P2 | Download the complete source object or a related object set | Define object identity and required members; distinguish exact bytes from a generated regional response | W5, C2 |

P0 denotes proposed first-scope requirements, not a delivery promise. Workload,
query, fault and correctness IDs are defined in [the evaluation plan](evaluation-plan.md).

## Query and scientific correctness

For the first evaluation, use explicitly named synthetic contigs and a single
interval. Record both the caller's coordinate convention and the selected
backend's convention. The htsget query convention is zero-based and half-open;
the samtools region-string convention is one-based and inclusive. A one-base
test must therefore be translated deliberately. This is a boundary adapter
requirement, not a new GeneWire coordinate specification.
[htsget parameters](https://samtools.github.io/hts-specs/htsget.html#query-parameters),
[samtools regions](https://www.htslib.org/doc/samtools-view.html).

Proposed scientific requirements:

- R01: identify the source, requested reference and interval before consuming data.
- R02: preserve sequence dictionaries and necessary format context; do not silently
  rename contigs or rewrite biological content.
- R03: compare decoded records and their multiplicities against an independently
  prepared oracle. Record order matters only under the declared ordering policy.
- R04: handle records spanning a boundary, empty results, missing contigs and
  overlapping queries deliberately. A parser returning one record proves neither
  completeness nor query correctness.
- R05: treat a response containing extra records as a separate transport-level
  result from the exact subset requested by the analysis caller. Filtering cannot
  provide authorization for data that should never have been disclosed.
- R06: distinguish reference sequence identity, serialized object identity,
  index provenance and the caller's permission to access each resource.

Indexes are dependencies when required by the chosen access path, not mandatory
companions to every genomic file. CRAM can use different reference arrangements;
the fixture plan must declare which one it exercises. Format-specific decisions
need domain review. [SAM/BAM](https://samtools.github.io/hts-specs/SAMv1.pdf),
[CRAM](https://samtools.github.io/hts-specs/CRAMv3.pdf),
[VCF/BCF](https://samtools.github.io/hts-specs/VCFv4.5.pdf).

## Streaming and recovery requirements

R07: report first decodable output separately from verified final completion.
Early output is provisional; a downstream tool might already have changed state
when a late failure occurs. Future integration must define whether such work is
discarded, marked incomplete, or performed in a staging area.

R08: do not assume a transport acknowledgement or received byte count establishes
durable application acceptance. Define the recovery unit, its identity, persisted
state and revalidation rules in M1. Do not splice an old stream prefix into a new
response unless compatibility is established.

R09: preserve logical output order while bounding prefetch. Request completion
must not depend on buffering an entire dataset. Exact limits remain to be chosen.

R10: surface cancellation, exhausted retry budget, authentication failure,
unsupported capability and incomplete output as distinct observable outcomes.
No exactly-once delivery, crash durability or transparent resume guarantee is
approved by these requirements.

R11 (owner constraint): pursue a Rust core for the performance-sensitive path,
with Python as a possible high-level integration. Measure both core and binding
overhead without changing scientific or completion semantics.
See [technology direction](technology-direction.md).

## Trust boundaries and privacy

| Boundary | Concern to resolve in design | Required research/evaluation case |
| --- | --- | --- |
| Caller → client | Ambiguous coordinates, unsupported queries, paths or unreasonable limits | Validate inputs and reject unsupported scope |
| Client → ticket/control service | Identity, authorization and mutable source resolution | Denied/expired access; source changes |
| Ticket → data origin | A returned URL is not authority to expose unrelated credentials or access arbitrary hosts | Origin changes, redirects and malicious destinations |
| Stream → parser/consumer | Malformed data, incomplete records, resource exhaustion, provisional effects | Corruption, truncation, slow consumer, cancellation |
| Reference/index → decoder | Correct name with wrong content or stale index | Wrong-reference and stale-index fixtures |
| Client → local cache/checkpoint/log | Cross-user reuse, sensitive query metadata and replayed state | Cache separation, stale state and log-redaction inspection |

Minimize persisted query metadata. Do not log credential-bearing URLs or headers.
Origin, redirect, credential scoping and outbound-access policies must be reviewed
before any endpoint is followed. All planned tests use controlled local services
and synthetic credentials. No tests against public genomic services are authorized
by this plan. See [SECURITY.md](../../SECURITY.md).

## Non-goals and unanswered questions

No new encryption primitive, genomic file format, clinical interpretation,
consent system, data hosting service or regulatory-compliance claim. A FASTQ
object has no assumed reference-coordinate retrieval contract in this scope.

Still needed: a concrete analysis consumer; desired read/variant scope; realistic
region distribution; acceptable failure/restart behavior; whether service or
client administration is available; and an independent domain review. These
unknowns prevent a production-feasibility or performance conclusion.
