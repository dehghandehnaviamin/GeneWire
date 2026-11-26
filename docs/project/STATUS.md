# Project status

**Experimental — Pre-alpha — Research and Design**

Snapshot: 2026-11-26. Status must be updated when verified evidence changes.

| Area | State | Evidence or next gate |
| --- | --- | --- |
| Public repository | Created | [GeneWire](https://github.com/dehghandehnaviamin/GeneWire) |
| Branding and community documentation | Prepared | README, local assets, policies and templates in this tree |
| License decision | Approved for bootstrap | Apache-2.0 for original project material; see DECISIONS |
| Bootstrap publication | Awaiting initial push verification | Confirm the initial commit on the remote; record evidence after publication |
| Bootstrap owner review | Awaiting approval | Required after the verified initial push |
| M0 research | Not started | Blocked on bootstrap owner approval |
| Protocol specification | Not started | Requires M0 feasibility decision |
| Reference implementation | Not started | No application or protocol source exists |
| Testing and CI | Not configured | Bootstrap uses manual documentation/asset checks |
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
self-referential commit hashes. The owner-facing bootstrap report will identify
the verified SHA. This file records the pre-publication snapshot until a later
authorized update.
