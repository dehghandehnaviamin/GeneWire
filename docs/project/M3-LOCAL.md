# M3 verified BAM job evidence

Snapshot: 2026-11-27. **First subset passed Linux/macOS CI; full M3 exit remains open.**
The owner instructed starting recovery work after M2. See D020 and
[RFC 0002](../rfcs/0002-recoverable-bam-jobs.md) for the adopted subset.
Initial local and first-subset CI evidence is preserved below. The current D023
job-lifecycle revision 7f15c77 passed
[Linux/macOS cancellation CI](CI-VALIDATION.md#m3-cooperative-cancellation).
No software release or deployment is claimed.

## Behavior and storage boundary

`genewire.recovery.recover_bam` wraps the existing Rust/Python network reader and
supervised BAM filter. Its expected digest pins the exact encoded upstream
regional response; the caller must obtain that digest through a trusted external
channel. It is not a digest of the final filtered output or a claim of genomic
record completeness. No digest-discovery or server-manifest mechanism exists.

The source, result and bounded JSON receipt live in an explicit private workspace
beside the destination. The receipt binds service, object, interval, destination,
byte budgets and policy through a request fingerprint without storing their raw
values or credentials. A fingerprint is not anonymization or authentication of
the receipt. The local owner/parent directory are trusted; BAM files retain their
contents and must remain outside the repository.

| Receipt | Checked recovery behavior |
| --- | --- |
| Downloading | Discard incomplete owned artifacts; fetch a new complete response |
| Verified | Rehash the full source; repeat analysis locally |
| Ready | Rehash source and result; publish or recognize the original result inode |
| Committed | Verify retained result and destination identity; return without network or a new output inode |

Input and decoded output have independent default 1 GiB file budgets. The entire
source must be present before decoding, so this optional adapter adds disk space
and latency compared with M2 streaming. The existing M2 byte reader remains
available. Receipt reads are capped at 4 KiB, hashing/file reads use 64 KiB chunks,
workspace scanning is bounded and only fixed owned artifacts are removed.

File/receipt/directory sync failures are failures. If publication is already
recognized, `output_committed=True` can coexist with failure and
`sync_confirmed=False`; retry the same job to reconcile it. A false committed
flag does not assert the destination path is absent, for example on a conflict.
Local source reads inside the supervisor have explicit VerifiedLocalBam labels;
their placeholder counters are not native-memory measurements and are not
returned as a reconstructed network report. RecoveryReport.transport is present
only when this invocation actually opened a network stream.

## Initial local evidence

The recorded environment is macOS 27.0 arm64, CPython 3.14.6, Rust 1.93.0,
uv 0.13.10 and the locked M2 dependencies. No dependency was added.

| Check | Observed local result |
| --- | --- |
| Rust workspace | 47 passed; formatting and clippy with warnings denied passed |
| Complete Python/native suite | 53 passed, zero skips; includes 19 recovery tests |
| Recovery-only harness | 19 passed, zero skips; [raw source-bound report](evidence/2026-11-27-m3-recovery.json) |
| Actual SIGKILL | Downloading, partial input, Verified, decoded-before-ready, Ready, post-link and Committed; controlled worker active during supervisor death also exercised |
| Scientific tiny oracle | Recovered Q1–Q5 matched the original expected name/multiplicity sets with zero new network requests after Verified |
| Failure admission | Corrupt/truncated input, corrupt result, malformed/oversized/duplicate/unknown state, mismatched request/limits/destination, symlinks, conflicting output, unknown workspace files and competing processes rejected |
| Storage/cancellation | Injected ENOSPC/EIO and sync failures, output/input limits, interrupted downloads and KeyboardInterrupt; no incomplete output accepted |
| Independent M2 regression | Pinned htsget-rs/HTSlib Q1–Q5 still matched; [raw report](evidence/2026-11-27-m3-interop.json) |
| Resource M2 regression | Both 64 MiB retention modes passed copy/payload/cleanup gates; [raw report](evidence/2026-11-27-m3-resources.json) |

The process tests use generated synthetic BAM and loopback-only HTTP. SIGKILL is
real; filesystem failures are explicitly injected, not physical disk exhaustion
or power interruption. The active-worker test uses a controlled subprocess under
the real supervisor; other successful recoveries use the actual pysam decoder.
The independent server probe exercises the existing M2 path, not a newly
qualified digest-discovery interface for arbitrary htsget servers.

Run [the documented local commands](../development.md#optional-recoverable-bam-jobs)
to reproduce the source-bound evidence. Historical CI evidence remains tied to
its original tested revision. Initial local reports are now explicitly anchored
to a32062f; their hashes describe that version of the tests, before the CI fixture
fix. The later reports below bind the fresh CI revision independently.

## Observed CI qualification

[Run 46035043779](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46035043779)
completed successfully for 87732e7 on Ubuntu x86_64 and macOS arm64 with
CPython 3.14.10. Each passed 47 Rust and 53 Python/native tests without skips,
then repeated the 19 recovery cases to produce a structured report. The harness
is a subset rerun, not 19 additional distinct tests. Both passed the eight
SIGKILL boundaries, recovered Q1–Q5 without new requests after Verified,
independent-server comparison and 64 MiB resource checks. Downloaded artifacts
matched the tested source hashes; [per-runner reports and metadata](CI-VALIDATION.md#m3-verified-source-bam-jobs)
are permanently archived. Neither job has warning annotations; the macOS capacity
notice remains.

The first M3 run failed on macOS before recovery checks due to the short existing
ticket-deadline test; D021 records the wider scheduling margins and stronger
successful-retry negative control. The fresh successful run includes that fix.
Only documentation/evidence changes follow this tested revision in the final
publication; no new workflow success is invented for that docs-only commit.

## Cancellation follow-up

The D023 cancellation follow-up adds `Cancellation` to both BAM APIs and is
tracked separately from the historical 87732e7 CI evidence. It interrupts blocked
native reads, checks spool hashing and supervises cancellation through child
shutdown, including the final wait after pipes close. Token cancellation is
serialized with output-link admission; a valid published result is preserved.
The expanded harness covers 19 recovery plus 12 cancellation cases. Its local
source-bound [recovery/cancellation report](evidence/2026-11-27-m3-cancellation.json)
and [independent-server regression](evidence/2026-11-27-m3-cancellation-interop.json)
identify the exact tested source at 7f15c77.

Observed locally for D023: 65 Python/native tests and the repeated 31-case
recovery/cancellation harness passed without skips; independent htsget-rs and
both HTSlib paths still matched Q1–Q5. The two linked local reports bind these
results to source-file hashes and preserve the preceding CI evidence unchanged.

The follow-up was published and [run 46039605642](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/46039605642)
completed successfully on Ubuntu x86_64 and macOS arm64. Each passed 47 Rust and
65 Python/native tests without skips, then repeated the 31-case job harness.
The ten structured cancellation observation points and all earlier SIGKILL/truth
gates passed; downloaded reports matched the published source hashes.
[Permanent per-runner evidence](CI-VALIDATION.md#m3-cooperative-cancellation)
includes independent-server/resource checks and actual annotations. Only the
hosted macOS capacity notice remains; the final docs-only update preserves the
tested code/workflow/assets.

RecoveryReport now exposes cleanup_complete separately from its error and
publication/sync flags. A cancelled operation with incomplete supervisor cleanup
cannot be mistaken for a fully stopped job even when network cleanup completed.
Storage failures conservatively leave cleanup unconfirmed as well.

## Workspace and storage follow-up

D024 adds `genewire.jobs.inspect_bam_job` and `clean_bam_job`. They bind the same
query/destination/digest/budgets and reuse the existing nonblocking lock without
creating missing jobs or issuing network requests. Inspection is read-only;
cleanup validates all candidates before deleting owned temporary files. Verified
source and Ready source/result survive cleanup. A matching Ready output alias
survives too; recovery completes its receipt. A missing initialized lock is
rejected rather than recreated as a second ownership domain.

After Committed, cleanup persists Releasing before deleting redundant input,
syncs the workspace, then persists Released. The stable lock, receipt and result
alias remain; the alias shares the accepted destination inode. Releasing/Released
recovery verifies that result/output and finishes without source, network or
decoding. Committed inspection/cleanup does not require redundant source content
to remain intact. Retained byte counts describe logical file-name extents, not
physical allocation; receipt source_bytes remains historical after release.
These two new phases extend the pre-alpha version-1 vocabulary; old readers fail
closed on unknown phases. No schema/fingerprint migration is implied.

Observed locally on the recorded macOS runner:

| Check | Result |
| --- | --- |
| Full Python/native discovery | 81 passed, zero skips (65 preceding cases, 13 workspace cases, three storage matrix cases) |
| Rust and static checks | 47 passed; formatting and clippy with denied warnings passed |
| Expanded job harness | 47 passed, zero skips; repeats 19 recovery, 12 cancellation, 13 workspace and three storage cases, not additional unique tests |
| Workspace observations | Seven structured points; read-only/no-create/no-network, phase-preserving cleanup, output/lock identity, release retry; unsafe candidates and competing owners also checked |
| Storage boundaries | 48 distinct before/after points, each exercised with real SIGKILL and injected EIO; 96 observations |
| File I/O failures | 12 observations: actual short writes, injected ENOSPC, flush and close errors for receipt, source and decoder output; no partial destination accepted |
| Independent regression | Q1–Q5 still match pinned htsget-rs and both HTSlib paths; both 64 MiB resource modes pass payload/copy/cleanup gates |

The 48 points cover source file sync/rename/directory sync, result file/directory
sync, file sync/receipt replacement/directory sync for Verified, Ready, Committed,
Releasing and Released, public link/parent sync, source unlink and release sync.
Every failed/killed invocation is retried with a fresh subprocess client. The
checks assert original output identity when already present, exact tiny record
names, byte equality of the output alias and no re-fetch after a verified receipt.
Released retries explicitly forbid network and decoder calls. Incomplete inputs
without a verified receipt still restart from zero, even after their file sync.

The first local matrix run exposed two untriggered parent-sync injections because
the test helper compared an unresolved temporary path with its resolved alias.
The helper was fixed; the final full suite and independently repeated harness
passed. No production failure is inferred from that instrumentation error.

Raw source-bound reports: [job/storage](evidence/2026-11-27-m3-storage.json),
[independent server](evidence/2026-11-27-m3-storage-interop.json) and
[resources](evidence/2026-11-27-m3-storage-resources.json). Their hashes identify
the current local implementation/tests. This follow-up has not yet been remotely
qualified; preceding CI evidence remains attached to 7f15c77.

## Remaining gates

Full M3 acceptance remains open. This increment does not supply byte-offset
resume, multi-object manifests, external acknowledgements, arbitrary consumer
rollback/exactly-once side effects, malicious same-user mutation protection,
network filesystems, power-loss durability or broad OS qualification. A
hard-killed supervisor cannot guarantee orphan reaping; recovery never uses stale
PIDs to terminate processes. Retain the job directory and its lock inode, do not
move its destination. Use explicit cleanup to release owned input after success;
retain the receipt, lock inode and result alias for future reconciliation. Cleanup
does not securely erase payloads or remove all genomic copies. Broader retention
policy, filesystem/device failure qualification and M3 exit remain separate work.
