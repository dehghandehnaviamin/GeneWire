# Project status

**Experimental — Pre-alpha — BAM job subset qualified; milestone replanning needed**

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
| M3 recovery | First verified-BAM-job subset published and CI-checked | [RFC 0002](../rfcs/0002-recoverable-bam-jobs.md) and [evidence](M3-LOCAL.md); complete-source reuse and publication receipts, full M3 exit open |
| M3 workspace/storage follow-up | Published and checked on observed Linux/macOS runners | Existing-job inspection, accepted-output recovery, recoverable source release and expanded BAM truth; [contract evidence](M3-LOCAL.md#admission-accepted-result-and-contract-qualification) |
| Testing and CI | Verified on the observed Linux/macOS runners with Node.js 24 actions | Each passed 47 Rust and 88 Python/native tests without skips, plus a repeated 54-case job harness; [workflow 46072529338](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46072529338); no warning annotations, one macOS capacity notice |
| Correctness evaluation | Controlled oracles and negative controls exercised | Q1–Q5 and B01–B16 span/flag/multiplicity/field cases, independent indexed HTSlib paths and source-bound failure evidence; broader formats/query shapes remain undefined |
| Next engineering boundary | Current concrete RFC 0002 backlog complete; full M3 and M4–M6 still open | [Contract review and milestone-definition inputs](CONTRACT-REVIEW.md#where-autonomous-execution-stops-for-replanning); no automatic release or new protocol claim |
| Performance and interoperability | Narrow local evidence | Pinned real htsget-rs and two HTSlib paths matched Q1–Q5; one 64 MiB opaque resource probe per retention mode; no ranking or full resource certification |
| Release and security support | No release | No supported version or production readiness |

Diagrams show the design target and partial local components. Only the behavior
in the M2/M3 ledgers has evidence; broader format support remains prospective.
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

**D021 verified M3 publication:** a32062f, a06ccc2 and the retry-test fixture fix
87732e7 are published on main. The fresh workflow for 87732e7 succeeded on both
observed runners. Recovery, independent-server and resource JSON matched its
source hashes and are [archived](CI-VALIDATION.md#m3-verified-source-bam-jobs).
The first failed macOS run is preserved as a separate observation. This closes
publication/CI qualification of the first job subset, not full M3, broader
platform qualification, scientific review or release approval.

**D022 current workflow:** The owner moved external scientific review to an
optional post-stable side task. It is not a milestone, development or release
prerequisite. Earlier references above are historical snapshots; the current
engineering gates are executable correctness, failure handling, interoperability
and stability. Routine reports should focus on those gates.

**D023 continuation:** The current M3 job-lifecycle increment adds explicit
Cancellation tokens, native-read interruption, cancellable hashing/supervision
and a serialized output-publication boundary. Local evidence and subsequent CI
qualification are tracked in the M3 ledger; the 87732e7 run remains historical
evidence for the preceding version.

**D023 verified continuation:** 7f15c77 is published on main and passed the fresh
Linux/macOS run 46039605642. The cancellation/publication/cleanup cases and
existing recovery, independent-server and resource gates passed. Source-bound
reports are [archived](CI-VALIDATION.md#m3-cooperative-cancellation). The final
evidence update preserves the tested implementation and workflow; full M3 remains
open for its separately listed engineering gates.

**D024 local follow-up:** Existing-workspace inspection and explicit safe source
release are implemented with Releasing/Released receipts and the stable job lock.
The complete 81-case Python/native suite, 47 Rust tests and repeated 47-case job
harness passed locally without skips; 48 storage points each passed SIGKILL and
EIO retry, plus 12 file-I/O faults. Independent-server/resource regressions passed.
Source-bound reports are in the [M3 ledger](M3-LOCAL.md#workspace-and-storage-follow-up).
Publication/CI qualification for this increment remains pending; older CI reports
do not qualify these new changes. Full M3 remains open.

**D024 verified publication:** e599df7 is published on main and passed the fresh
Linux/macOS run 46068024173. Both runners passed all counts/gates above, including
108 storage observations. The six downloaded reports matched all 31 source inputs;
ZIP digests matched GitHub metadata. [Archived evidence](CI-VALIDATION.md#m3-workspace-management-and-storage-faults)
records actual runner results and annotations. The final evidence-only update
preserves the tested implementation/build/workflow/assets. Full M3 remains open.

**D025 autonomous qualification:** The owner authorized exhausting defined work
without repeated confirmation. Local admission/Committed recovery fixes,
B01–B16 BAM controls and the structural C01–C30 reference index are complete:
88 Python/native and 47 Rust tests passed; the repeated 54-case job harness and
independent-server/resource checks passed. Fresh CI qualification remains pending.
The [contract review and planning boundary](CONTRACT-REVIEW.md) separates the
completed concrete RFC 0002 backlog from undefined full-M3 and later scope.

**D025 verified boundary:** d27beca passed run 46072529338 on both observed
runners with the counts above, all 108 storage and 16 semantic observations,
nine workspace observations, independent-server/resource gates and the 30-case
structural reference index (zero behavior tests executed by that index). All
eight downloaded reports matched 35 source inputs and both ZIP digests matched
GitHub metadata. [Permanent evidence](CI-VALIDATION.md#m3-accepted-output-and-contract-qualification)
is archived. The current defined BAM-job implementation/failure tasks are done;
the owner's requested stopping point for milestone replanning is reached. Full
M3 and M4–M6 are not declared complete; the cosmetic social-preview side task
remains unverified. The final evidence update preserves tested code/build/
workflow/vector/assets and attributes success to the actual d27beca run.
