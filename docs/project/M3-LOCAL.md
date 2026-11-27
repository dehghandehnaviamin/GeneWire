# M3 verified BAM job evidence

Snapshot: 2026-11-27. **First subset passed Linux/macOS CI; full M3 exit remains open.**
The owner instructed starting recovery work after M2. See D020 and
[RFC 0002](../rfcs/0002-recoverable-bam-jobs.md) for the adopted subset.
The initial evidence below is local. Under D021, a32062f and the CI wiring/fix
were published on main. Revision 87732e7 passed
[Linux/macOS CI](CI-VALIDATION.md#m3-verified-source-bam-jobs). No software release
or deployment is claimed.

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

## Local evidence

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
identify the exact tested source. Remote qualification for this follow-up is
recorded only after its own completed run.

Observed locally for D023: 65 Python/native tests and the repeated 31-case
recovery/cancellation harness passed without skips; independent htsget-rs and
both HTSlib paths still matched Q1–Q5. The two linked local reports bind these
results to source-file hashes and preserve the preceding CI evidence unchanged.

RecoveryReport now exposes cleanup_complete separately from its error and
publication/sync flags. A cancelled operation with incomplete supervisor cleanup
cannot be mistaken for a fully stopped job even when network cleanup completed.
Storage failures conservatively leave cleanup unconfirmed as well.

## Remaining gates

Full M3 acceptance remains open. This increment does not supply byte-offset
resume, multi-object manifests, external acknowledgements, arbitrary consumer
rollback/exactly-once side effects, malicious same-user mutation protection,
network filesystems, power-loss durability or broad OS qualification. A
hard-killed supervisor cannot guarantee orphan reaping; recovery never uses stale
PIDs to terminate processes. Retain the job directory and its lock inode, do not
move its destination, and remove the private spool/receipt manually only when
future recovery is no longer needed and no job owns the lock. Input/output
payload files remain retained after success by design.
