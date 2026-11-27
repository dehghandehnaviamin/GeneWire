"""Pinned BAM job recovery, actual process death and filesystem failure gates."""
from contextlib import contextmanager
import errno
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pysam

from genewire import GeneWireError
from genewire import recovery
from test_python_stream import client, service, write_bam


@contextmanager
def fixture(payload=None):
    with TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "fixture.bam"
        write_bam(source)
        data = source.read_bytes() if payload is None else payload
        with service(data) as (origin, seen, _), client(origin) as c:
            yield root, data, origin, seen, c


def run_job(root, data, c, **kwargs):
    options = dict(expected_sha256=hashlib.sha256(data).hexdigest())
    options.update(kwargs)
    return recovery.recover_bam(c, "s", "chrSynthetic", 99, 101,
                               root / "output.bam", root / "job", **options)


def child_job(root, data, origin, fault, region=(99, 101)):
    # Run a fresh native client; never inherit a Rust runtime across fork.
    code = '''
import os, signal, sys
from unittest.mock import patch
from pathlib import Path
from genewire import Client, Destination, recovery
root, origin, digest, fault, start, end = sys.argv[1:]
root = Path(root)
start, end = int(start), int(end)
original_state = recovery._write_state
original_hash = recovery._hash_file
original_decode = recovery.filter_bam
original_link = os.link

def die():
    os.kill(os.getpid(), signal.SIGKILL)

def write_state(job, state):
    original_state(job, state)
    if state['phase'] == fault:
        die()

def hash_file(path, *args, **kwargs):
    if fault == 'Decoded' and path.name == 'result.bam':
        die()
    return original_hash(path, *args, **kwargs)

def decode(*args, **kwargs):
    if fault == 'Decoding':
        # Actual existing supervisor with a controlled pipe-writing worker.
        from genewire.analysis import _supervise
        p = root / 'decoder-started'
        worker = chr(10).join(['import os,pathlib,sys,time', 'pathlib.Path(sys.argv[1]).touch()', 'sys.stdin.buffer.read()', 'while True:', ' os.write(1, bytes([120])); time.sleep(.01)'])
        cmd = [sys.executable, '-c', worker, str(p)]
        return _supervise(args[0], cmd, args[1], **kwargs)
    return original_decode(*args, **kwargs)

def link(source, target, **kwargs):
    original_link(source, target, **kwargs)
    if fault == 'Linked' and Path(target).name == 'output.bam':
        die()

with Client(origin + '/reads/', {origin: Destination(['127.0.0.1'])}, loopback_http_for_tests=True) as c:
    if fault == 'Partial':
        original_read = c.open
        def open_stream(*args):
            stream = original_read(*args)
            read = stream.read_chunk
            def interrupted(size):
                data = read(size)
                if not data:
                    die()
                return data
            stream.read_chunk = interrupted
            return stream
        c.open = open_stream
    with patch.object(recovery, '_write_state', side_effect=write_state), patch.object(recovery, '_hash_file', side_effect=hash_file), patch.object(recovery, 'filter_bam', side_effect=decode), patch('os.link', side_effect=link):
        report = recovery.recover_bam(c, 's', 'chrSynthetic', start, end, root / 'output.bam', root / 'job', expected_sha256=digest)
        raise SystemExit(0 if report.state == 'Complete' else 2)
'''
    return subprocess.Popen([sys.executable, "-c", code, str(root), origin,
                             hashlib.sha256(data).hexdigest(), fault, *map(str, region)],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)


