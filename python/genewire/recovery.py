"""Local POSIX BAM job receipts; complete-source reuse, never byte-offset resume."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat

from . import Client, GeneWireError, MemoryReport, Report, Stream
from .analysis import filter_bam


@dataclass(frozen=True)
class RecoveryReport:
    state: str
    error: str | None
    phase: str
    source_reused: bool
    source_bytes: int
    output_bytes: int
    output_committed: bool
    sync_confirmed: bool
    # Only a network attempt observed in this invocation; never reconstructed.
    transport: Report | None


def _fail(category: str) -> None:
    raise GeneWireError(category)


def _private_open(path: Path, *, links: tuple[int, ...] = (1,)):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or info.st_mode & 0o077 or info.st_nlink not in links):
            _fail("CheckpointInvalid")
        return os.fdopen(fd, "rb")
    except BaseException:
        os.close(fd)
        raise


def _sync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _discard(path: Path) -> None:
    try:
        with _private_open(path, links=(1, 2)):
            pass
    except FileNotFoundError:
        return
    path.unlink()


def _write_state(workspace: Path, state: dict) -> None:
    temporary = workspace / "state.tmp"
    _discard(temporary)
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as output:
        output.write((json.dumps(state, sort_keys=True) + "\n").encode())
        output.flush()
        os.fsync(output.fileno())
    os.replace(temporary, workspace / "state.json")
    _sync_dir(workspace)


def _advance(workspace: Path, state: dict, **changes) -> dict:
    updated = dict(state, **changes)
    _write_state(workspace, updated)
    return updated


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate")
        result[key] = value
    return result


def _read_state(workspace: Path, fingerprint: str) -> dict | None:
    try:
        with _private_open(workspace / "state.json") as source:
            data = source.read(4097)
    except FileNotFoundError:
        return None
    try:
        if len(data) > 4096:
            raise ValueError("oversized")
        state = json.loads(data, object_pairs_hook=_unique_pairs)
        if (type(state) is not dict or set(state) != {
                "version", "request", "phase", "source_bytes", "output_bytes", "output_sha256"}
                or type(state["version"]) is not int or state["version"] != 1
                or state["phase"] not in ("Downloading", "Verified", "Ready", "Committed")
                or not _digest(state["request"])
                or any(type(state[k]) is not int or not 0 <= state[k] <= 2**63 - 1
                       for k in ("source_bytes", "output_bytes"))):
            raise ValueError("invalid")
        ready = state["phase"] in ("Ready", "Committed")
        if (ready and not _digest(state["output_sha256"])) or (
                not ready and (state["output_sha256"] is not None or state["output_bytes"] != 0)):
            raise ValueError("invalid")
        if state["phase"] == "Downloading" and state["source_bytes"] != 0:
            raise ValueError("invalid")
    except (ValueError, TypeError, UnicodeError, RecursionError):
        _fail("CheckpointInvalid")
    if state["request"] != fingerprint:
        _fail("CheckpointMismatch")
    return state


def _digest(value) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _hash_file(path: Path, limit: int, *, links=(1,), sync=False) -> tuple[int, str]:
    total = 0
    digest = hashlib.sha256()
    with _private_open(path, links=links) as source:
        if os.fstat(source.fileno()).st_size > limit:
            _fail("ResourceLimit")
        while data := source.read(65536):
            total += len(data)
            if total > limit:
                _fail("ResourceLimit")
            digest.update(data)
        if sync:
            os.fsync(source.fileno())
    return total, digest.hexdigest()


class _VerifiedFileStream(Stream):
    """Private supervisor input; local counters do not claim native measurements."""

    def __init__(self, path: Path, region: tuple[str, int, int]):
        self._file = _private_open(path)
        self._region = region
        self._done = self._closed = False
        self._delivered = 0

    def read_chunk(self, max_bytes=65536):
        data = self._file.read(max_bytes)
        self._delivered += len(data)
        self._done = not data
        return data

    def finish(self):
        if not self._done:
            _fail("InvalidState")
        return self.result()

    def result(self):
        return Report(
            "TransportComplete" if self._done else "Cancelled" if self._closed else "Fetching",
            self._delivered, 0, self._closed, None, "LocalSpool", False,
            "Complete" if self._closed else "NotStarted", None,
            "VerifiedLocalBam", "ExpectedSha256", MemoryReport(0, 0, 0, 0, 0),
            "VerifiedLocalBam", "ExpectedSha256", "ExpectedSha256",
        )

    def cancel(self):
        pass  # Local regular-file reads; no native worker to cancel.

    def close(self):
        self._file.close()
        self._closed = True


def recover_bam(
    client: Client,
    object_id: str,
    reference: str,
    start: int,
    end: int,
    destination: str | os.PathLike[str],
    workspace: str | os.PathLike[str],
    *,
    expected_sha256: str,
    max_source_bytes: int = 1024**3,
    max_output_bytes: int = 1024**3,
    timeout_s: float = 600,
    cleanup_timeout_s: float = 5,
) -> RecoveryReport:
    """Recover one explicitly pinned BAM job; retain a private source/result receipt.

    Workspace must be a private sibling of destination on a local POSIX filesystem.
    Reinvoke with identical arguments to recover. Partial input starts from zero;
    only hash-verified complete input is reused. No remote digest is inferred.
    Sync confirmation covers successful fsync calls, not proven power-loss safety.
    """
    if os.name != "posix":
        _fail("Unsupported")
    if (not isinstance(client, Client) or not _digest(expected_sha256)
            or any(not isinstance(s, str) or not s or len(s.encode()) > 4096
                   or any(ord(c) < 32 or 127 <= ord(c) <= 159 for c in s)
                   for s in (object_id, reference)) or reference == "*"
            or any(type(n) is not int or not 0 <= n <= 2**32 - 1 for n in (start, end))
            or start >= end
            or any(type(n) is not int or not 0 < n <= 2**63 - 1
                   for n in (max_source_bytes, max_output_bytes))
            or any(type(n) not in (int, float) or not 0 < n <= 86400 or not math.isfinite(n)
                   for n in (timeout_s, cleanup_timeout_s))):
        _fail("InvalidQuery")

    import fcntl

    lock = None
    transport = None
    state = None
    reused = committed = synced = False
    error = None
    try:
        target = Path(destination).absolute()
        job = Path(workspace).absolute()
        parent = target.parent.resolve(strict=True)
        if job.parent.resolve(strict=True) != parent or target.name == job.name:
            _fail("InvalidQuery")
        target, job = parent / target.name, parent / job.name
        fingerprint = hashlib.sha256(json.dumps([
            "GeneWireBamJob1", client._service, object_id, reference, start, end,
            str(target), expected_sha256, max_source_bytes, max_output_bytes,
            "MappedReadOverlapBam",
        ], ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()
        try:
            job.mkdir(mode=0o700)
        except FileExistsError:
            pass
        info = job.lstat()
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o700):
            _fail("CheckpointInvalid")
        fd = os.open(job / "lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
        lock = os.fdopen(fd, "r+b")
        info = os.fstat(lock.fileno())
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                or info.st_mode & 0o077 or info.st_nlink != 1):
            _fail("CheckpointInvalid")
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            _fail("RecoveryBusy")
        _sync_dir(parent)
        # Bound scanning and never recursively remove arbitrary workspace contents.
        entries = []
        with os.scandir(job) as iterator:
            for entry in iterator:
                if len(entries) >= 16 or not (
                    entry.name in {"lock", "state.json", "state.tmp", "source.partial", "source.bam", "result.bam"}
                    or re.fullmatch(r"\.genewire-[a-z0-9_]+\.partial", entry.name)
                ):
                    _fail("CheckpointInvalid")
                entries.append(entry.name)
        state = _read_state(job, fingerprint)
        if state is None:
            if set(entries) - {"lock", "state.tmp"}:
                _fail("CheckpointInvalid")
            if os.path.lexists(target):
                _fail("DestinationExists")
            state = dict(version=1, request=fingerprint, phase="Downloading",
                         source_bytes=0, output_bytes=0, output_sha256=None)
            _write_state(job, state)
        if state["phase"] not in ("Ready", "Committed") and os.path.lexists(target):
            _fail("DestinationExists")
        for name in entries:
            if name == "state.tmp" or name.startswith(".genewire-"):
                _discard(job / name)
        if state["phase"] == "Downloading":
            for name in ("source.partial", "source.bam", "result.bam"):
                _discard(job / name)
            stream = client.open(object_id, reference, start, end)
            try:
                fd = os.open(job / "source.partial", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                digest, total = hashlib.sha256(), 0
                with os.fdopen(fd, "wb") as output:
                    while data := stream.read_chunk(65536):
                        total += len(data)
                        if total > max_source_bytes:
                            _fail("ResourceLimit")
                        output.write(data)
                        digest.update(data)
                    stream.finish()
                    output.flush()
                    os.fsync(output.fileno())
                if digest.hexdigest() != expected_sha256:
                    _fail("IntegrityFailed")
            finally:
                try:
                    stream.close()
                finally:
                    transport = stream.result()
            if transport.state != "TransportComplete" or not transport.cleanup_complete:
                _fail("CleanupTimeout")
            os.replace(job / "source.partial", job / "source.bam")
            _sync_dir(job)
            state = _advance(job, state, phase="Verified", source_bytes=total)
        else:
            reused = True
        size, digest = _hash_file(job / "source.bam", max_source_bytes)
        if size != state["source_bytes"] or digest != expected_sha256:
            _fail("IntegrityFailed")
        if state["phase"] == "Verified":
            _discard(job / "result.bam")
            local = _VerifiedFileStream(job / "source.bam", (reference, start, end))
            try:
                analysis = filter_bam(
                    local, job / "result.bam", reference, start, end,
                    timeout_s=timeout_s, cleanup_timeout_s=cleanup_timeout_s,
                    max_output_bytes=max_output_bytes,
                )
            finally:
                local.close()
            if analysis.state != "AnalysisComplete" or not analysis.cleanup_complete:
                _fail(analysis.error or "ConsumerFailed")
            size, digest = _hash_file(job / "result.bam", max_output_bytes, sync=True)
            _sync_dir(job)
            state = _advance(job, state, phase="Ready", output_bytes=size, output_sha256=digest)
        size, digest = _hash_file(job / "result.bam", max_output_bytes, links=(1, 2))
        if size != state["output_bytes"] or digest != state["output_sha256"]:
            _fail("IntegrityFailed")
        if state["phase"] == "Committed" and not os.path.lexists(target):
            _fail("CheckpointInvalid")
        try:
            os.link(job / "result.bam", target, follow_symlinks=False)
            committed = True
        except FileExistsError:
            original = (job / "result.bam").lstat()
            visible = target.lstat()
            if (not stat.S_ISREG(visible.st_mode)
                    or (original.st_dev, original.st_ino) != (visible.st_dev, visible.st_ino)):
                _fail("DestinationExists")
            committed = True
        _sync_dir(parent)
        state = _advance(job, state, phase="Committed")
        synced = True
    except GeneWireError as failure:
        error = str(failure)
    except (OSError, ValueError):
        error = "StorageFailure"
    finally:
        if lock is not None:
            lock.close()
    return RecoveryReport(
        "Complete" if error is None and synced else "Failed", error,
        state["phase"] if state else "New", reused,
        state["source_bytes"] if state else 0, state["output_bytes"] if state else 0,
        committed, synced, transport,
    )
