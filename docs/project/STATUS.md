# Project status

**Experimental — Pre-alpha — Research and Design**

Snapshot: 2026-11-27. Status must be updated when verified evidence changes.

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
| M1 design | Direction adopted for local prototype | [RFC 0001](../rfcs/0001-regional-streaming-profile.md); complete contract remains provisional |
| M2 reference implementation | First local increment works; milestone in progress | Rust/Tokio byte reader and synchronous PyO3/Python binding; [evidence and gaps](M2-LOCAL.md) |
| Testing and CI | Local suites exist; no CI | 28 Rust and 12 Python/native tests passed; no tests skipped on this runner |
| Scientific evaluation | Tiny controlled oracle exercised | Q1–Q5 plus invalid-BAM/omission controls; no independent domain sign-off |
| Performance and interoperability | Still unqualified | No measured performance comparison or independent real-server run |
| Release and security support | No release | No supported version or production readiness |

Diagrams show the design target and partial local components. Only the behavior
in the M2 ledger has evidence; broader format support remains prospective.
[Local setup and checks](../development.md) work in the recorded environment.
A proposed lifecycle is not a stable protocol or complete implementation claim.

## Evidence policy

Use `Proposed`, `Under research`, `Planned`, `In development`, `Implemented`, and
`Verified` deliberately. Call a capability verified only when the applicable
checks and their scope are recorded. Distinguish local preparation, a local
commit, remote publication, and deployment; none implies another.

Keep immutable initial-publication evidence outside its own commit to avoid
self-referential commit hashes. The bootstrap SHA above is now known and can be
recorded in this later research update.

M0 was pushed and verified on docs/m0-feasibility. M1 was committed locally at
b684087fb3da50b69dd8fdd209858068eab350a2. Current work continues locally on
feat/local-regional-stream. The owner requested local work and delegated
product/business decisions; no new push, merge or issue closure was performed.
Public main was last verified at the bootstrap, not refreshed during this local
increment. M2 is not complete, independently audited or production-qualified.
