# Project status

**Experimental — Pre-alpha — Research and Design**

Snapshot: 2026-11-26. Status must be updated when verified evidence changes.

| Area | State | Evidence or next gate |
| --- | --- | --- |
| Public repository | Created | [GeneWire](https://github.com/dehghandehnaviamin/GeneWire) |
| Branding and community documentation | Published in bootstrap | README, local assets, policies and templates |
| License decision | Approved for bootstrap | Apache-2.0 for original project material; see DECISIONS |
| Bootstrap publication | Verified | [4549e772eab116b3ec0c1566ecd33e7ebae630a2](https://github.com/dehghandehnaviamin/GeneWire/commit/4549e772eab116b3ec0c1566ecd33e7ebae630a2); remote main rechecked before M0 |
| Bootstrap owner review | Approved to proceed to M0 | Owner instructed start after the post-push report, 2026-11-26 |
| Lead use case | Owner selected | Regional retrieval and streaming for analysis tools |
| Technology direction | Owner selected | Rust core; Python can provide high-level integration |
| M0 research | Published; direction accepted for M1 | [5e28a62](https://github.com/dehghandehnaviamin/GeneWire/commit/5e28a6283fed0445b89c09df17c3ec3087a6c5ec); no independent domain sign-off or experiments |
| M1 design | Draft prepared locally | [RFC 0001](../rfcs/0001-regional-streaming-profile.md), [contracts and candidate vectors](../spec/README.md); owner instructed continuation after M0 publication |
| Reference implementation | Not started | No application or protocol source exists |
| Testing and CI | No project test suite or CI | Documentation/link/render checks only; [experiment plan](../research/evaluation-plan.md) is unrun |
| Performance and interoperability | Not measured | No benchmark or compatibility claims |
| Release and security support | No release | No supported version or production readiness |

All diagrams are conceptual, all capabilities are planned or under research, and
all format support is prospective. There are no install instructions because
there is nothing to install. A proposed lifecycle is not a normative protocol.

## Evidence policy

Use `Proposed`, `Under research`, `Planned`, `In development`, `Implemented`, and
`Verified` deliberately. Call a capability verified only when the applicable
checks and their scope are recorded. Distinguish local preparation, a local
commit, remote publication, and deployment; none implies another.

Keep immutable initial-publication evidence outside its own commit to avoid
self-referential commit hashes. The bootstrap SHA above is now known and can be
recorded in this later research update.

M0 was pushed and verified on docs/m0-feasibility. Public main still contains
the bootstrap. M1 is local on docs/m1-regional-profile, based on the published M0
branch, pending review and separate push approval. GitHub issues #1–#4 remain open.
The M1 design is not implemented behavior, a completed security review or
scientific validation.
