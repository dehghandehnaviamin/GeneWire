# Project status

**Experimental — Pre-alpha — Narrow M2 reference gate complete; local M3 in development**

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
| M2 reference implementation | Narrow engineering gate complete | Rust/Python byte reader and supervised BAM adapter; [exit evidence and limits](CI-VALIDATION.md) |
| M3 recovery | Local verified-BAM-job increment | [RFC 0002](../rfcs/0002-recoverable-bam-jobs.md) and [local evidence](M3-LOCAL.md); complete-source reuse and publication receipts, full M3 exit open |
| Testing and CI | Verified on the observed Linux/macOS runners with Node.js 24 actions | Each passed 47 Rust and 34 Python/native tests without skips; [workflow 46021619658](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46021619658); no warning annotations, one macOS capacity notice |
| Scientific evaluation | Tiny controlled oracle exercised; university review deferred | Q1–Q5 and negative controls; owner will arrange final review, no independent sign-off yet |
| Performance and interoperability | Narrow local evidence | Pinned real htsget-rs and two HTSlib paths matched Q1–Q5; one 64 MiB opaque resource probe per retention mode; no ranking or full resource certification |
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

M0 was published and then merged into GitHub main through PR #5 at 4f765fc.
On 2026-11-27 the owner explicitly requested integrating all prepared branches
into main and pushing main. M1 b684087 and the local M2 history through 8c8b132
are now integrated on main at merge commit e9be690. Original commits and branches
are retained. The integrated source tree matches the tested prototype; the
remaining changes record publication authorization and integration status.

The main publication was verified at bb6eba53e832ce030e8b9911fe02670a58f8cfb8:
all 70 file hashes matched the local tree, and no Actions workflow/run existed.
On 2026-11-27, the owner raised issue maintenance; #1–#3 were reconciled and closed
as published documentation deliverables. #4 remains open for independent domain
feedback. See D013 and the task register for the scope of those closures.
No release or deployment is included. That publication did not supply real-server
or performance evidence; later local evidence is distinguished below.

The owner's subsequent M2 instruction continued local development under D014.
Ticket retries and richer failure reports have local executable evidence; these
changes are not part of the previously verified remote publication.

Under D015 the owner instructed continued development and will arrange the final
university review. The local tree now includes the supervised BAM path,
failure/race/cleanup tests, configured CA/TLS and IPv6 checks, independently run
htsget-rs/HTSlib comparison and source-bound resource reports. CI is prepared
locally but has no verified remote run. Full memory/copy/dependency qualification
and further failure/lifetime variants remain. M2 and scientific review are not
marked complete; no new push, release or deployment occurred.

The [university review handoff](UNIVERSITY-REVIEW.md) identifies the current
demonstration, original truth cases, reproducible evidence and review questions.

D016 authorizes publishing the prepared M2 work and necessary follow-up fixes.
D017 adds explicit accepted-payload/output-copy counters and actual process
failure checks. The initial implementation is preserved at f4d8866. Publication
and CI results will be appended when observed; no release/deployment is included.

**D018 verified update:** f4d8866 and da92bc9 were pushed to main. The complete
Linux/macOS workflow for da92bc9 succeeded; downloaded artifacts matched its
source hashes, tiny truth and payload/copy gates. The narrow M2 reference exit
is complete, with the [scope and permanent raw evidence](CI-VALIDATION.md)
recorded. Earlier pending/local-only statements above describe their respective
snapshots. M3–M6 remain planned and university review remains pending. No software
release or deployment has occurred.

**D019 verified update:** dc46c2b upgrades the four action pins to declared
Node.js 24 runtimes. Fresh run 46021619658 succeeded on both runners with the same
test counts, source-checked Q1–Q5 and resource gates. The Node.js 20 warnings are
absent; the macOS hosted-capacity notice remains. The final evidence-only update
does not change the tested implementation or workflow; no later milestone starts.

**D020 local M3 update:** The owner's subsequent instruction starts the recovery
increment in RFC 0002. The local tree now contains private locked receipts,
SHA-256-pinned full input spools and recoverable no-overwrite result publication.
Local Python/native and Rust suites plus process/storage fault evidence are
recorded in the M3 ledger. The earlier CI result qualifies its historical M2
revision; this new increment has not been pushed or observed in remote CI.
Full M3, power-loss durability and scientific review remain open.
