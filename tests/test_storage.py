"""Storage failures and actual process death around durable job transitions."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import unittest

import pysam

from test_jobs import manage, prepare
from test_recovery import fixture
from genewire.jobs import clean_bam_job


def worker(root, data, origin, boundary="none", mode="error", action="recover"):
    process = subprocess.Popen([
        sys.executable, str(Path(__file__).with_name("_storage_worker.py")),
        str(root), origin, hashlib.sha256(data).hexdigest(), boundary, mode, action,
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        output, diagnostics = process.communicate(timeout=20)
    except BaseException:
        process.kill()
        process.communicate()
        raise
    return process.returncode, output, diagnostics


BOUNDARIES = [
    (point + "." + side, action)
    for point, action in (
        *(("source." + operation, "recover") for operation in ("file_sync", "rename", "dir_sync")),
        *(("result." + operation, "recover") for operation in ("file_sync", "dir_sync")),
        *(("receipt." + phase + "." + operation, "clean" if phase in ("Releasing", "Released") else "recover")
          for phase in ("Verified", "Ready", "Committed", "Releasing", "Released")
          for operation in ("file_sync", "replace", "dir_sync")),
        ("publication.link", "recover"), ("publication.parent_sync", "recover"),
        ("release.unlink", "clean"), ("release.dir_sync", "clean"),
    ) for side in ("before", "after")
]


@unittest.skipUnless(os.name == "posix", "Storage recovery currently requires POSIX")
class StorageTests(unittest.TestCase):
    def observe(self, **observation):
        self.__dict__.setdefault("storage_observations", []).append(observation)

    def assert_output(self, root):
        target = root / "output.bam"
        with pysam.AlignmentFile(str(target), "rb") as bam:
            self.assertEqual(sorted(record.query_name for record in bam), ["B", "C", "D"])
        self.assertEqual(target.read_bytes(), (root / "job/result.bam").read_bytes())
        self.assertEqual(target.stat().st_ino, (root / "job/result.bam").stat().st_ino)

    def fresh_retry(self, root, data, origin, seen):
        target = root / "output.bam"
        inode = target.stat().st_ino if target.exists() else None
        receipt = root / "job/state.json"
        phase = json.loads(receipt.read_text())["phase"] if receipt.exists() else "New"
        requests = len(seen)
        code, output, diagnostics = worker(root, data, origin, action="released" if phase in ("Releasing", "Released") else "recover")
        self.assertEqual(code, 0, (output, diagnostics))
        report = json.loads(output)["report"]
        self.assertEqual(report["state"], "Complete", report)
        self.assertTrue(report["sync_confirmed"])
        self.assertTrue(report["cleanup_complete"])
        if phase not in ("New", "Downloading"):
            self.assertEqual(len(seen), requests, "verified input was fetched again")
            self.assertIsNone(report["transport"])
        if inode is not None:
            self.assertEqual(target.stat().st_ino, inode)
        self.assert_output(root)
        return phase, report

    def matrix(self, mode):
        for boundary, action in BOUNDARIES:
            with self.subTest(boundary=boundary), fixture() as (root, data, origin, seen, c):
                if action == "clean":
                    prepare(root, data, c, "Committed")
                code, output, diagnostics = worker(root, data, origin, boundary, mode, action)
                if mode == "kill":
                    self.assertEqual(code, -signal.SIGKILL, (boundary, output, diagnostics))
                else:
                    self.assertEqual(code, 2, (boundary, output, diagnostics))
                    failure = json.loads(output)
                    self.assertTrue(failure["injected"])
                    self.assertEqual(failure["report"]["error"], "StorageFailure")
                    self.assertFalse(failure["report"]["sync_confirmed"])
                    self.assertFalse(failure["report"]["cleanup_complete"])
                    self.assertNotIn("diagnostic", output.decode())
                phase, report = self.fresh_retry(root, data, origin, seen)
                if action == "clean":
                    # Before the Releasing receipt replacement, a crash may
                    # leave Committed. Cleanup still finishes without decoding.
                    released = manage(clean_bam_job, root, data, c)
                    self.assertEqual(released.phase, "Released", released)
                    self.assertEqual(released.retained_source_bytes, 0)
                    count = len(seen)
                    _, retry = self.fresh_retry(root, data, origin, seen)
                    self.assertEqual(retry["phase"], "Released")
                    self.assertFalse(retry["source_reused"])
                    self.assertEqual(len(seen), count)
                self.observe(boundary=boundary, mode=mode, exit_code=code,
                             recovered_from=phase, recovered_to=report["phase"],
                             output_identity_preserved=True)

    def test_sigkill_storage_boundaries_recover_in_a_fresh_process(self):
        self.matrix("kill")

    def test_eio_storage_boundaries_recover_in_a_fresh_process(self):
        self.matrix("error")

    def test_short_write_enospc_flush_and_close_never_publish_partial_output(self):
        for kind in ("receipt", "source", "decoder"):
            for operation, mode in (("write", "short"), ("write", "enospc"), ("flush", "error"), ("close", "error")):
                boundary = kind + "." + operation
                with self.subTest(boundary=boundary, mode=mode), fixture() as (root, data, origin, seen, _):
                    code, output, diagnostics = worker(root, data, origin, boundary, mode)
                    self.assertEqual(code, 2, (output, diagnostics))
                    failure = json.loads(output)
                    self.assertTrue(failure["injected"], boundary)
                    self.assertIn(failure["report"]["error"], ("StorageFailure", "ConsumerFailed"))
                    self.assertFalse(failure["report"]["output_committed"])
                    self.assertFalse((root / "output.bam").exists())
                    phase, report = self.fresh_retry(root, data, origin, seen)
                    self.observe(boundary=boundary, mode=mode, exit_code=code,
                                 recovered_from=phase, recovered_to=report["phase"],
                                 incomplete_output_rejected=True)


if __name__ == "__main__":
    unittest.main()
