"""Cancellation must interrupt real work and preserve the publication boundary."""
from concurrent.futures import ThreadPoolExecutor
import gc
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import weakref

from genewire import Cancellation, GeneWireError
from genewire import recovery
from genewire.analysis import _supervise, filter_bam
from test_python_stream import client, service, write_bam
from test_recovery import fixture, run_job


@unittest.skipUnless(os.name == "posix", "BAM supervision/recovery requires POSIX")
class CancellationTests(unittest.TestCase):
    def observe(self, point, report):
        self.__dict__.setdefault("cancellation_observations", []).append({
            "point": point, "state": report.state, "error": report.error,
            "phase": getattr(report, "phase", "Analysis"),
            "output_committed": report.output_committed,
            "cleanup_complete": report.cleanup_complete,
        })

    def wait_marker(self, path, task):
        deadline = time.monotonic() + 10
        while not path.exists():
            if task.done():
                self.fail(f"worker ended before marker: {task.result()}")
            self.assertLess(time.monotonic(), deadline, "worker did not reach the gate")
            time.sleep(.01)

    def assert_complete(self, report):
        self.assertEqual(report.state, "Complete", report)
        self.assertTrue(report.output_committed)
        self.assertTrue(report.sync_confirmed)
        self.assertTrue(report.cleanup_complete)

    def test_precancelled_job_does_not_touch_disk_or_network(self):
        with fixture() as (root, data, _, seen, c):
            token = Cancellation()
            token.cancel()
            token.cancel()
            result = run_job(root, data, c, cancellation=token)
            self.assertEqual(result.error, "Cancelled")
            self.assertEqual(result.phase, "New")
            self.observe("BeforeStart", result)
            self.assertFalse((root / "job").exists())
            self.assertEqual(seen, [])
            self.assert_complete(run_job(root, data, c))

    def test_precancelled_direct_filter_closes_native_stream_without_output(self):
        with fixture() as (root, _, _, seen, c):
            token = Cancellation()
            token.cancel()
            stream = c.open("s", "chrSynthetic", 99, 101)
            result = filter_bam(stream, root / "out", "chrSynthetic", 99, 101, cancellation=token)
            self.assertEqual(result.error, "Cancelled")
            self.assertEqual(result.state, "Failed")
            self.assertTrue(result.cleanup_complete)
            self.assertTrue(result.transport.cleanup_complete)
            self.assertFalse(result.output_committed)
            self.assertEqual(seen, [])
            self.assertFalse(list(root.glob(".genewire-*")))
            self.observe("BeforeDirectFilterStart", result)

    def test_cancellation_interrupts_blocked_native_data_read_then_restarts_cleanly(self):
        import hashlib

        entered, release = threading.Event(), threading.Event()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fixture.bam"
            write_bam(source)
            data = source.read_bytes()
            token = Cancellation()
            with service(data, block_gate=(entered, release)) as (origin, seen, _), client(origin, timeout_ms=30000) as c:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    task = executor.submit(run_job, root, data, c, cancellation=token)
                    try:
                        self.assertTrue(entered.wait(10), "data request did not reach the server")
                        token.cancel()
                        result = task.result(timeout=3)
                    finally:
                        token.cancel()
                        release.set()
                self.assertEqual(result.error, "Cancelled", result)
                self.assertEqual(result.phase, "Downloading")
                self.observe("BlockedNativeRead", result)
                self.assertEqual(result.transport.error, "Cancelled")
                self.assertTrue(result.transport.cleanup_complete)
                self.assertFalse((root / "output.bam").exists())
                before = len(seen)
                again = run_job(root, data, c)
                self.assert_complete(again)
                self.assertFalse(again.source_reused)
                self.assertGreater(len(seen), before)
                self.assertEqual(hashlib.sha256((root / "job/source.bam").read_bytes()).digest(),
                                 hashlib.sha256(data).digest())

    def test_cancellation_after_verified_receipt_reuses_source_on_next_call(self):
        with fixture() as (root, data, _, seen, c):
            token = Cancellation()
            write = recovery._write_state

            def cancel_verified(workspace, state):
                write(workspace, state)
                if state["phase"] == "Verified":
                    token.cancel()

            with patch.object(recovery, "_write_state", side_effect=cancel_verified):
                result = run_job(root, data, c, cancellation=token)
            self.assertEqual(result.error, "Cancelled")
            self.assertEqual(result.phase, "Verified")
            self.observe("VerifiedReceipt", result)
            self.assertFalse((root / "output.bam").exists())
            before = len(seen)
            again = run_job(root, data, c)
            self.assert_complete(again)
            self.assertTrue(again.source_reused)
            self.assertEqual(len(seen), before)

    def test_cancellation_during_rehash_stops_before_decoder(self):
        with fixture() as (root, data, _, seen, c):
            with patch.object(recovery, "filter_bam", side_effect=GeneWireError("Cancelled")):
                self.assertEqual(run_job(root, data, c).phase, "Verified")
            token = Cancellation()
            entered, release = threading.Event(), threading.Event()
            original = recovery._private_open

            class PausedRead:
                def __init__(self, file):
                    self.file = file

                def __enter__(self):
                    return self

                def __exit__(self, *args):
                    self.file.close()

                def fileno(self):
                    return self.file.fileno()

                def read(self, size):
                    data = self.file.read(size)
                    entered.set()
                    if not release.wait(10):
                        raise OSError("test gate timed out")
                    return data

            def gated_open(path, **kwargs):
                file = original(path, **kwargs)
                return PausedRead(file) if path.name == "source.bam" else file

            before = len(seen)
            with patch.object(recovery, "_private_open", side_effect=gated_open), patch.object(recovery, "filter_bam") as decode:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    task = executor.submit(run_job, root, data, c, cancellation=token)
                    try:
                        self.assertTrue(entered.wait(10))
                        token.cancel()
                        release.set()
                        result = task.result(timeout=3)
                    finally:
                        release.set()
                decode.assert_not_called()
            self.assertEqual(result.error, "Cancelled")
            self.assertEqual(len(seen), before)
            self.observe("SourceHashRead", result)
            self.assert_complete(run_job(root, data, c))

    def test_cancelled_stalled_decoder_is_reaped_and_verified_input_is_retained(self):
        with fixture() as (root, data, _, seen, c):
            token = Cancellation()
            marker = root / "worker-started"
            processes = []
            popen = subprocess.Popen

            def capture(*args, **kwargs):
                process = popen(*args, **kwargs)
                processes.append(process)
                return process

            def stalled(stream, destination, *_region, **options):
                code = "import pathlib,sys,time; sys.stdin.buffer.read(); pathlib.Path(sys.argv[1]).touch(); time.sleep(30)"
                return _supervise(stream, [sys.executable, "-c", code, str(marker)], destination, **options)

            with patch.object(recovery, "filter_bam", side_effect=stalled), patch("genewire.analysis.subprocess.Popen", side_effect=capture):
                with ThreadPoolExecutor(max_workers=1) as executor:
                    task = executor.submit(run_job, root, data, c, cancellation=token)
                    try:
                        self.wait_marker(marker, task)
                        token.cancel()
                        result = task.result(timeout=3)
                    finally:
                        token.cancel()
            self.assertEqual(result.error, "Cancelled", result)
            self.assertEqual(result.phase, "Verified")
            self.observe("StalledDecoder", result)
            self.assertTrue(processes)
            self.assertTrue(all(p.poll() is not None for p in processes))
            self.assertFalse((root / "output.bam").exists())
            self.assertFalse(list((root / "job").glob("*.partial")))
            before = len(seen)
            self.assert_complete(run_job(root, data, c))
            self.assertEqual(len(seen), before)

    def test_child_that_closes_pipes_but_stays_alive_can_still_be_cancelled(self):
        with fixture() as (root, _, _, _, c):
            stream = c.open("s", "chrSynthetic", 99, 101)
            token = Cancellation()
            marker = root / "pipes-closed"
            code = "import os,pathlib,sys,time; sys.stdin.buffer.read(); os.close(1); os.close(2); pathlib.Path(sys.argv[1]).touch(); time.sleep(30)"
            with ThreadPoolExecutor(max_workers=1) as executor:
                task = executor.submit(_supervise, stream, [sys.executable, "-c", code, str(marker)], root / "out", cancellation=token)
                try:
                    self.wait_marker(marker, task)
                    token.cancel()
                    result = task.result(timeout=3)
                finally:
                    token.cancel()
            self.assertEqual(result.error, "Cancelled", result)
            self.assertTrue(result.cleanup_complete)
            self.observe("ChildWaitAfterPipesClosed", result)
            self.assertFalse(result.output_committed)
            self.assertIsNotNone(result.exit_code)

    def test_cancelled_job_preserves_incomplete_supervisor_cleanup_status(self):
        with fixture() as (root, data, _, _, c):
            failed = SimpleNamespace(state="Failed", error="Cancelled", cleanup_complete=False)
            with patch.object(recovery, "filter_bam", return_value=failed):
                result = run_job(root, data, c, cancellation=Cancellation())
            self.assertEqual(result.error, "Cancelled")
            self.assertFalse(result.cleanup_complete)
            self.assertTrue(result.transport.cleanup_complete)
            self.assertFalse(result.output_committed)
            self.observe("IncompleteSupervisorCleanup", result)

    def test_cancellation_before_publication_admission_preserves_ready_receipt(self):
        with fixture() as (root, data, _, seen, c):
            token = Cancellation()
            entered, release = threading.Event(), threading.Event()
            commit = token._commit
            commits = 0

            def gate(action):
                nonlocal commits
                commits += 1
                if commits == 2:  # private decoder result first, public output second
                    entered.set()
                    if not release.wait(10):
                        raise OSError("test gate timed out")
                return commit(action)

            with patch.object(token, "_commit", side_effect=gate):
                with ThreadPoolExecutor(max_workers=1) as executor:
                    task = executor.submit(run_job, root, data, c, cancellation=token)
                    try:
                        self.assertTrue(entered.wait(10))
                        token.cancel()
                        release.set()
                        result = task.result(timeout=3)
                    finally:
                        release.set()
                        token.cancel()
            self.assertEqual(result.error, "Cancelled", result)
            self.assertEqual(result.phase, "Ready")
            self.observe("BeforePublicationAdmission", result)
            self.assertFalse(result.output_committed)
            self.assertFalse((root / "output.bam").exists())
            before = len(seen)
            self.assert_complete(run_job(root, data, c))
            self.assertEqual(len(seen), before)

    def test_cancellation_after_publication_does_not_retract_valid_output(self):
        with fixture() as (root, data, _, seen, c):
            token = Cancellation()
            sync = recovery._sync_dir

            def cancel_after_link(path):
                if (root / "output.bam").exists():
                    token.cancel()
                sync(path)

            with patch.object(recovery, "_sync_dir", side_effect=cancel_after_link):
                result = run_job(root, data, c, cancellation=token)
            self.assert_complete(result)
            self.assertTrue(token.is_cancelled)
            self.observe("AfterPublicationAdmission", result)
            inode = (root / "output.bam").stat().st_ino
            before = len(seen)
            self.assert_complete(run_job(root, data, c))
            self.assertEqual((root / "output.bam").stat().st_ino, inode)
            self.assertEqual(len(seen), before)

    def test_completed_operations_release_native_cancellation_subscriptions(self):
        with fixture() as (root, data, _, _, c):
            token = Cancellation()
            references = []
            original = c.open

            def capture(*args):
                stream = original(*args)
                references.append(weakref.ref(stream))
                return stream

            with patch.object(c, "open", side_effect=capture):
                self.assert_complete(run_job(root, data, c, cancellation=token))
            gc.collect()
            self.assertTrue(references)
            self.assertTrue(all(reference() is None for reference in references))
            token.cancel()

    def test_invalid_cancellation_does_not_alter_stream_or_workspace(self):
        with fixture() as (root, data, _, seen, c), c.open("s", "chrSynthetic", 99, 101) as stream:
            with self.assertRaisesRegex(GeneWireError, "InvalidQuery"):
                run_job(root, data, c, cancellation=object())
            with self.assertRaisesRegex(GeneWireError, "InvalidQuery"):
                filter_bam(stream, root / "out", "chrSynthetic", 99, 101, cancellation=object())
            self.assertEqual(stream.result().state, "New")
            self.assertFalse((root / "job").exists())
            self.assertEqual(seen, [])


if __name__ == "__main__":
    unittest.main()
