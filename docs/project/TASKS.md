# Task register

This is a curated backlog, not a record of completed research. GitHub milestones
track the same sequence as [ROADMAP.md](../../ROADMAP.md). No deadline is promised.

## Bootstrap checklist

- [x] Inspect local Git state and preserve the existing `main` branch and remote.
- [x] Verify authenticated owner and the existing public, empty repository.
- [x] Prepare original branding and conceptual architecture diagrams.
- [x] Prepare README, contributor guidance, community files, and issue forms.
- [x] Record the approved license scope and preserve official license text.
- [x] Complete rendering, local/external link, template, and sensitive-content checks.
- [x] Configure topics, Discussions, private reporting, labels, and milestones.
- [x] Inspect the complete staged diff, commit, and verify the remote push.
- [ ] Set the social preview through GitHub's repository settings.
- [x] Obtain the owner's post-push approval before M0.

Bootstrap commit: [4549e77](https://github.com/dehghandehnaviamin/GeneWire/commit/4549e772eab116b3ec0c1566ecd33e7ebae630a2).
The owner authorized M0 on 2026-11-26. Social-preview upload remains unverified.

## M0 — Research and Feasibility (published; direction accepted for M1)

| Task | Output | State |
| --- | --- | --- |
| [#1: use cases and boundaries](https://github.com/dehghandehnaviamin/GeneWire/issues/1) | [Regional scenarios and requirements](../research/use-cases.md) | Prepared; domain/deployment assumptions need review |
| [#2: standards comparison](https://github.com/dehghandehnaviamin/GeneWire/issues/2) | [Comparison](../research/standards-comparison.md) and [source register](../research/sources.md) | Desk review prepared; no conformance test |
| [#3: evaluation plan](https://github.com/dehghandehnaviamin/GeneWire/issues/3) | [Synthetic workloads, truth table, faults and metrics](../research/evaluation-plan.md) | Planned experiments; none run |
| [#4: feasibility decision](https://github.com/dehghandehnaviamin/GeneWire/issues/4) | [Conditional reuse-first recommendation](../research/feasibility-decision.md) | Owner authorized advancing the direction into M1; no domain/experimental sign-off |
| Owner technology constraint | [Rust core and Python integration options](../research/technology-direction.md) | Language direction accepted; interfaces/dependencies unselected |

The owner selected regional retrieval/streaming and a Rust core with possible
Python high-level access. Bulk transfer remains a secondary comparison.
The initial review does not establish a need for a new binary wire protocol.

## Remaining M0 review and publication

- [x] Owner authorizes advancing the proposed scope and reuse-first direction into M1.
- [ ] Identify the first analysis consumer and its incomplete-output policy.
- [ ] Obtain a domain review of the tiny truth fixture and intended query semantics.
- [ ] Select actual baseline implementations and a controlled future runner.
- [x] Approve and verify M0 publication at 5e28a6283fed0445b89c09df17c3ec3087a6c5ec.

GitHub issues remain open until published, reviewed evidence meets their acceptance
criteria. M1 is a local design draft; implementation has not started.

## M1 — Design draft

| Output | State |
| --- | --- |
| [RFC 0001](../rfcs/0001-regional-streaming-profile.md) | Proposed first subset and tradeoffs |
| [Profile](../spec/regional-streaming.md) and [lifecycle](../spec/stream-lifecycle.md) | Proposed P01–P18; no replay after block exposure |
| [Rust/Python boundary](../spec/rust-python.md) | Preferred synchronous native interface; no implemented SDK |
| [Security model](../spec/security-model.md) | Proposed controls and residual risks; no audit claim |
| [Conformance plan](../spec/conformance.md) and [30 vectors](../spec/vectors/cases.json) | Scenario expectations only; none executed |
| Updated three architecture/lifecycle diagrams | Proposed M1 subset; no implementation claim |

- [ ] Review the first consumer and provisional-output policy.
- [ ] Review retry, cleanup, outbound policy, budgets and native lifetime choices.
- [ ] Obtain domain review before expanding beyond the narrow synthetic oracle.
- [ ] Qualify real baseline implementations and actual dependency/build versions.
- [ ] Approve and verify later M1 publication.
- [ ] Approve implementation after reviewing the M1 draft.

## Later milestones

M1 requires a reviewed client contract, state model, resource limits and security
analysis. M2–M3 require implementation and fault evidence. M4 requires format and
domain review. M5 requires working contributor and user workflows. M6 requires
release validation. Decompose these into actionable issues when earlier evidence
establishes scope; do not create speculative placeholder issue activity.
