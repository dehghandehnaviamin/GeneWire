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
  compatibility or performance. Python/asyncio is a proposed reference environment.
- **Next gate:** M0 feasibility review, after bootstrap owner approval.

## D004 — Preserve the existing repository identity

- **Date:** 2026-11-26
- **State:** Accepted
- **Decision:** Use the existing public `dehghandehnaviamin/GeneWire` repository,
  its `main` branch and SSH `origin`; do not create a competing lowercase repository.
- **Evidence:** GitHub CLI verified the authenticated owner, public visibility,
  empty remote and expected description before local file creation.
- **Consequence:** All contributor links use the observed canonical repository name.