@unittest.skipUnless(os.name == "posix", "Recovery currently requires POSIX")
class RecoveryTests(unittest.TestCase):
    def assert_output(self, root):
        with pysam.AlignmentFile(str(root / "output.bam"), "rb") as bam:
            self.assertEqual(sorted(r.query_name for r in bam), ["B", "C", "D"])

    def kill_at(self, root, data, origin, boundary, region=(99, 101)):
        process = child_job(root, data, origin, boundary, region)
        try:
            _, diagnostics = process.communicate(timeout=15)
        except BaseException:
            process.kill()
            process.communicate()
            raise
        self.assertEqual(process.returncode, -signal.SIGKILL, diagnostics.decode())
        self.__dict__.setdefault("crash_observations", []).append(
            {"boundary": boundary, "exit_code": process.returncode})

    def test_success_receipt_retry_is_network_free_and_preserves_output_inode(self):
        with fixture() as (root, data, _, seen, c):
            result = run_job(root, data, c)
            self.assertEqual(result.state, "Complete", result)
            self.assertFalse(result.source_reused)
            self.assertTrue(result.sync_confirmed)
            self.assertEqual(result.transport.state, "TransportComplete")
            inode = (root / "output.bam").stat().st_ino
            count = len(seen)
            again = run_job(root, data, c)
            self.assertEqual(again.state, "Complete", again)
            self.assertTrue(again.source_reused)
            self.assertIsNone(again.transport)
            self.assertEqual(len(seen), count)
            self.assertEqual((root / "output.bam").stat().st_ino, inode)
            self.assert_output(root)
            self.assertEqual((root / "job").stat().st_mode & 0o777, 0o700)
            for path in (root / "job").iterdir():
                self.assertEqual(path.stat().st_mode & 0o077, 0)
            receipt = (root / "job/state.json").read_text()
            self.assertNotIn("chrSynthetic", receipt)
            self.assertNotIn(str(root), receipt)
            self.assertNotIn("127.0.0.1", receipt)

    def test_sigkill_boundaries_recover_without_splicing_or_double_publication(self):
        for boundary in ("Downloading", "Partial", "Verified", "Decoded", "Ready", "Linked", "Committed"):
            with self.subTest(boundary=boundary), fixture() as (root, data, origin, seen, c):
                self.kill_at(root, data, origin, boundary)
                before = len(seen)
                result = run_job(root, data, c)
                self.assertEqual(result.state, "Complete", result)
                if boundary in ("Downloading", "Partial"):
                    self.assertGreater(len(seen), before)
                    self.assertFalse(result.source_reused)
                else:
                    self.assertEqual(len(seen), before)
                    self.assertTrue(result.source_reused)
                self.assert_output(root)
                self.assertFalse(list((root / "job").glob("*.partial")))

    def test_verified_source_recovery_matches_all_five_tiny_truth_cases(self):
        cases = [(0, 1, ["A"]), (99, 100, ["B", "D"]), (100, 101, ["C", "D"]),
                 (499, 500, []), (99, 101, ["B", "C", "D"])]
        for i, (start, end, expected) in enumerate(cases, 1):
            with self.subTest(case=f"Q{i}"), fixture() as (root, data, origin, seen, c):
                self.kill_at(root, data, origin, "Verified", (start, end))
                before = len(seen)
                result = recovery.recover_bam(
                    c, "s", "chrSynthetic", start, end, root / "output.bam", root / "job",
                    expected_sha256=hashlib.sha256(data).hexdigest(),
                )
                self.assertEqual(result.state, "Complete", result)
                self.assertEqual(len(seen), before)
                with pysam.AlignmentFile(str(root / "output.bam"), "rb") as bam:
                    observed = sorted(r.query_name for r in bam)
                self.assertEqual(observed, expected)
                self.__dict__.setdefault("truth_observations", []).append(
                    {"case": f"Q{i}", "expected": expected, "observed": observed,
                     "new_network_requests": len(seen)-before})

    def test_killed_supervisor_during_decode_restarts_from_verified_source(self):
        import time

        with fixture() as (root, data, origin, seen, c):
            process = child_job(root, data, origin, "Decoding")
            try:
                deadline = time.monotonic() + 10
                while not (root / "decoder-started").exists():
                    if process.poll() is not None:
                        self.fail("decoder did not start: " + process.communicate()[1].decode())
                    if time.monotonic() > deadline:
                        self.fail("decoder did not start within budget")
                    time.sleep(.01)
                process.kill()
                process.communicate(timeout=5)
                self.assertEqual(process.returncode, -signal.SIGKILL)
                self.__dict__.setdefault("crash_observations", []).append(
                    {"boundary": "Decoding", "exit_code": process.returncode})
                before = len(seen)
                result = run_job(root, data, c)
                self.assertEqual(result.state, "Complete", result)
                self.assertEqual(len(seen), before)
                self.assert_output(root)
            finally:
                if process.poll() is None:
                    process.kill()
                    process.communicate()

    def test_wrong_expected_digest_never_reaches_decode_or_output(self):
        with fixture() as (root, data, _, _, c), patch.object(recovery, "filter_bam") as decode:
            result = run_job(root, data, c, expected_sha256="0" * 64)
            self.assertEqual(result.error, "IntegrityFailed")
            self.assertFalse(result.output_committed)
            decode.assert_not_called()
            self.assertFalse((root / "output.bam").exists())

    def test_decodable_source_pin_is_not_a_decode_success_claim(self):
        with fixture(b"not a BAM") as (root, data, _, _, c):
            result = run_job(root, data, c)
            self.assertEqual(result.error, "ConsumerFailed")
            self.assertEqual(result.phase, "Verified")
            self.assertFalse(result.output_committed)

    def test_changed_or_truncated_verified_source_is_rejected_without_network(self):
        for contents in (b"", b"corrupt"):
            with self.subTest(contents=contents), fixture() as (root, data, origin, seen, c):
                self.kill_at(root, data, origin, "Verified")
                (root / "job/source.bam").write_bytes(contents)
                before = len(seen)
                result = run_job(root, data, c)
                self.assertEqual(result.error, "IntegrityFailed")
                self.assertEqual(len(seen), before)
                self.assertFalse((root / "output.bam").exists())

    def test_ready_result_corruption_and_unrelated_output_are_rejected(self):
        for fault in ("corrupt", "conflict", "identical-copy", "symlink"):
            with self.subTest(fault=fault), fixture() as (root, data, origin, seen, c):
                self.kill_at(root, data, origin, "Ready")
                if fault == "corrupt":
                    (root / "job/result.bam").write_bytes(b"bad")
                elif fault == "symlink":
                    (root / "output.bam").symlink_to(root / "job/result.bam")
                else:
                    (root / "output.bam").write_bytes(
                        (root / "job/result.bam").read_bytes() if fault == "identical-copy" else b"keep")
                before = len(seen)
                result = run_job(root, data, c)
                self.assertEqual(result.error, "IntegrityFailed" if fault == "corrupt" else "DestinationExists")
                self.assertFalse(result.output_committed)
                self.assertEqual(len(seen), before)

    def test_stale_query_digest_target_or_limits_preserve_original_receipt(self):
        with fixture() as (root, data, origin, seen, c):
            self.kill_at(root, data, origin, "Verified")
            path = root / "job/state.json"
            original = path.read_bytes()
            before = len(seen)
            for change in (dict(expected_sha256="0"*64), dict(max_output_bytes=123)):
                self.assertEqual(run_job(root, data, c, **change).error, "CheckpointMismatch")
            result = recovery.recover_bam(c, "other", "chrSynthetic", 99, 101,
                                         root / "output.bam", root / "job",
                                         expected_sha256=hashlib.sha256(data).hexdigest())
            self.assertEqual(result.error, "CheckpointMismatch")
            result = recovery.recover_bam(c, "s", "chrSynthetic", 99, 101,
                                         root / "different-output.bam", root / "job",
                                         expected_sha256=hashlib.sha256(data).hexdigest())
            self.assertEqual(result.error, "CheckpointMismatch")
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(len(seen), before)

    def test_malformed_oversized_duplicate_and_unknown_version_receipts_fail_closed(self):
        for fault in ("json", "large", "duplicate", "version", "boolean", "unknown-phase"):
            with self.subTest(fault=fault), fixture() as (root, data, origin, seen, c):
                self.kill_at(root, data, origin, "Verified")
                path = root / "job/state.json"
                state = json.loads(path.read_text())
                if fault == "version":state["version"] = 2
                if fault == "boolean":state["source_bytes"] = True
                if fault == "unknown-phase":state["phase"] = "future"
                content = {"json": "{", "large": " "*4097, "duplicate": '{"version":1,"version":1}'}.get(fault, json.dumps(state))
                path.write_text(content)
                before = len(seen)
                result = run_job(root, data, c)
                self.assertEqual(result.error, "CheckpointInvalid", result)
                self.assertEqual(len(seen), before)
                self.assertEqual(path.read_text(), content)

    def test_symlink_workspace_and_source_never_follow_or_modify_target(self):
        with fixture() as (root, data, _, seen, c):
            other = root / "other"
            other.mkdir(mode=0o700)
            (root / "job").symlink_to(other, target_is_directory=True)
            result = run_job(root, data, c)
            self.assertEqual(result.error, "CheckpointInvalid")
            self.assertEqual(list(other.iterdir()), [])
            self.assertEqual(seen, [])
        with fixture() as (root, data, origin, seen, c):
            self.kill_at(root, data, origin, "Verified")
            (root / "job/source.bam").unlink()
            keep = root / "keep"
            keep.write_bytes(b"preserve")
            keep.chmod(0o600)
            (root / "job/source.bam").symlink_to(keep)
            result = run_job(root, data, c)
            self.assertEqual(result.state, "Failed")
            self.assertEqual(keep.read_bytes(), b"preserve")

    def test_lock_contention_between_processes_is_nonblocking_and_network_free(self):
        with fixture() as (root, data, origin, seen, c):
            self.kill_at(root, data, origin, "Verified")
            import fcntl
            with open(root / "job/lock", "r+b") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                process = child_job(root, data, origin, "none")
                _, diagnostics = process.communicate(timeout=5)
                self.assertEqual(process.returncode, 2, diagnostics.decode())
                before = len(seen)
                self.assertEqual(run_job(root, data, c).error, "RecoveryBusy")
                self.assertEqual(len(seen), before)
            self.assertEqual(run_job(root, data, c).state, "Complete")

    def test_input_and_output_budgets_leave_no_published_output(self):
        for options in (dict(max_source_bytes=8), dict(max_output_bytes=8)):
            with self.subTest(options=options), fixture() as (root, data, _, _, c):
                result = run_job(root, data, c, **options)
                self.assertEqual(result.error, "ResourceLimit", result)
                self.assertFalse((root / "output.bam").exists())

    def test_interrupted_or_failed_download_is_discarded_on_next_attempt(self):
        for failure in (GeneWireError("TransportFailed"), KeyboardInterrupt()):
            with self.subTest(failure=type(failure).__name__), fixture() as (root, data, _, seen, c):
                original = c.open

                def failing_open(*args):
                    stream = original(*args)
                    read = stream.read_chunk
                    calls = 0

                    def fail_read(_size):
                        nonlocal calls
                        calls += 1
                        if calls == 1:
                            return read(8)
                        raise failure

                    stream.read_chunk = fail_read
                    return stream

                with patch.object(c, "open", side_effect=failing_open):
                    if isinstance(failure, KeyboardInterrupt):
                        with self.assertRaises(KeyboardInterrupt):
                            run_job(root, data, c)
                    else:
                        result = run_job(root, data, c)
                        self.assertEqual(result.error, "TransportFailed")
                self.assertEqual(json.loads((root / "job/state.json").read_text())["phase"], "Downloading")
                self.assertFalse((root / "output.bam").exists())
                before = len(seen)
                self.assertEqual(run_job(root, data, c).state, "Complete")
                self.assertGreater(len(seen), before)
                self.assert_output(root)

    def test_receipt_write_failure_after_decode_keeps_verified_source_recoverable(self):
        with fixture() as (root, data, _, seen, c):
            original = recovery._write_state

            def full(workspace, state):
                if state["phase"] == "Ready":
                    raise OSError(errno.ENOSPC, "sensitive diagnostic")
                return original(workspace, state)

            with patch.object(recovery, "_write_state", side_effect=full):
                result = run_job(root, data, c)
            self.assertEqual(result.error, "StorageFailure")
            self.assertEqual(result.phase, "Verified")
            self.assertFalse(result.output_committed)
            before = len(seen)
            self.assertEqual(run_job(root, data, c).state, "Complete")
            self.assertEqual(len(seen), before)

    def test_unknown_workspace_content_and_removed_committed_output_fail_closed(self):
        with fixture() as (root, data, _, seen, c):
            self.assertEqual(run_job(root, data, c).state, "Complete")
            before = len(seen)
            (root / "job/unrelated").write_bytes(b"keep")
            self.assertEqual(run_job(root, data, c).error, "CheckpointInvalid")
            self.assertEqual((root / "job/unrelated").read_bytes(), b"keep")
            (root / "job/unrelated").unlink()
            (root / "output.bam").unlink()
            self.assertEqual(run_job(root, data, c).error, "CheckpointInvalid")
            self.assertEqual(len(seen), before)

    def test_disk_full_and_prepublication_sync_failure_do_not_publish(self):
        for fault in ("state-write", "source-write", "fsync"):
            with self.subTest(fault=fault), fixture() as (root, data, _, _, c):
                original = os.open

                def full(path, flags, *args, **kwargs):
                    if Path(path).name == ("state.tmp" if fault == "state-write" else "source.partial"):
                        raise OSError(errno.ENOSPC, "sensitive diagnostic")
                    return original(path, flags, *args, **kwargs)

                with patch("os.fsync", side_effect=OSError("sensitive diagnostic")) if fault == "fsync" else patch("os.open", side_effect=full):
                    result = run_job(root, data, c)
                self.assertEqual(result.error, "StorageFailure")
                self.assertFalse(result.output_committed)
                self.assertFalse(result.sync_confirmed)
                self.assertFalse(result.cleanup_complete)
                self.assertNotIn("sensitive", repr(result))
                self.assertFalse((root / "output.bam").exists())

    def test_postlink_sync_failure_reports_visible_output_and_recovers_receipt(self):
        with fixture() as (root, data, origin, seen, c):
            self.kill_at(root, data, origin, "Ready")
            original = recovery._sync_dir

            def fail_after_link(path):
                if (root / "output.bam").exists():
                    raise OSError(errno.EIO, "sensitive sync failure")
                original(path)

            with patch.object(recovery, "_sync_dir", side_effect=fail_after_link):
                result = run_job(root, data, c)
            self.assertEqual(result.error, "StorageFailure")
            self.assertTrue(result.output_committed)
            self.assertFalse(result.sync_confirmed)
            self.assertEqual(result.phase, "Ready")
            inode = (root / "output.bam").stat().st_ino
            before = len(seen)
            self.assertEqual(run_job(root, data, c).state, "Complete")
            self.assertEqual((root / "output.bam").stat().st_ino, inode)
            self.assertEqual(len(seen), before)

    def test_invalid_parameters_do_not_touch_disk_or_network(self):
        with fixture() as (root, data, _, seen, c):
            for options in (dict(expected_sha256="wrong"), dict(max_source_bytes=True),
                            dict(max_output_bytes=0), dict(timeout_s=float("nan"))):
                with self.assertRaisesRegex(GeneWireError, "InvalidQuery"):
                    run_job(root, data, c, **options)
            self.assertFalse((root / "job").exists())
            self.assertEqual(seen, [])


if __name__ == "__main__":
    unittest.main()
