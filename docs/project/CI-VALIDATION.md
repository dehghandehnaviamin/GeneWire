# Cross-platform CI evidence

The latest observed run covers the M3 BAM job cancellation/cleanup follow-up:
[46039605642](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46039605642)
at 7f15c77. See [cancellation results](#m3-cooperative-cancellation) below.
Historical M2 and first-subset M3 results remain preserved here.

## Historical M2 reference evidence

Evaluation date: 2026-11-27. The narrow reference implementation at
[dc46c2b](https://github.com/dehghandehnaviamin/GeneWire/commit/dc46c2b8eb045149de396f439f6e4c445cf6ceba)
passed [workflow 46021619658](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46021619658)
after the Node.js 24 action migration.
Both jobs finished with success. This evidence qualifies that tested revision;
later implementation or workflow changes require their own checks. The archived
result is not a substitute for observing subsequent workflow runs.

| Observed job | Rust | Python/native | Skips | Runtime |
| --- | --- | --- | --- | --- |
| [Ubuntu](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46021619658/job/140582420528) | 47 passed | 34 passed | 0 | Ubuntu 26.04.1 x86_64, CPython 3.14.10 |
| [macOS](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46021619658/job/140582420004) | 47 passed | 34 passed | 0 | macOS 26.7.2 arm64, CPython 3.14.10 |

Both used Rust 1.93.0, uv 0.13.10, locked project dependencies, pysam 0.24.1 /
HTSlib 1.24, and independently built the pinned htsget-rs source. Each passed
formatting, clippy, local HTTP/native tests, supervised BAM tests, Q1–Q5 against
the real local server and two independent HTSlib paths, and the 64 MiB resource
probe in both caller-retention modes.

## Permanent evidence

[Run summary](evidence/ci-46021619658/summary.json) records job/commit/artifact
identity, observed test counts and archive/report hashes. The GitHub-reported ZIP
digest is metadata; the downloaded JSON was independently checked against source
file hashes and result gates. Archived JSON adds source_commit provenance and is
not claimed byte-identical to the original ZIP entries.

- Ubuntu: [interoperability](evidence/ci-46021619658/ubuntu-interop.json),
  [resources](evidence/ci-46021619658/ubuntu-resources.json).
- macOS: [interoperability](evidence/ci-46021619658/macos-interop.json),
  [resources](evidence/ci-46021619658/macos-resources.json).

The initial successful run for da92bc9 remains preserved in its
[historical summary](evidence/ci-45995255517/summary.json). Its two Node.js 20
warnings remain in that run's history; the new run has zero warning annotations,
zero Ubuntu annotations and one macOS capacity notice. Job logs also contain no
Node.js 20 deprecation warning. The latest summary binds the tested workflow hash
as well as implementation hashes and records the actual annotation messages.

Each returned the expected five name/multiplicity sets, with successful full BAM
decode/filter and cleanup. For both resource modes on both runners, each named
output-copy counter equaled 67,108,864 bytes, accepted payload peak stayed below
2 MiB, and retained payload was zero after close. These are logical accepted
payload/copy counts; allocator slack, HTTP/TLS/JSON buffers, decoder RSS and
caller retention remain separate. Raw RSS/tracemalloc/timings are single-run
observations, not an advantage claim or hard process-memory ceiling.

## M2 exit scope

The engineering exit applies to the implemented single-region BAM reference
path, not the entire provisional M1 contract or every variant of C01–C30.

| Minimum gate | Evidence |
| --- | --- |
| Working Rust/Python build and CI | Both observed jobs and locked setup |
| Real existing server and full decode | Pinned independent htsget-rs, supervised mature decoder |
| Independent tiny truth | Q1–Q5 and independent htsget/indexed HTSlib comparisons |
| Declared transport/failure policy | Strict ticket/range/length/encoding/credential checks, bounded retry/deadline, no replay after exposure, fresh-query separation |
| Native ownership and cleanup | Owned bytes/runtime lifetime, serialized handoff/cancel checks, cleanup timeout/retry, panic translation |
| Analysis/process failure | Early/nonzero exit, SIGKILL, SIGINT, timeout, output/diagnostic budgets, staging and filesystem failure checks |
| Resource and outbound-policy review | Named payload/copy accounting plus RSS probes; target-specific dependency inventory, pins and TLS/IPv6 tests |

M2's narrow engineering gate is complete under D018. M3–M6 remain planned.
Hard-killed supervisor crash recovery, arbitrary descendants, full allocator
accounting, broader APIs/platform qualification, security audits, comparative
benchmarks and production/release approval are not supplied by this CI run.
Optional external review is tracked separately under the current D022 policy.

## Action runtime maintenance

The initial successful run reported Node.js 20 deprecation warnings for the
four pinned actions. D019 upgrades them to immutable official releases whose
`action.yml` explicitly selects Node.js 24:

| Action | Release | Verified metadata |
| --- | --- | --- |
| actions/checkout | v7.0.1 | [action.yml](https://github.com/actions/checkout/blob/3d3c42e5aac5ba805825da76410c181273ba90b1/action.yml) |
| actions/setup-python | v7.1.0 | [action.yml](https://github.com/actions/setup-python/blob/6d4fd22b20465ccc0f7354476588e8df7c9ca0e0/action.yml) |
| astral-sh/setup-uv | v10.4.0 | [action.yml](https://github.com/astral-sh/setup-uv/blob/1db35dd8eee11c5894872e0b383ae6c406cf738d/action.yml) |
| actions/upload-artifact | v7.0.2 | [action.yml](https://github.com/actions/upload-artifact/blob/cf430e030ddbb5b0abf93d22962f4752f3646cd9/action.yml) |

The hosted runner's separate macOS arm64 capacity notice concerns queue time.
The matrix retains arm64 coverage; it does not substitute an Intel runner or hide
annotations. Run 46021619658 completed successfully on both targets and verified
the migration without those warnings. Only the infrastructure capacity notice
remains. The final evidence-only publication preserves all implementation,
build and workflow inputs from dc46c2b and uses a docs-only CI skip; the observed
success above belongs to dc46c2b, not to an unrun documentation commit.

## M3 verified-source BAM jobs

Evaluation date: 2026-11-27. Implementation and CI fixture revision
[87732e7](https://github.com/dehghandehnaviamin/GeneWire/commit/87732e7c41dde4cdda181d7807a1b80f869ba576)
passed [run 46035043779](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46035043779).

| Observed job | Rust | Python/native | Recovery harness | Skips |
| --- | --- | --- | --- | --- |
| [Ubuntu x86_64](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46035043779/job/140628192767) | 47 passed | 53 passed | 19 passed | 0 |
| [macOS arm64](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46035043779/job/140628193243) | 47 passed | 53 passed | 19 passed | 0 |

The 19 recovery cases are part of the 53-test Python suite and are repeated by
the evidence harness; they are not 19 additional distinct tests. Both jobs
passed formatting/clippy, locked native/Python builds, pinned independent-server
Q1–Q5 comparisons and both 64 MiB resource modes. Rust/uv and decoder versions
remain those recorded above; both used CPython 3.14.10. Ubuntu had no annotations;
macOS retained only the hosted-capacity notice, with no warning annotations or
Node.js 20 warning in either log.

Permanent [run summary](evidence/ci-46035043779/summary.json) records the tested
source/workflow hashes, job/artifact identities, actual annotations, counts and
normalized report hashes:

- Ubuntu: [recovery](evidence/ci-46035043779/ubuntu-recovery.json),
  [interoperability](evidence/ci-46035043779/ubuntu-interop.json),
  [resources](evidence/ci-46035043779/ubuntu-resources.json).
- macOS: [recovery](evidence/ci-46035043779/macos-recovery.json),
  [interoperability](evidence/ci-46035043779/macos-interop.json),
  [resources](evidence/ci-46035043779/macos-resources.json).

All six downloaded reports matched the tested source hashes. Recovery reports
contain actual SIGKILL at eight distinct boundaries and Q1–Q5 oracle matches
with no new requests after Verified. Input/result corruption, receipt mismatch,
concurrent owners, interruption, limits and injected ENOSPC/EIO/sync errors are
covered. The independent-server/resource reports satisfy the same limited M2
comparison and logical payload/copy gates described above. GitHub-reported ZIP
digests remain archive metadata; normalized JSON adds source_commit and is not
claimed byte-identical to the ZIP entries.

The [initial M3 run](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46034485690)
failed on macOS in the pre-existing short ticket-deadline fixture before M3
tests ran; Ubuntu succeeded. D021 records its correction with unchanged
production timeout policy. The successful fresh run above tests that correction;
the earlier failure is retained in the summary rather than reclassified.

This qualifies the [RFC 0002 subset and its explicit limits](M3-LOCAL.md), not
the full M3 milestone, byte-offset resume, physical power-loss behavior, a stable
package, general genomic correctness or a release. The final evidence/status
commit is docs-only with CI skipped after verifying implementation/build/workflow
inputs remain byte-identical to 87732e7. Its parent run is the observed evidence;
the documentation commit does not claim another successful workflow.

## M3 cooperative cancellation

Evaluation date: 2026-11-27. Source
[7f15c77](https://github.com/dehghandehnaviamin/GeneWire/commit/7f15c77132861ddda0192e5cd130976e158407f3)
passed [run 46039605642](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46039605642).

| Observed job | Rust | Python/native | Repeated job harness | Skips |
| --- | --- | --- | --- | --- |
| [Ubuntu x86_64](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46039605642/job/140643675414) | 47 passed | 65 passed | 31 passed | 0 |
| [macOS arm64](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46039605642/job/140643674872) | 47 passed | 65 passed | 31 passed | 0 |

The 31-case harness repeats 19 recovery and 12 cancellation tests already in
the 65-test Python suite. Both jobs passed locked builds, formatting/clippy,
independent-server/HTSlib Q1–Q5 and both 64 MiB resource modes on CPython 3.14.10.
The toolchain/action pins remain unchanged. Ubuntu had no annotations; macOS
retained only the hosted-capacity notice. Neither job had warning annotations or
a Node.js 20 warning in its log.

The permanent [summary](evidence/ci-46039605642/summary.json) binds the tested
source/workflow, job/artifact identities, actual test counts, annotation messages
and normalized report hashes:

- Ubuntu: [recovery/cancellation](evidence/ci-46039605642/ubuntu-recovery.json),
  [interoperability](evidence/ci-46039605642/ubuntu-interop.json),
  [resources](evidence/ci-46039605642/ubuntu-resources.json).
- macOS: [recovery/cancellation](evidence/ci-46039605642/macos-recovery.json),
  [interoperability](evidence/ci-46039605642/macos-interop.json),
  [resources](evidence/ci-46039605642/macos-resources.json).

All six reports matched the source hashes at 7f15c77. In addition to the earlier
SIGKILL/oracle gates, both runners observed cancellation of a blocked native data
read, bounded rehash work, a stalled worker and the final wait of a pipe-closed
live child. Cancellation before publication prevented output; after publication
it preserved a Complete result. A simulated incomplete supervisor cleanup stayed
explicitly unconfirmed despite completed network cleanup. Subscription-lifetime,
pre-cancelled operations, type validation and subsequent recovery checks passed.
Resource/oracle gates retain the scope described above.

The ZIP digests are GitHub-reported metadata. Archived JSON adds source_commit;
its normalized hashes do not assert byte equality with the original ZIP entries.
Only documentation/evidence changes follow 7f15c77 in the final publication,
with CI skipped after checking implementation/build/workflow/assets are unchanged.
The observed success belongs to that actual run, not to an unrun docs commit.
