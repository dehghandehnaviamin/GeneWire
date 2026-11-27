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
| [#1: use cases and boundaries](https://github.com/dehghandehnaviamin/GeneWire/issues/1) | [Regional scenarios and requirements](../research/use-cases.md) | Closed: document delivered and published; domain/deployment assumptions remain provisional |
| [#2: standards comparison](https://github.com/dehghandehnaviamin/GeneWire/issues/2) | [Comparison](../research/standards-comparison.md) and [source register](../research/sources.md) | Closed: desk comparison delivered; no runtime-conformance claim |
| [#3: evaluation plan](https://github.com/dehghandehnaviamin/GeneWire/issues/3) | [Synthetic workloads, truth table, faults and metrics](../research/evaluation-plan.md) | Closed: plan delivered; tiny oracle later exercised, broader experiments unrun |
| [#4: feasibility decision](https://github.com/dehghandehnaviamin/GeneWire/issues/4) | [Conditional reuse-first recommendation](../research/feasibility-decision.md) | Open: decision published and engineering direction accepted; independent domain feedback outstanding |
| Owner technology constraint | [Rust core and Python integration options](../research/technology-direction.md) | Language direction accepted; initial Tokio/PyO3 choices now recorded in local M2 |

The owner selected regional retrieval/streaming and a Rust core with possible
Python high-level access. Bulk transfer remains a secondary comparison.
The initial review does not establish a need for a new binary wire protocol.

## Remaining M0 review and publication

- [x] Owner authorizes advancing the proposed scope and reuse-first direction into M1.
- [x] Choose a Python/HTSlib evaluation consumer with provisional-output policy.
- [ ] Identify a production consumer beyond the tiny evaluation harness.
- [ ] Obtain a domain review of the tiny truth fixture and intended query semantics.
- [ ] Select actual baseline implementations and a controlled future runner.
- [x] Approve and verify M0 publication at 5e28a6283fed0445b89c09df17c3ec3087a6c5ec.

On 2026-11-27, issues #1–#3 were updated with published evidence and closed as
documentation deliverables; #3 explicitly planned experiments rather than requiring
benchmark execution. Issue #4 remains open for actual domain-review feedback.
The M0 milestone is therefore not marked complete. M1 is the prototype's design
basis; the full contract is not verified. See D013 in the decision register.

## M1 — Design draft

| Output | State |
| --- | --- |
| [RFC 0001](../rfcs/0001-regional-streaming-profile.md) | Proposed first subset and tradeoffs |
| [Profile](../spec/regional-streaming.md) and [lifecycle](../spec/stream-lifecycle.md) | Proposed P01–P18; no replay after block exposure |
| [Rust/Python boundary](../spec/rust-python.md) | Synchronous native interface now partially implemented locally |
| [Security model](../spec/security-model.md) | Proposed controls and residual risks; no audit claim |
| [Conformance plan](../spec/conformance.md) and [30 vectors](../spec/vectors/cases.json) | Design expectations; selected behaviors have separate local executable evidence |
| Updated three architecture/lifecycle diagrams | Design target with partial local components labeled |

- [x] Select evaluation consumer and require transport/decode success before the test oracle gate.
- [ ] Review retry, cleanup, outbound policy, budgets and native lifetime choices.
- [ ] Obtain domain review before expanding beyond the narrow synthetic oracle.
- [ ] Qualify real baseline implementations and actual dependency/build versions.
- [x] Owner authorizes integration and publication of the prepared M1 history on main.
- [x] Owner instructs local continuation and delegates product/business decisions.

## M2 — First local implementation (in progress)

- [x] Build a Python-independent Rust core and synchronous PyO3 binding.
- [x] Exercise ordered bytes, strict ticket/range/encoding checks and retry admission.
- [x] Exercise cancellation, concurrent reads, deadlines and explicit cleanup.
- [x] Check Python-owned output and retained runtime lifetime.
- [x] Match Q1–Q5 through an external decoder; add invalid-BAM and omission controls.
- [x] Verify local setup, formatting, static checks and Rust/Python suites.
- [ ] Run a real independent htsget server and qualify baseline clients.
- [ ] Complete ticket retry/capability, cleanup-timeout, panic and race evidence.
- [ ] Build/review product analysis-process supervision.
- [ ] Measure memory/copies/latency and qualify TLS/IPv6/additional platforms.
- [ ] Configure and exercise CI before claiming M2 exit.

See [M2 evidence/gaps](M2-LOCAL.md) and [working local commands](../development.md).
On 2026-11-27 the owner authorized integrating the prepared history into main and
pushing main. This publication does not complete the remaining M2 evidence gates.

## Later milestones

M1 requires a reviewed client contract, state model, resource limits and security
analysis. M2–M3 require implementation and fault evidence. M4 requires format and
domain review. M5 requires working contributor and user workflows. M6 requires
release validation. Decompose these into actionable issues when earlier evidence
establishes scope; do not create speculative placeholder issue activity.
