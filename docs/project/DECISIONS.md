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
  ticket retries and product analysis supervision deferred. Reject an HTTP body
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
