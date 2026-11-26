# GeneWire roadmap

**All milestones are planned.** The current deliverable is a documentation-only
bootstrap. This roadmap has evidence gates rather than delivery dates. Feasibility
may lead to a scope reduction, an extension of an existing standard, or a no-go.

| Milestone | Scope | Exit criteria |
| --- | --- | --- |
| M0 — Research and Feasibility | Use cases, constraints, existing tools and standards, evaluation plan | Primary-source comparison; privacy and genomic requirements; proposed baseline workloads; documented go/no-go and scope decision |
| M1 — Protocol Specification | Session and transfer models, manifest proposal, errors, versions, transport evaluation | Reviewable specification draft; security threat model; resource limits; coordinate/reference semantics; candidate conformance vectors; documented unresolved questions |
| M2 — Core Protocol | Proposed Python/asyncio reference, negotiation, framing, bounded I/O | Working two-peer exchange; malformed/fragmented input tests; version incompatibility behavior; reproducible contributor setup and CI |
| M3 — Reliable Transfer Engine | Streaming, acknowledgements, object verification, checkpoints, recovery | Fault tests covering interruption, truncation, corruption, stale state, cancellation and resource exhaustion; documented durable acceptance semantics |
| M4 — Genomic Extensions | Incremental FASTA/FASTQ, SAM/BAM, CRAM, VCF/BCF investigation | Per-format scope and versions; synthetic licensed fixtures; reference/index dependency tests; domain review; explicit opaque-transfer versus semantic-support matrix |
| M5 — Developer Experience | CLI, packaging, examples, operational guidance | Installation from a real artifact; executable examples; supported Python policy; diagnostics that avoid sensitive data; independent implementation guide |
| M6 — Alpha Release | Conformance, reproducible performance evaluation, release preparation | Published methods and limitations; security review findings tracked; interoperability evidence; changelog, versioning and support policy; explicit release approval |

## Sequence and review gates

The bootstrap's initial push must be verified and the project owner must approve
the bootstrap before M0 begins. Research decisions precede protocol specification;
specification review precedes application or protocol implementation. Testing and
security review accompany implementation, while comparative benchmarking and
release preparation require a functioning, correctness-checked system.

There is no stable wire protocol or compatibility commitment yet. No release is
scheduled. Acceptance of an RFC does not make its feature implemented.

## Out of scope for the initial direction

Clinical decision-making, variant interpretation, replacing genomic formats,
hosting patient datasets, a new cryptographic primitive, and claims of regulatory
compliance. Existing transport, retrieval, encryption, and storage standards must
be evaluated before introducing new mechanisms.

Progress is tracked in [STATUS.md](docs/project/STATUS.md),
[TASKS.md](docs/project/TASKS.md), and GitHub milestones. Roadmap changes require
an explanation of new evidence and a decision record.
