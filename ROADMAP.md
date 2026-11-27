# GeneWire roadmap

**M0 is published; M1 is the design basis. The narrow M2 reference gate is complete.**
M3 has a local verified-BAM-job increment; its full exit remains open. M4–M6
are planned. The owner selected regional retrieval/streaming, a Rust core
and Python high-level integration. The first subset and integration details
remain provisional beyond the implemented subset. The owner authorized local work
and delegated product/business decisions. This roadmap has evidence gates rather than delivery dates. Feasibility
may lead to a scope reduction, an extension of an existing standard, or a no-go.

| Milestone | Scope | Exit criteria |
| --- | --- | --- |
| M0 — Research and Feasibility | Regional use cases, constraints, existing standards, Rust/Python direction, evaluation plan | [Published desk review](docs/research/README.md); direction accepted for M1; domain review and experiments unclaimed |
| M1 — Protocol Specification | [RFC 0001](docs/rfcs/0001-regional-streaming-profile.md), client profile, lifecycle, boundaries, security and 30 candidate scenarios | Draft prepared; review subset/retry/consumer policy and budgets; no new binary wire format justified |
| M2 — Core Protocol | Rust/Python transport, supervised BAM adapter, real-server/HTSlib comparison, failure/race checks and payload/copy/RSS probes; [scope](docs/project/M2-LOCAL.md) | Complete for the narrow single-region BAM reference path: [observed Linux/macOS CI and exit gates](docs/project/CI-VALIDATION.md); full M1 conformance, broader qualification and scientific sign-off unclaimed |
| M3 — Reliable Transfer Engine | Streaming, acknowledgements, object verification, checkpoints, recovery | Fault tests covering interruption, truncation, corruption, stale state, cancellation and resource exhaustion; documented durable acceptance semantics. [Local verified-source BAM jobs](docs/project/M3-LOCAL.md) are a first subset; full exit and cross-platform qualification remain open |
| M4 — Genomic Extensions | Incremental FASTA/FASTQ, SAM/BAM, CRAM, VCF/BCF investigation | Per-format scope and versions; synthetic licensed fixtures; reference/index dependency tests; domain review; explicit opaque-transfer versus semantic-support matrix |
| M5 — Developer Experience | CLI, Rust/Python integration, packaging, examples, operational guidance | Installation from a real artifact; executable examples; supported toolchain/interpreter and wheel policy; diagnostics that avoid sensitive data; interoperability guide |
| M6 — Alpha Release | Conformance, reproducible performance evaluation, release preparation | Published methods and limitations; security review findings tracked; interoperability evidence; changelog, versioning and support policy; explicit release approval |

## Sequence and review gates

The bootstrap's initial push was verified and the owner authorized M0 on
2026-11-26. After M0 publication, the owner instructed continuation into M1.
The owner subsequently instructed local M2 continuation and delegated product/business
decisions. M1 contracts are provisional beyond verified local behavior. Research precedes specification;
specification review precedes application or protocol implementation. Testing and
security review accompany implementation, while comparative benchmarking and
release preparation require a functioning, correctness-checked system.

The owner will arrange the final university review and has instructed continued
local development. This defers external scientific review without claiming that
the fixture or broader genomic semantics have already been independently approved.

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
