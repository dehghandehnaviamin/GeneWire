"""Inspect and clean existing private BAM job workspaces without network I/O."""
from __future__ import annotations

from dataclasses import dataclass
import os

from . import Cancellation, Client, GeneWireError
from . import recovery as store


@dataclass(frozen=True)
class WorkspaceReport:
    state: str
    error: str | None
    phase: str
    retained_source_bytes: int
    retained_result_bytes: int
    source_verified: bool
    result_verified: bool
    output_verified: bool
    removed_files: tuple[str, ...]
    sync_confirmed: bool
    cleanup_complete: bool


def _usage(job, entries, source_limit, result_limit, token):
    source_bytes = result_bytes = 0
    for name in entries:
        token._check()
        if name == "lock":
            continue
        links = (1, 2) if name == "result.bam" or name.startswith(".genewire-") else (1,)
        with store._private_open(job / name, links=links) as file:
            size = os.fstat(file.fileno()).st_size
        if name in ("source.bam", "source.partial"):
            if size > source_limit:
                store._fail("ResourceLimit")
            source_bytes += size
        elif name == "result.bam" or name.startswith(".genewire-"):
            if size > result_limit:
                store._fail("ResourceLimit")
            result_bytes += size
        elif size > 4096:
            store._fail("ResourceLimit")
    return source_bytes, result_bytes


def _snapshot(job, target, state, entries, expected, source_limit, result_limit, token):
    usage = _usage(job, entries, source_limit, result_limit, token)
    phase = state["phase"]
    source_verified = result_verified = output_verified = False
    # Accepted output can be inspected/released even if its now-redundant input
    # is missing or corrupt. Incomplete jobs still require the pinned source.
    if phase in ("Verified", "Ready"):
        size, digest = store._hash_file(job / "source.bam", source_limit, cancellation=token)
        if size != state["source_bytes"] or digest != expected:
            store._fail("IntegrityFailed")
        source_verified = True
    if phase in ("Ready", "Committed", "Releasing", "Released"):
        size, digest = store._hash_file(job / "result.bam", result_limit, links=(1, 2), cancellation=token)
        if size != state["output_bytes"] or digest != state["output_sha256"]:
            store._fail("IntegrityFailed")
        result_verified = True
        if os.path.lexists(target):
            if not store._output_matches(target, job / "result.bam"):
                store._fail("DestinationExists")
            output_verified = True
        elif phase != "Ready":
            store._fail("CheckpointInvalid")
    elif os.path.lexists(target):
        store._fail("DestinationExists")
    return *usage, source_verified, result_verified, output_verified


def _manage(client, object_id, reference, start, end, destination, workspace, *,
            expected_sha256, max_source_bytes, max_output_bytes, cancellation, clean):
    token = store._request_token(client, object_id, reference, start, end, expected_sha256,
                                 max_source_bytes, max_output_bytes, cancellation)
    lock = state = None
    error = None
    source_bytes = result_bytes = 0
    source_verified = result_verified = output_verified = synced = False
    cleanup_ok = True
    removed = []
    try:
        token._check()
        target, job = store._job_paths(destination, workspace)
        fingerprint = store._job_fingerprint(client, object_id, reference, start, end, target,
                                              expected_sha256, max_source_bytes, max_output_bytes)
        lock = store._open_job_lock(job, create=False)
        entries = store._scan_workspace(job)
        state = store._read_state(job, fingerprint)
        if state is None:
            store._fail("CheckpointMissing")
        source_bytes, result_bytes, source_verified, result_verified, output_verified = _snapshot(
            job, target, state, entries, expected_sha256, max_source_bytes, max_output_bytes, token)
        if clean:
            phase = state["phase"]
            if phase == "Committed":
                candidates = store._deletion_candidates(entries, "Releasing")
                store._preflight_removals(job, candidates)
                token._check()
                state = store._advance(job, state, phase="Releasing")
            if state["phase"] in ("Releasing", "Released"):
                state = store._finish_release(job, state, token, removed)
                source_verified = False
            else:
                store._remove_artifacts(job, store._deletion_candidates(entries, phase), token, removed)
                store._sync_dir(job)
            source_bytes, result_bytes = _usage(
                job, store._scan_workspace(job), max_source_bytes, max_output_bytes, token)
            synced = True
    except GeneWireError as failure:
        error = str(failure)
    except FileNotFoundError:
        error = "CheckpointMissing" if lock is None else "CheckpointInvalid"
    except (OSError, ValueError):
        error = "StorageFailure"
        cleanup_ok = False
    finally:
        if lock is not None:
            try:
                lock.close()
            except OSError:
                error = error or "StorageFailure"
                cleanup_ok = False
    return WorkspaceReport(
        "Failed" if error else "Cleaned" if clean else "Inspected", error,
        state["phase"] if state else "New", source_bytes, result_bytes,
        source_verified, result_verified, output_verified, tuple(removed), synced, cleanup_ok,
    )


def inspect_bam_job(
    client: Client, object_id: str, reference: str, start: int, end: int,
    destination: str | os.PathLike[str], workspace: str | os.PathLike[str], *,
    expected_sha256: str, max_source_bytes: int = 1024**3, max_output_bytes: int = 1024**3,
    cancellation: Cancellation | None = None,
) -> WorkspaceReport:
    """Verify an existing job under its lock without creating, deleting or fetching.

    Counts are logical file bytes; a retained result alias shares the final inode.
    Source content is verified only for Verified/Ready jobs that may need replay.
    sync_confirmed is false because inspection does not perform storage writes.
    """
    return _manage(client, object_id, reference, start, end, destination, workspace,
                   expected_sha256=expected_sha256, max_source_bytes=max_source_bytes,
                   max_output_bytes=max_output_bytes, cancellation=cancellation, clean=False)


def clean_bam_job(
    client: Client, object_id: str, reference: str, start: int, end: int,
    destination: str | os.PathLike[str], workspace: str | os.PathLike[str], *,
    expected_sha256: str, max_source_bytes: int = 1024**3, max_output_bytes: int = 1024**3,
    cancellation: Cancellation | None = None,
) -> WorkspaceReport:
    """Remove owned temporary input/output while preserving valid recovery/output.

    Incomplete jobs keep verified source/result. Committed jobs release their
    source through a recoverable Releasing/Released receipt; keep lock, receipt
    and the final result alias. Never delete the public destination or workspace.
    A partial cleanup is retryable; inspect error, removed_files and sync flags.
    """
    return _manage(client, object_id, reference, start, end, destination, workspace,
                   expected_sha256=expected_sha256, max_source_bytes=max_source_bytes,
                   max_output_bytes=max_output_bytes, cancellation=cancellation, clean=True)
