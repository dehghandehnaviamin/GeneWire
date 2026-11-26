# GeneWire roadmap

**M0's initial desk review is prepared; its recommendation awaits review.**
M1–M6 are planned. The owner selected regional retrieval/streaming, a Rust core
and possible Python high-level integration. The scope refinements below are M0
proposals, not approval to implement them. This roadmap has evidence gates rather than delivery dates. Feasibility
may lead to a scope reduction, an extension of an existing standard, or a no-go.

| Milestone | Scope | Exit criteria |
| --- | --- | --- |
| M0 — Research and Feasibility | Regional use cases, constraints, existing standards, Rust/Python direction, evaluation plan | [Desk review prepared](docs/research/README.md); recommendation and domain assumptions require review; no experiments run |
| M1 — Protocol Specification | Candidate reuse profile, stream/completion states, errors, security and Rust/Python boundaries | Reviewable design; resource limits; coordinate/reference semantics; candidate conformance vectors; clear decision on whether any wire extension is necessary |
| M2 — Core Protocol | Proposed Rust core interoperating with the selected existing mechanism; bounded I/O and stream consumption | Working reference path; malformed/fragmented input tests; capability/incompatibility behavior; reproducible contributor setup and CI |
| M3 — Reliable Transfer Engine | Streaming, acknowledgements, object verification, checkpoints, recovery | Fault tests covering interruption, truncation, corruption, stale state, cancellation and resource exhaustion; documented durable acceptance semantics |
| M4 — Genomic Extensions | Incremental FASTA/FASTQ, SAM/BAM, CRAM, VCF/BCF investigation | Per-format scope and versions; synthetic licensed fixtures; reference/index dependency tests; domain review; explicit opaque-transfer versus semantic-support matrix |
| M5 — Developer Experience | CLI, Rust/Python integration, packaging, examples, operational guidance | Installation from a real artifact; executable examples; supported toolchain/interpreter and wheel policy; diagnostics that avoid sensitive data; interoperability guide |
| M6 — Alpha Release | Conformance, reproducible performance evaluation, release preparation | Published methods and limitations; security review findings tracked; interoperability evidence; changelog, versioning and support policy; explicit release approval |

## Sequence and review gates

The bootstrap's initial push was verified and the owner authorized M0 on
2026-11-26. M0's recommendation remains proposed for owner review; M1 has not
started. Research decisions precede protocol specification;
specification review precedes application or protocol implementation. Testing and
security review accompany implementation, while comparative benchmarking and
release preparation require a functioning, correctness-checked system.

There is no stable wire protocol or compatibility commitment yet. No release is
scheduled. Acceptance of an RFC does not make its feature implemented.

The [M0 recommendation](docs/research/feasibility-decision.md) is conditional go
for reuse-first design, with no demonstrated need yet for a new binary wire
protocol. Existing regional clients must be fair baselines. Choosing Rust does
not itself justify a transport change or establish an end-to-end speedup.

## Out of scope for the initial direction

Clinical decision-making, variant interpretation, replacing genomic formats,
hosting patient datasets, a new cryptographic primitive, and claims of regulatory
compliance. Existing transport, retrieval, encryption, and storage standards must
be evaluated before introducing new mechanisms.

Progress is tracked in [STATUS.md](docs/project/STATUS.md),
[TASKS.md](docs/project/TASKS.md), and GitHub milestones. Roadmap changes require
an explanation of new evidence and a decision record.
