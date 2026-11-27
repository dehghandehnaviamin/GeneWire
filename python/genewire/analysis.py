"""Bounded POSIX process supervision and atomic staging for the BAM adapter."""
from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
import queue
import selectors
import signal
import subprocess
import sys
import tempfile
import threading
import time
from typing import Sequence

from . import Cancellation, GeneWireError, Report, Stream


@dataclass(frozen=True)
class AnalysisReport:
    state: str
    error: str | None
    transport: Report
    exit_code: int | None
    output_bytes: int
    output_committed: bool
    cleanup_complete: bool
    policy: str = "MappedReadOverlapBam"


def filter_bam(
    stream: Stream,
    destination: str | os.PathLike[str],
    reference: str,
    start: int,
    end: int,
    *,
    timeout_s: float = 600,
    cleanup_timeout_s: float = 5,
    max_output_bytes: int = 1024**3,
    cancellation: Cancellation | None = None,
) -> AnalysisReport:
    """Consume and close stream; commit filtered BAM only after both success gates.

    Requires pysam in the owning interpreter. The destination must not exist.
    A report records failures without including child diagnostics or input values.
    """
    if (not isinstance(reference, str) or not reference or reference == "*"
            or len(reference) > 4096 or any(ord(c) < 32 for c in reference)
            or any(type(n) is not int or not 0 <= n <= 2**32 - 1 for n in (start, end))
            or start >= end):
        raise GeneWireError("InvalidQuery")
    if stream.region != (reference, start, end):
        raise GeneWireError("InvalidQuery")
    return _supervise(
        stream, [sys.executable, "-m", "genewire._bam_consumer", reference, str(start), str(end)],
        destination, timeout_s=timeout_s, cleanup_timeout_s=cleanup_timeout_s,
        max_output_bytes=max_output_bytes,
        cancellation=cancellation,
    )


