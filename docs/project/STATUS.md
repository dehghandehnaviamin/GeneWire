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
| M0 research | Initial desk review prepared locally | [Research pack](../research/README.md); recommendation proposed; no domain sign-off or experiments |
| Protocol specification | Not started | M0 recommendation and scope need review |
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

The M0 branch is local pending remote-push approval. Public main still contains
the bootstrap. GitHub issues #1–#4 remain open; drafts are not published completion
evidence and have not been presented as accepted decisions.
