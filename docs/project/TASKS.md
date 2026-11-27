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

## M2 — Narrow reference implementation (engineering gate complete)

- [x] Build a Python-independent Rust core and synchronous PyO3 binding.
- [x] Exercise ordered bytes, strict ticket/range/encoding checks and retry admission.
- [x] Exercise cancellation, concurrent reads, deadlines and explicit cleanup.
- [x] Check Python-owned output and retained runtime lifetime.
- [x] Match Q1–Q5 through an external decoder; add invalid-BAM and omission controls.
- [x] Verify local setup, formatting, static checks and Rust/Python suites.
- [x] Run pinned htsget-rs locally on generated BAM/BAI; match Q1–Q5 through
  GeneWire, independent HTSlib htsget retrieval and direct indexed HTSlib.
- [x] Implement bounded ticket retries and exercise admission, exhaustion,
  cancellation, shared deadlines and nonretryable failures locally.
- [x] Expose retained transport phase and partial-output failure flag in Rust/Python.
- [x] Report the configured upstream subset assumption and separate cleanup states.
- [x] Exercise cleanup timeout/retry, panic translation and both sides of the
  committed-handoff cancellation boundary with test-only scheduling hooks.
- [x] Implement supervised full BAM decode/filter with bounded process shutdown,
  provisional staging, existing-file protection and failure-path tests.
- [x] Measure one 64 MiB opaque transfer per caller-retention mode; exercise
  configured-CA TLS, hostname rejection, IPv6 pins and normal interpreter shutdown.
- [x] Inspect and record the current target's resolved Rust feature/license graph.
- [x] Add explicit accepted-payload/output-copy counters, test retained fragment
  extents and mixed large blocks, and check the counters on 64 MiB transfers.
- [x] Exercise abrupt decoder/native-process exit and supervisor SIGINT cleanup.
- [x] Qualify the current counters/failure checks on CI and record their scope;
  allocator/TLS/HTTP/JSON memory and crash recovery remain distinct exclusions.
- [x] Prepare pinned CI workflow with Rust/Python and independent-server checks.
- [x] Publish under D016 approval and verify actual Linux/macOS CI before M2 exit.
- [x] Upgrade the four action pins to Node.js 24; verify a fresh successful
  Linux/macOS run and archive results with no Node.js 20 warnings (D019).

See [M2 evidence/gaps](M2-LOCAL.md) and [working local commands](../development.md).
On 2026-11-27 the owner authorized integrating the prepared history into main and
pushing main. This publication does not complete the remaining M2 evidence gates.

The owner will arrange the final university review and instructed continued
development. External scientific review is deferred, not recorded as completed.

Under D018, [the narrow M2 reference gates passed](CI-VALIDATION.md): both hosted
runners completed 47 Rust and 34 Python/native tests without skips, independent
server/baseline comparisons and resource assertions. Full conformance, allocator/
TLS/HTTP/JSON accounting, hard-crash recovery and wider qualification remain
explicitly outside this exit claim and part of later qualification work.

## M3 — Verified BAM job recovery (local increment; full exit open)

- [x] Define complete-source reuse, query binding, receipt transitions and limits
  in [RFC 0002](../rfcs/0002-recoverable-bam-jobs.md) under the owner's M3 instruction.
- [x] Require an externally trusted digest; discard incomplete input instead of
  appending bytes from a fresh ticket.
- [x] Implement private locked state, synced source/result files and no-overwrite
  publication with post-link crash reconciliation.
- [x] Exercise SIGKILL boundaries, interrupted downloads, corrupt/stale receipts,
  changed/truncated files, lock contention, limits and storage/sync errors.
- [x] Recover Q1–Q5 from verified source without new network requests; preserve
  existing M2 independent-server and resource checks locally.
- [ ] Obtain authorization for M3 remote publication and observe Linux/macOS CI.
- [ ] Qualify broader durable acceptance/storage behavior before full M3 exit;
  byte-offset resume, multi-object recovery and generic analysis effects remain outside this increment.

See [M3 source-bound evidence and exclusions](M3-LOCAL.md).

## Later milestones

M1 requires a reviewed client contract, state model, resource limits and security
analysis. M2–M3 require implementation and fault evidence. M4 requires format and
domain review. M5 requires working contributor and user workflows. M6 requires
release validation. Decompose these into actionable issues when earlier evidence
establishes scope; do not create speculative placeholder issue activity.
