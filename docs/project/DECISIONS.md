# Decision register

Decisions record rationale and limits, not implementation claims.

## D001 — Bootstrap before research

- **Date:** 2026-11-26
- **State:** Accepted
- **Decision:** Publish a documentation-only open-source bootstrap, verify the
  initial push, and obtain owner approval before research or implementation.
- **Reason:** Preserve the evolution of design decisions in public history.
- **Consequence:** No production source, wire specification, package metadata,
  installation commands, CI claims, or performance results at bootstrap.

## D002 — One license for original project material

- **Date:** 2026-11-26
- **State:** Accepted for bootstrap following owner instruction to continue after
  presentation of the Apache-2.0 recommendation and scope.
- **Decision:** Apache-2.0 applies to original code, protocol specifications,
  documentation, and visual assets. Copyright holder: Amin Dehghan; initial year:
  2026. Third-party material retains its own license and attribution.
- **Alternatives:** MIT is simpler and permissive, but has no explicit patent
  grant. Apache-2.0 expressly addresses contributor patent rights, termination of
  that grant in specified litigation, modification notices and attribution. A
  separate documentation license would add reuse and contribution complexity.
- **Reason:** A common license supports a reusable infrastructure ecosystem and
  avoids splitting original prose, examples, diagrams and future implementations.
- **Limits:** This is not a claim of patent clearance, a standards-body patent
  commitment, or a grant of trademark rights. External specifications are linked,
  not relicensed. Contributor Covenant 2.1 retains its CC-BY-4.0 attribution.
- **Follow-up:** Future package metadata must declare `Apache-2.0`. Revisit a
  separate documentation license only through an explicit, reviewed decision.
