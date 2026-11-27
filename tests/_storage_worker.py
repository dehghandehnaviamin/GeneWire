"""Fresh-process fault instrumentation; never imported by the library."""
from contextlib import ExitStack
from dataclasses import asdict
import errno
import json
import os
from pathlib import Path
import signal
import sys
from unittest.mock import patch

from genewire import Client, Destination, recovery
from genewire.jobs import clean_bam_job


def main():
    directory, origin, digest, boundary, mode, action = sys.argv[1:]
    root = Path(directory).resolve()
    receipt_phase = None
    stage = None
    fired = False
    descriptors = {}
    original_open, original_fdopen = os.open, os.fdopen
    original_sync, original_replace, original_link, original_unlink = os.fsync, os.replace, os.link, os.unlink
    original_state, original_dir, original_decode = recovery._write_state, recovery._sync_dir, recovery.filter_bam

    def event(point):
        nonlocal fired
        if point != boundary or fired:
            return
        fired = True
        if mode == "kill":
            os.kill(os.getpid(), signal.SIGKILL)
        raise OSError(errno.EIO, "injected storage diagnostic")

    def surround(point, operation):
        event(point + ".before")
        result = operation()
        event(point + ".after")
        return result

    def open_file(path, flags, *args, **kwargs):
        fd = original_open(path, flags, *args, **kwargs)
        descriptors[fd] = Path(path).name
        return fd

    def state(job, value):
        nonlocal receipt_phase
        receipt_phase = value["phase"]
        try:
            return original_state(job, value)
        finally:
            receipt_phase = None

    def sync(fd):
        name = descriptors.get(fd)
        if name == "state.tmp" and receipt_phase:
            point = "receipt." + receipt_phase + ".file_sync"
        elif name == "source.partial":
            point = "source.file_sync"
        elif name == "result.bam":
            point = "result.file_sync"
        else:
            return original_sync(fd)
        return surround(point, lambda: original_sync(fd))

    def replace(source, target):
        nonlocal stage
        if Path(source).name == "state.tmp":
            point = "receipt." + receipt_phase + ".replace"
        elif Path(source).name == "source.partial":
            point = "source.rename"
            stage = "source"
        else:
            return original_replace(source, target)
        return surround(point, lambda: original_replace(source, target))

    def decode(*args, **kwargs):
        nonlocal stage
        if action == "released":
            raise AssertionError("Released job attempted decoding")
        result = original_decode(*args, **kwargs)
        stage = "result"
        return result

    def sync_dir(path):
        if receipt_phase:
            point = "receipt." + receipt_phase + ".dir_sync"
        elif Path(path) == root and (root / "output.bam").exists():
            point = "publication.parent_sync"
        elif action == "clean":
            point = "release.dir_sync"
        elif stage:
            point = stage + ".dir_sync"
        else:
            return original_dir(path)
        return surround(point, lambda: original_dir(path))

    def link(source, target, **kwargs):
        if Path(target).name == "output.bam":
            return surround("publication.link", lambda: original_link(source, target, **kwargs))
        return original_link(source, target, **kwargs)

    def unlink(path, *args, **kwargs):
        if action == "clean" and Path(path).name == "source.bam":
            return surround("release.unlink", lambda: original_unlink(path, *args, **kwargs))
        return original_unlink(path, *args, **kwargs)

    # File-operation failures include errors reported by flush and close, plus
    # actual partial writes. Readers and lock files stay ordinary file objects.
    class FaultFile:
        def __init__(self, file, kind):
            self.file, self.kind = file, kind

        def __getattr__(self, name):
            return getattr(self.file, name)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.close()

        def write(self, payload):
            nonlocal fired
            point = self.kind + ".write"
            if boundary == point and not fired:
                fired = True
                if mode == "short":
                    return self.file.write(payload[:max(0, len(payload) - 1)])
                raise OSError(errno.ENOSPC, "injected storage diagnostic")
            return self.file.write(payload)

        def flush(self):
            event(self.kind + ".flush")
            return self.file.flush()

        def close(self):
            self.file.close()
            event(self.kind + ".close")

    def fdopen(fd, mode="r", *args, **kwargs):
        file = original_fdopen(fd, mode, *args, **kwargs)
        name = descriptors.get(fd, "")
        kind = "receipt" if name == "state.tmp" else "source" if name == "source.partial" else "decoder" if name.startswith(".genewire-") else None
        return FaultFile(file, kind) if kind and mode == "wb" else file

    with Client(origin + "/reads/", {origin: Destination(["127.0.0.1"])}, loopback_http_for_tests=True) as client:
        with ExitStack() as stack:
            if action == "released":
                stack.enter_context(patch.object(client, "open", side_effect=AssertionError("Released job attempted network")))
            for obj, name, function in (
                (os, "open", open_file), (os, "fdopen", fdopen), (os, "fsync", sync),
                (os, "replace", replace), (os, "link", link), (os, "unlink", unlink),
                (recovery, "_write_state", state), (recovery, "_sync_dir", sync_dir),
                (recovery, "filter_bam", decode),
            ):
                stack.enter_context(patch.object(obj, name, side_effect=function))
            operation = clean_bam_job if action == "clean" else recovery.recover_bam
            report = operation(client, "s", "chrSynthetic", 99, 101,
                               root / "output.bam", root / "job", expected_sha256=digest)
        print(json.dumps({"injected": fired, "report": asdict(report)}))
        return 0 if report.error is None else 2


if __name__ == "__main__":
    raise SystemExit(main())