def _supervise(
    stream: Stream,
    command: Sequence[str],
    destination: str | os.PathLike[str],
    *,
    timeout_s: float = 600,
    cleanup_timeout_s: float = 5,
    max_output_bytes: int = 1024**3,
    cancellation: Cancellation | None = None,
) -> AnalysisReport:
    # subprocess pipe selectors and process-group termination are POSIX-only.
    if os.name != "posix":
        raise GeneWireError("Unsupported")
    if (any(type(n) not in (int, float) or not 0 < n <= 86400 or not math.isfinite(n)
            for n in (timeout_s, cleanup_timeout_s))
            or type(max_output_bytes) is not int or not 0 < max_output_bytes <= 2**63 - 1
            or (cancellation is not None and not isinstance(cancellation, Cancellation))):
        raise GeneWireError("InvalidQuery")
    token = cancellation if cancellation is not None else Cancellation()
    target = Path(destination)
    messages: queue.Queue[bytes | BaseException | None] = queue.Queue(maxsize=1)
    stopped = threading.Event()
    process = None
    pump = None
    stage = None
    output = None
    error = None
    written = 0
    committed = False
    cleanup_ok = True
    deadline = time.monotonic() + timeout_s
    unsubscribe = token._subscribe(stream.cancel)

    def send(value: bytes | BaseException | None) -> None:
        while not stopped.is_set():
            try:
                messages.put(value, timeout=.02)
                return
            except queue.Full:
                pass

    def produce() -> None:
        try:
            while not stopped.is_set():
                data = stream.read_chunk(65536)
                if not data:
                    stream.finish()
                    send(None)
                    return
                send(data)
        except BaseException as failure:
            send(failure)

    try:
        token._check()
        if target.exists():
            raise GeneWireError("ConsumerFailed")
        fd, stage = tempfile.mkstemp(prefix=".genewire-", suffix=".partial", dir=target.parent)
        output = os.fdopen(fd, "wb")
        process = subprocess.Popen(
            list(command), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, bufsize=0, start_new_session=True,
        )
        pump = threading.Thread(target=produce, name="genewire-analysis-input", daemon=True)
        pump.start()
        pending = memoryview(b"")
        input_closed = False
        diagnostics = 0
        with selectors.DefaultSelector() as selector:
            for pipe, event, label in (
                (process.stdin, selectors.EVENT_WRITE, "input"),
                (process.stdout, selectors.EVENT_READ, "output"),
                (process.stderr, selectors.EVENT_READ, "diagnostics"),
            ):
                os.set_blocking(pipe.fileno(), False)
                selector.register(pipe, event, label)
            while selector.get_map():
                token._check()
                if time.monotonic() >= deadline:
                    raise GeneWireError("DeadlineExceeded")
                if process.poll() is not None and not input_closed:
                    raise GeneWireError("ConsumerFailed")
                for key, _ in selector.select(timeout=min(.02, max(0, deadline-time.monotonic()))):
                    if key.data == "input":
                        if not pending:
                            try:
                                item = messages.get_nowait()
                            except queue.Empty:
                                # Avoid spinning on a writable pipe while network input stalls.
                                stopped.wait(.001)
                                continue
                            if isinstance(item, BaseException):
                                raise item
                            if item is None:
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                                input_closed = True
                                continue
                            pending = memoryview(item)
                        try:
                            count = os.write(key.fd, pending)
                            pending = pending[count:]
                        except BlockingIOError:
                            pass
                    else:
                        try:
                            data = os.read(key.fd, 65536)
                        except BlockingIOError:
                            continue
                        if not data:
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                        elif key.data == "output":
                            written += len(data)
                            if written > max_output_bytes:
                                raise GeneWireError("ResourceLimit")
                            output.write(data)
                        else:
                            diagnostics += len(data)
                            if diagnostics > 65536:
                                raise GeneWireError("ResourceLimit")
            # A child can close every pipe yet stay alive. Keep cancellation
            # responsive during that final wait as well as during pipe traffic.
            while process.poll() is None:
                token._check()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise GeneWireError("DeadlineExceeded")
                try:
                    process.wait(timeout=min(.02, remaining))
                except subprocess.TimeoutExpired:
                    pass
            if process.returncode != 0 or not input_closed:
                raise GeneWireError("ConsumerFailed")
    except GeneWireError as failure:
        error = str(failure)
    except subprocess.TimeoutExpired:
        error = "DeadlineExceeded"
    except (OSError, ValueError):
        error = "ConsumerFailed"
    except BaseException:
        # KeyboardInterrupt/SystemExit still run bounded resource cleanup below.
        error = "InternalFailure"
        raise
    finally:
        stopped.set()
        if error:
            stream.cancel()
        if process is not None:
            # Signal the session group even if its leader already exited: children
            # must not keep pipes or provisional analysis alive after the gate.
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(process.pid, sig)
                except ProcessLookupError:
                    pass
                if process.poll() is None:
                    try:
                        process.wait(timeout=cleanup_timeout_s / 2)
                    except subprocess.TimeoutExpired:
                        continue
            cleanup_ok = process.poll() is not None
            for pipe in (process.stdin, process.stdout, process.stderr):
                if pipe is not None:
                    try:
                        pipe.close()
                    except OSError:
                        cleanup_ok = False
        if pump is not None:
            pump.join(timeout=cleanup_timeout_s)
            cleanup_ok = cleanup_ok and not pump.is_alive()
        try:
            stream.close()
        except GeneWireError:
            cleanup_ok = False
        cleanup_ok = cleanup_ok and stream.result().cleanup_complete
        if output is not None:
            try:
                output.flush()
            except OSError:
                error = error or "ConsumerFailed"
            try:
                output.close()
            except OSError:
                cleanup_ok = False
                error = error or "ConsumerFailed"
            if error is None and cleanup_ok:
                try:
                    # Close/flush must succeed before the no-overwrite commit.
                    token._commit(lambda: os.link(stage, target))
                    committed = True
                except GeneWireError as failure:
                    error = str(failure)
                except OSError:
                    error = "ConsumerFailed"
        if stage is not None:
            try:
                os.unlink(stage)
            except OSError:
                cleanup_ok = False
        unsubscribe()
    if not cleanup_ok:
        error = error or "CleanupTimeout"
    return AnalysisReport(
        "AnalysisComplete" if error is None and committed else "Failed",
        error, stream.result(), process.returncode if process else None,
        written, committed, cleanup_ok,
    )