- **Sources:** [Apache text](https://www.apache.org/licenses/LICENSE-2.0),
  [MIT text](https://choosealicense.com/licenses/mit/),
  [Covenant license](https://github.com/EthicalSource/contributor_covenant/blob/91532d80ea5f39b6685aff4892bc6854bf2f6d6f/LICENSE.md).

## D003 — Conceptual architecture, open transport choice

- **Date:** 2026-11-26
- **State:** Proposed
- **Direction:** Separate session control, bounded transfer, integrity/checkpoint
  persistence, optional format adapters, and transport integration.
- **Open questions:** Existing-standard extension versus a new protocol; transport;
  framing; identifiers; integrity granularity; authentication/authorization;
  durable acceptance; reference and coordinate semantics.
- **Limits:** Diagrams do not assign wire fields, algorithms, normative behavior,
  compatibility or performance. The original Python/asyncio core direction is
  superseded by the owner's Rust/Python direction in D007.
- **Next gate:** Review [RFC 0001](../rfcs/0001-regional-streaming-profile.md).
  M1 diagrams replace the bootstrap model with a proposed regional-access subset.

## D004 — Preserve the existing repository identity

- **Date:** 2026-11-26
- **State:** Accepted
- **Decision:** Use the existing public `dehghandehnaviamin/GeneWire` repository,
  its `main` branch and SSH `origin`; do not create a competing lowercase repository.
- **Evidence:** GitHub CLI verified the authenticated owner, public visibility,
  empty remote and expected description before local file creation.
- **Consequence:** All contributor links use the observed canonical repository name.

## D005 — Bootstrap approved; regional access leads M0

- **Date:** 2026-11-26
- **State:** Accepted owner direction
- **Evidence:** After the verified-push report and next-step explanation, the owner
  instructed start and selected regional retrieval/streaming for analysis tools.
- **Decision:** Begin M0 around that scenario. Keep bulk-object exchange secondary.
- **Limits:** This authorizes research, not implementation or later remote pushes.
  The current public bootstrap commit is 4549e772eab116b3ec0c1566ecd33e7ebae630a2.
- **Outputs:** [Research pack](../research/README.md).

## D006 — Reuse existing regional access before defining new wire behavior

- **Date:** 2026-11-26
- **State:** Owner accepted advancing this direction into M1; independent domain review outstanding
- **Recommendation:** Conditional go for a reuse-first M1 design review. Compare
  existing regional mechanisms and clients before proposing a new binary protocol.
- **Evidence:** [Primary-source comparison](../research/standards-comparison.md),
  [requirements](../research/use-cases.md), and [evaluation plan](../research/evaluation-plan.md).
- **Limits:** No conformance, throughput, demand or production-feasibility result.
  No claim that the candidate integration gap is novel or unsolved.
- **Alternatives and stopping conditions:** [Feasibility recommendation](../research/feasibility-decision.md).

## D007 — Rust core with possible Python high-level access

- **Date:** 2026-11-26
- **State:** Accepted owner technology direction
- **Decision:** Pursue Rust for the performance-sensitive core. Python can provide
  a convenient high-level interface and analysis/workflow integration.
- **Supersedes:** The bootstrap's proposed Python/asyncio reference core; it does
  not supersede the principle of protocol interoperability.
- **Limits:** Responsibilities are a proposed split; runtime, format libraries,
  binding, package layout and support matrix remain unselected. No speedup,
  zero-copy behavior or memory-safety guarantee is inferred from language alone.
- **Follow-up:** Evaluate native bindings versus a process boundary and measure
  core-only and end-to-end overhead. See [technology direction](../research/technology-direction.md).

## D008 — M0 publication verified; proceed to M1 design

- **Date:** 2026-11-26
- **State:** Accepted owner direction
- **Evidence:** Owner approved publishing M0; Git/CLI verified branch
  docs/m0-feasibility at 5e28a6283fed0445b89c09df17c3ec3087a6c5ec and all 43 file
  hashes. After the publication report, the owner instructed continuation.
- **Decision:** Develop the reuse-first regional-access architecture and
  specification draft with Rust/Python boundaries. Do not infer scientific
  sign-off, implementation approval or permission for subsequent pushes.
- **Outstanding:** Domain review, actual baseline runs and M1 draft review.

## D009 — Narrow htsget client subset and explicit incomplete results

- **Date:** 2026-11-26
- **State:** Adopted as direction for local evaluation under D010; partial implementation
- **Proposal:** One mapped-read interval/BAM over existing htsget behavior;
  bounded encoded-byte streaming; separate transport/analysis/oracle outcomes;
  retry a block only before any of its output is exposed.
- **Technology preference:** Tokio Rust core; synchronous PyO3 binding and
  maturin packaging candidate. Versions, build features and support remain M2 work.
- **Tradeoff:** Conservative failure/restart behavior rather than ambiguous
  transparent replay; no persistent checkpoint or new wire format in P0.
- **Evidence and tests:** [RFC](../rfcs/0001-regional-streaming-profile.md),
  [lifecycle](../spec/stream-lifecycle.md), [conformance plan](../spec/conformance.md).

## D010 — Local implementation and delegated product decisions

- **Date:** 2026-11-26
- **State:** Accepted owner instruction
- **Evidence:** After the M1 report, the owner instructed continuing locally and
  explicitly delegated business/product decisions to the agent.
- **Decision:** Start the narrow M2 local prototype from RFC 0001. Retain the
  regional/BAM focus and Rust/Python stack; record technical tradeoffs and evidence.
- **Publication:** No subsequent remote push, merge, issue update, release or
  deployment is included. Keep existing public history and remotes unchanged.
- **Limits:** The instruction does not supply independent domain/security review
  or measured performance. M2 exit remains governed by observed evidence.

## D011 — Pull-based prototype with explicit destination pins

- **Date:** 2026-11-26
- **State:** Implemented locally; broader qualification pending
- **Decision:** Use a synchronous pull reader over Tokio/reqwest, with an overall
  watchdog, owned outputs and explicit close. No producer queue/prefetch in the
  first increment. Use operator-supplied IP pins without ambient DNS so address
  policy binds to actual connections without an unowned blocking DNS lookup.
- **Tradeoffs:** HTTP/1 only; per-hop HTTP client; cross-origin redirects rejected;
  ticket retries initially deferred (implemented in D014); product analysis
  supervision still deferred. Reject an HTTP body
  fragment above 256 KiB. No performance or complete resource-bound claim.
- **Evidence:** [M2 ledger](M2-LOCAL.md), Rust HTTP/fault tests, Python/native and
  synthetic BAM checks. This does not establish real-server interoperability.

## D012 — Integrate and publish the prepared history on main

- **Date:** 2026-11-27
- **State:** Accepted owner instruction; history integrated locally
- **Evidence:** The owner explicitly requested merging all prepared branches into
  main and pushing. Before integration, origin/main was refreshed and found to
  include M0 through PR #5, merge 4f765fc.
- **Action:** Fast-forward local main to origin/main, then merge
  feat/local-regional-stream through 8c8b132 with a merge commit e9be690. The M0
  and M1 branches are ancestors of the integrated history; no rewrite or branch
  deletion is needed.
- **Checks:** All 28 Rust and 12 Python/native tests passed before integration.
  The merged source tree exactly matches the tested prototype. Publication
  metadata updates do not change runtime behavior.
- **Scope:** Push main, verify its exact GitHub head and inspect Actions state.
  Preserve all source commits, existing branches and remotes. No release,
  deployment, issue closure or claim of M2 completion is included.

## D013 — Reconcile M0 issue states with published deliverables

- **Date:** 2026-11-27
- **Trigger:** The owner asked whether issues needed updating after publication;
  routine project decisions had already been delegated.
- **Decision:** Close #1–#3 as completed document-delivery tasks, retaining their
  original acceptance criteria and linking immutable published evidence at
  bb6eba53e832ce030e8b9911fe02670a58f8cfb8. #3 required an evaluation plan, not
  execution of the full benchmark matrix.
- **Outstanding:** Keep #4 open because actual independent domain-review feedback
  and resulting changes/dissent have not been recorded. The owner-authorized
  conditional engineering direction does not supply that review.
- **Verification:** GitHub returned closed/completed for #1–#3 and open for #4;
  issue bodies now distinguish completed documents, later tiny-fixture checks
  and unqualified M2 work. Labels, assignees and milestones were preserved.
- **Limits:** This updates the publication/project record; it does not complete
  M0's remaining review, M2, a real-server evaluation, security audit or release.

## D014 — Continue M2 with bounded ticket retries and explicit failure context

- **Date:** 2026-11-27
- **Trigger:** The owner instructed starting M2; the existing partial prototype
  and remaining gates were inspected before continuing local implementation.
- **Decision:** Retry unaccepted ticket GETs for selected transient transport
  failures and 429/500/502/503/504, with three total attempts independent of each
  block's attempt budget. One ticket-phase deadline covers all attempts and waits;
  overall deadline and cancellation also interrupt them. Reapply destination and
  credential policy on every attempt. Discard an incomplete unaccepted ticket.
- **Failure policy:** Authorization, policy, JSON, encoding, resource and declared
  length failures remain terminal. Connection/TLS setup remains conservatively
  nonretryable. Release unsuccessful responses before retry waits. An excessive
  Retry-After cannot overflow the timer or cause an earlier retry.
- **Reporting:** Retain the active phase on terminal outcomes. Set
  `may_have_partial_output` only when an unsuccessful query has exposed bytes.
  Count retries admitted after completed waits; interrupted waits add no retry.
  Preserve terminal report fields across later cancel/close calls.
- **Evidence:** [M2 ledger](M2-LOCAL.md); 38 Rust and 14 Python/native tests passed,
  including new retry/deadline/cancellation/report cases. Clippy and formatting
  passed. No real-server, full race/panic/cleanup or performance qualification.
- **Publication:** Local work only; the earlier D012 authorization covered the
  then-prepared history. No new push, issue update, release or deployment.

## D015 — Continue engineering; defer scientific review to the university

- **Date:** 2026-11-27
- **Owner instruction:** Continue development; the owner will arrange the final
  university review. This does not supply independent scientific findings,
  publication authorization or release approval.
- **Analysis boundary:** Implement an optional POSIX Python supervisor using a
  separate mature pysam/HTSlib decoder. Fully decode and apply the explicit mapped
  read-overlap filter for the original query. Bound the input queue, output,
  diagnostic bytes and child shutdown. Stage output beside the destination and
  create the final name only after transport, decoder and owned cleanup succeed.
  Refuse existing files. Do not claim arbitrary downstream rollback or clinical
  correctness. `analysis` is an optional dependency extra, not required for bytes.
- **Core lifecycle:** Expose NotStarted/InProgress/Complete/Failed cleanup and a
  separate sanitized cleanup error. Serialize competing closes under a finite
  wait; keep admission occupied after a cleanup timeout until a later successful
  close. Test panic translation and both handoff/cancel orderings using hooks
  compiled only into Rust unit tests, with no public injection interface.
- **Configured capability:** Report HtsgetBamRegional with Configured evidence;
  no service-info discovery, version inference or conformance claim. Reject an
  unsupported Python profile before network access.
- **TLS:** Permit one bounded operator-supplied PEM trust anchor in addition to
  platform roots. Validate it before query admission; retain hostname/certificate
  verification. No ticket may choose a root. Positive local CA and wrong-name
  negative controls exercise the distinction.
- **Resource finding:** The initial 64 MiB opaque probe failed the prototype's
  256 KiB HTTP-fragment restriction. Public reads remain ≤256 KiB; library body
  fragments may now use the remaining draft 2 MiB window after reserving inline
  bytes and one read copy. Release empty retained Bytes storage before polling
  again. Oversized fragments still fail; this is not certified RSS accounting.
- **Independent evaluation:** Pin MIT-licensed htsget-rs source at
  `2a91e661e6a287e3adf30e65c26a8f47697f3548`, no default features, local generated
  BAM/BAI only. Q1–Q5 matched through GeneWire, independent HTSlib htsget retrieval
  and direct indexed HTSlib. Service-info and CLI version strings differ and are
  retained as observed in the [raw report](evidence/2026-11-27-interop.json).
- **Evidence:** 45 Rust and 31 Python/native tests passed without skips on this
  macOS runner. Normal interpreter exit, IPv6 loopback and TLS controls passed.
  [Resource probe](evidence/2026-11-27-resources.json) records one 64 MiB transfer
  in each caller-retention mode, source hashes and method limits. No ranking.
  [Dependency metadata](evidence/2026-11-27-dependencies.json) records 128 resolved
  packages' effective features and declared licenses on the current target;
  this is not a vulnerability scan or distribution-compliance attestation.
- **CI/publication:** Prepare an immutable-action-pinned Linux/macOS workflow.
  Local commands and YAML parsing are checked; no GitHub run or new push occurred.
  M2 remains in progress until its remaining qualification and CI gates pass.

## D016 — Authorize the M2 follow-up, publication and CI verification

- **Date:** 2026-11-27
- **Owner approval:** After the proposed next steps (native/Python resource and
  copy accounting, abrupt process/timeout/cleanup tests, then commit/push and
  Linux/macOS CI), the owner explicitly instructed proceeding and approved them.
- **Scope:** Preserve the prepared M2 work and history, complete those checks,
  commit and push main without rewriting history, fix failures exposed by CI,
  and publish the accompanying evidence/status updates. Follow CI to its terminal
  result; local checks alone are not evidence of a passing remote workflow.
- **Limits:** No release/deployment or scientific sign-off is implied. Continue
  the narrow synthetic BAM subset; record any remaining unsupported failure or
  resource behavior honestly. University review remains the owner's later step.

## D017 — Account for accepted payload/copies and extend process-failure checks

- **Date:** 2026-11-27; execution under D016.
- **Decision:** Expose a nested MemoryReport through Rust/Python. Count retained
  inline bytes and each pending fragment's original accepted extent, including
  empty Bytes views; account for a Rust output Vec until handoff. Track current
  and peak accepted payload, largest observed HTTP fragment, bytes copied into
  Rust read results, and bytes copied into Python-owned outputs.
- **Scope:** These are logical data-plane extents and named copy operations, not
  allocator-capacity/TLS/HTTP/JSON accounting or a process-memory cap. Caller
  retention and bridge copies are additional to native retained payload. Counts
  can change during cleanup/handoff; compare them after exhaustion/close.
- **Checks:** A sliced-buffer unit test retains the original allocation extent;
  a mixed million-byte inline/HTTP/inline test preserves order and the accepted
  payload budget. The 64 MiB probe checks zero retained payload after close,
  accepted payload peak ≤2 MiB and exactly 64 MiB counted at each output-copy
  boundary. RSS/tracemalloc and limitations remain recorded separately.
- **Process lifetime:** Add actual decoder SIGKILL, supervisor SIGINT and native
  process os._exit checks. Interruption reaps the owned child, cancels native I/O
  and removes staging; abrupt native process exit returns promptly. A hard-killed
  supervisor cannot run finalizers or promise removal of its staging files or
  daemonized descendants; crash recovery remains outside this P0 contract.
- **Observed locally:** 47 Rust and 34 Python/native tests passed without skips,
  clippy/formatting passed, independent-server cases still matched. CI will retain
  synthetic source-bound JSON artifacts for verification on each runner.
- **Evidence chronology:** Reports from D015 are anchored to prepared commit
  f4d886692f8b4c32f4803ef8556b164db2ea1060. Follow-up reports contain the new
  source hashes. Neither report set implies that a different revision was tested.

## D018 — Record the narrow M2 engineering exit from actual CI evidence

- **Date:** 2026-11-27; execution under D016 and delegated engineering decisions.
- **Observed:** Published implementation da92bc9a1d56b51bed7f7035e980c71da026b424
  passed GitHub Actions run 45995255517. Ubuntu 26.04.1 x86_64 and macOS 26.7.2
  arm64 each passed 47 Rust and 34 Python/native tests without skips, static/build
  checks, independently built htsget-rs/HTSlib Q1–Q5 and both resource modes.
- **Verification:** Downloaded JSON artifacts matched the published implementation
  file hashes. Expected/observed/indexed/htsget-baseline record sets agreed.
  Both copy counters equaled each 64 MiB result; accepted payload peaks were
  within 2 MiB and zero remained after close. Archive identities, test counts,
  normalized raw reports and method limits are retained in [CI evidence](CI-VALIDATION.md).
- **Exit decision:** The [minimum M2 reference gates](CI-VALIDATION.md#m2-exit-scope)
  are met for the implemented single-region BAM subset. This closes the narrow
  engineering prototype milestone, not every provisional M1 requirement/vector
  or general native allocation/security/platform qualification. Preserve those
  limits explicitly; do not recast logical payload counts as a process-memory cap.
- **Remaining phases:** Durable/crash recovery remains M3; expanded genomic
  semantics require later review; packaging/release, comparative benchmarks and
  security qualification remain later work. No M3 implementation, release or
  deployment is included in this publication. University review remains pending.
- **Final publication:** Publish the evidence/status documentation with all
  implementation/build/workflow inputs byte-identical to da92bc9. Use a CI-skip
  marker only for that documentation update; its evidence points to the actual
  successful run rather than inventing a new successful check for the final SHA.

## D019 — Migrate CI actions to their declared Node.js 24 runtime

- **Date:** 2026-11-27, under the owner's explicit continuation and CI-fix approval.
- **Trigger:** The owner supplied two Node.js 20 deprecation warnings from run
  45995255517 and one hosted macOS arm64 capacity notice.
- **Decision:** Upgrade checkout v7.0.1, setup-python v7.1.0, upload-artifact
  v7.0.2 and setup-uv v10.4.0. Resolve official release tags to commit SHAs and
  verify `runs.using: node24` at each pinned commit. Preserve the existing
  toolchain/interpreter/uv versions, permissions and arm64 coverage. Explicitly
  keep ZIP archival enabled for the two synthetic report files.
- **Sources:** [Verified action metadata](CI-VALIDATION.md#action-runtime-maintenance)
  and [GitHub migration guidance](https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/).
- **Capacity notice:** Queue scheduling belongs to hosted infrastructure; keeping
  the observed arm64 target is preferable to changing the qualification matrix
  merely to suppress a notice. No runner-capacity or queue-time guarantee is made.
- **Publication chronology:** The previous final documentation commit did not
  execute because automatic approval review hit a usage limit, not because its
  action was classified unsafe. After the owner requested continuation, that
  reviewed evidence was preserved at 6e433d3. Publish it with this CI fix and
  observe a fresh complete run; D018's proposed docs-only CI skip is superseded
  because this update changes the workflow.
- **Verification:** YAML/input/runtime metadata checked before push. Record actual
  run results and annotation counts after execution; do not infer their absence
  from a local configuration change.
- **Observed outcome:** dc46c2b8eb045149de396f439f6e4c445cf6ceba passed run
  46021619658 on Ubuntu and macOS. Each passed 47 Rust and 34 Python/native tests
  without skips, independent-server Q1–Q5 and both 64 MiB resource modes.
  Downloaded report hashes matched the tested source; normalized reports and
  workflow hash are [archived](evidence/ci-46021619658/summary.json).
  Both jobs have zero warning annotations; Ubuntu has no annotations and macOS
  retains only the hosted-capacity notice. Logs contain no Node.js 20 warning.
- **Evidence publication:** The final update changes only documentation and
  synthetic evidence. Verify all implementation/build/workflow inputs remain
  byte-identical to dc46c2b and use a docs-only CI skip. Attribute successful CI
  to the tested revision; do not imply another run for the evidence commit.

## D020 — Start local M3 with verified complete-source BAM job recovery

- **Date:** 2026-11-27. After the M3 proposal, the owner instructed proceeding.
- **Authorization:** Local design, implementation and tests. Preserve previous
  work; the earlier M2 push/CI approval does not authorize an unrelated M3 push,
  release or deployment. University review remains deferred to the owner.
- **Decision:** Adopt [RFC 0002](../rfcs/0002-recoverable-bam-jobs.md) for the first
  recovery subset. The existing htsget stream lacks a safe authenticated offset
  resume contract. Restart incomplete input; reuse only a complete synced source
  matching an externally trusted expected SHA-256. Do not join fresh-ticket bytes
  to old bytes or pretend a checksum establishes scientific completeness.
- **Implementation:** A Python job wrapper retains mode-0600 files in a private
  sibling workspace, holds a nonblocking advisory lock and atomically records
  Downloading/Verified/Ready/Committed receipts. Reuse the existing supervised
  decoder. A synced result is published by no-overwrite hard link; the retained
  result inode reconciles a crash after publication but before the final receipt.
- **Failure policy:** Corruption, unknown/stale state, wrong query/destination or
  limits and unrelated output fail closed. A failed post-link sync reports the
  recognized publication separately from unconfirmed sync completion. Never
  signal a stored PID or fabricate a recovered network transport report.
- **Evidence:** [M3 ledger](M3-LOCAL.md) records local source-bound process/storage
  checks and regression results. This is a first local M3 increment, not full M3
  exit, power-loss qualification, byte-offset resume, a stable API or scientific
  approval. Sync confirmation means successful fsync calls on the observed host.

## D021 — Publish the prepared M3 increment and observe cross-platform CI

- **Date:** 2026-11-27. After reviewing the local result and commit a32062f,
  the owner explicitly approved the requested push and Linux/macOS CI run.
- **Scope:** Publish the prepared M3 job subset, run its recovery fault harness
  alongside the full Rust/Python and independent-server/resource checks, fix
  failures exposed by CI and publish accompanying evidence/status updates.
  Preserve immutable action pins and existing evaluation versions.
- **Evidence:** Retain source-bound recovery JSON alongside interoperability and
  resource artifacts. Inspect actual terminal jobs, test outcomes, artifact
  source hashes and annotations before claiming cross-platform qualification.
- **Limits:** This approval does not close the full M3 milestone or authorize
  release/deployment, power-loss claims, broader APIs or scientific sign-off.
- **First CI observation:** Run 46034485690 failed on macOS before the M3 tests:
  `ticket_phase_budget_does_not_restart_after_a_retry` observed zero retries when
  the old 300 ms total deadline expired before its delayed first response could
  admit a retry. This is a pre-existing wall-clock fixture with only 100 ms
  admission headroom, not evidence of a recovery failure.
- **CI fix:** Preserve the shared-phase deadline behavior. Give the fixture a
  five-second phase budget, two-second initial transient response and four-second
  successful retry. Each response fits an incorrectly reset per-attempt budget,
  while their six-second total must fail the correct shared deadline. This widens
  initial scheduling headroom and strengthens the negative control without
  changing production timeouts or removing the retry-count assertions.
- **Observed final result:** 87732e7c41dde4cdda181d7807a1b80f869ba576 passed
  run 46035043779 on Ubuntu x86_64 and macOS arm64. Each passed 47 Rust and
  53 Python/native tests without skips, then repeated the 19-case recovery subset
  for evidence. The eight SIGKILL boundaries, recovered Q1–Q5 and existing
  independent-server/resource gates passed. Source-checked reports, annotations
  and initial failure chronology are [archived](evidence/ci-46035043779/summary.json).
  No warning annotations remain; only the hosted macOS capacity notice persists.
- **Qualification/publication:** The first RFC 0002 job subset has observed
  cross-platform evidence; full M3 remains open. Publish the final documentation
  and evidence with a docs-only CI skip after verifying implementation/build/
  workflow inputs are unchanged from 87732e7. Attribute success to that actual
  run, not an unrun documentation revision. No release/deployment is included.

## D022 — Continue stability engineering; make external review optional

- **Date:** 2026-11-27. The owner clarified that external scientific review belongs
  to an optional side task after a complete stable version. It is not required
  for development, milestone progression or release, and should not be repeated
  in routine progress/final reports. This supersedes earlier review-gate wording.
- **Engineering policy:** Keep correctness expectations, negative controls and
  independent executable comparisons. Removing an institutional review gate does
  not supply evidence for an untested format, guarantee or performance claim.
- **Next M3 increment:** Add explicit cancellation through download, spool
  verification and supervised decoding, with a serialized output-publication
  boundary. Preserve valid receipts for a later fresh invocation; never delete a
  published result merely because a later cancellation arrives. Exercise actual
  native I/O interruption, stalled decoder cleanup and both sides of publication.

## D023 — Add cooperative BAM job cancellation with publication admission

- **Date:** 2026-11-27; continued M3 job-lifecycle engineering under the owner's
  latest continuation instruction, following the existing M3 validation workflow.
- **API:** Export a one-way thread-safe Cancellation token; accept it optionally
  in filter_bam/recover_bam. Signal a subscribed native stream to interrupt blocked
  I/O, check bounded file hashing and poll both supervisor pipe traffic and the
  final child wait. Unsubscribe completed operations so a token does not retain
  native streams. Invalid token types fail before changing a stream/workspace.
- **Publication:** Serialize token cancellation with no-overwrite link admission.
  Cancellation before admission prevents output; after admission, finish the
  accepted result's sync/receipt path. A late signal cannot retract published
  bytes. Filesystem/kernel blocking still has no hard termination guarantee.
- **Recovery:** Cancelled attempts retain their last valid receipt. A fresh token
  restarts incomplete input or reuses verified source/result, preserving existing
  budgets and preventing cross-query byte-offset splicing.
- **Evidence:** Exercise real blocked native I/O, hashing and stalled/reaped
  workers, a pipe-closed/live child, both sides of publication, subscription
  lifetime and subsequent recovery. Record local/CI results separately in the
  M3 ledger. No new format, release or deployment is included.
- **Cleanup result:** Expose RecoveryReport.cleanup_complete separately from
  Cancelled and publication/sync state. A network stream can already be clean
  while supervisor cleanup is incomplete; preserve that distinction in the job
  result instead of implying cancellation synchronously stopped all resources.
- **Observed locally:** 65 Python/native tests and the repeated 31-case
  recovery/cancellation harness passed without skips. Independent htsget-rs and
  HTSlib Q1–Q5 still matched. Follow this M3 lifecycle increment through the
  established publication/CI workflow and archive the actual runner results.
