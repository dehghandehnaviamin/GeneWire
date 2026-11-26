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

## M0 — Research and Feasibility (drafts prepared)

| Task | Output | State |
| --- | --- | --- |
| [#1: use cases and boundaries](https://github.com/dehghandehnaviamin/GeneWire/issues/1) | [Regional scenarios and requirements](../research/use-cases.md) | Prepared; domain/deployment assumptions need review |
| [#2: standards comparison](https://github.com/dehghandehnaviamin/GeneWire/issues/2) | [Comparison](../research/standards-comparison.md) and [source register](../research/sources.md) | Desk review prepared; no conformance test |
| [#3: evaluation plan](https://github.com/dehghandehnaviamin/GeneWire/issues/3) | [Synthetic workloads, truth table, faults and metrics](../research/evaluation-plan.md) | Planned experiments; none run |
| [#4: feasibility decision](https://github.com/dehghandehnaviamin/GeneWire/issues/4) | [Conditional reuse-first recommendation](../research/feasibility-decision.md) | Proposed, awaiting owner review |
| Owner technology constraint | [Rust core and Python integration options](../research/technology-direction.md) | Language direction accepted; interfaces/dependencies unselected |

The owner selected regional retrieval/streaming and a Rust core with possible
Python high-level access. Bulk transfer remains a secondary comparison.
The initial review does not establish a need for a new binary wire protocol.

## Remaining M0 review and publication

- [ ] Owner reviews the proposed scope and reuse-first recommendation.
- [ ] Identify the first analysis consumer and its incomplete-output policy.
- [ ] Obtain a domain review of the tiny truth fixture and intended query semantics.
- [ ] Select actual baseline implementations and a controlled future runner.
- [ ] Approve and verify publication of the local M0 changes.

GitHub issues remain open until published, reviewed evidence meets their acceptance
criteria. M1 and implementation have not started.

## Later milestones

M1 requires a reviewed state model, wire proposal, resource limits and security
analysis. M2–M3 require implementation and fault evidence. M4 requires format and
domain review. M5 requires working contributor and user workflows. M6 requires
release validation. Decompose these into actionable issues when earlier evidence
establishes scope; do not create speculative placeholder issue activity.
