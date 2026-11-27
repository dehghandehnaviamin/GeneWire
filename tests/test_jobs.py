"""Read-only workspace inspection and recoverable, output-preserving cleanup."""
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest
from unittest.mock import patch

from genewire import Cancellation, GeneWireError
from genewire.jobs import clean_bam_job, inspect_bam_job
from genewire import recovery as store
from test_recovery import fixture, run_job
from test_python_stream import client, service, write_bam


def manage(operation, root, data, c, **options):
    arguments = dict(expected_sha256=hashlib.sha256(data).hexdigest())
    arguments.update(options)
    return operation(c, "s", "chrSynthetic", 99, 101, root / "output.bam", root / "job", **arguments)


def prepare(root, data, c, phase):
    if phase == "Committed":
        report = run_job(root, data, c)
        assert report.state == "Complete", report
        return
    original = store._write_state

    def stop_at(workspace, state):
        original(workspace, state)
        if state["phase"] == phase:
            raise GeneWireError("Cancelled")

    with patch.object(store, "_write_state", side_effect=stop_at):
        report = run_job(root, data, c)
    assert report.error == "Cancelled", report
    assert json.loads((root / "job/state.json").read_text())["phase"] == phase


def private_file(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as file:
        file.write(data)


@unittest.skipUnless(os.name == "posix", "Workspace management currently requires POSIX")
class WorkspaceTests(unittest.TestCase):
    def observe(self, point, report):
        self.__dict__.setdefault("workspace_observations", []).append({
            "point": point, "state": report.state, "error": report.error,
            "phase": report.phase, "retained_source_bytes": report.retained_source_bytes,
            "output_verified": report.output_verified, "removed_files": list(report.removed_files),
        })

    def test_inspection_is_read_only_and_network_free(self):
        with fixture() as (root, data, _, seen, c):
            prepare(root, data, c, "Committed")
            before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_ino)
                      for p in (root / "job").iterdir()}
            requests = len(seen)
            original_open = os.open

            def no_create(path, flags, *args, **options):
                self.assertFalse(flags & os.O_CREAT, "inspection tried to create a file")
                return original_open(path, flags, *args, **options)

            with patch("os.open", side_effect=no_create), patch.object(store, "_sync_dir") as sync, patch.object(c, "open") as network:
                report = manage(inspect_bam_job, root, data, c)
                sync.assert_not_called()
                network.assert_not_called()
            self.assertEqual(report.state, "Inspected", report)
            self.assertTrue(report.output_verified)
            self.assertTrue(report.result_verified)
            self.assertFalse(report.source_verified)
            self.assertFalse(report.sync_confirmed)
            self.assertEqual(report.removed_files, ())
            after = {p.name: (p.read_bytes(), p.stat().st_mtime_ns, p.stat().st_ino)
                     for p in (root / "job").iterdir()}
            self.assertEqual(before, after)
            self.assertEqual(len(seen), requests)
            self.observe("ReadOnlyInspection", report)

    def test_missing_or_empty_workspace_is_not_created_by_management(self):
        with fixture() as (root, data, _, seen, c):
            for operation in (inspect_bam_job, clean_bam_job):
                report = manage(operation, root, data, c)
                self.assertEqual(report.error, "CheckpointMissing")
                self.assertFalse((root / "job").exists())
            (root / "job").mkdir(mode=0o700)
            for operation in (inspect_bam_job, clean_bam_job):
                self.assertEqual(manage(operation, root, data, c).error, "CheckpointInvalid")
                self.assertEqual(list((root / "job").iterdir()), [])
            self.assertEqual(seen, [])
            self.assertEqual(run_job(root, data, c).state, "Complete")

    def test_cleanup_releases_source_but_keeps_output_lock_and_idempotent_receipt(self):
        with fixture() as (root, data, _, seen, c):
            prepare(root, data, c, "Committed")
            target = root / "output.bam"
            original, inode = target.read_bytes(), target.stat().st_ino
            lock_inode = (root / "job/lock").stat().st_ino
            before = len(seen)
            with patch.object(c, "open") as network:
                report = manage(clean_bam_job, root, data, c)
                self.assertEqual(report.state, "Cleaned", report)
                self.assertEqual(report.phase, "Released")
                self.assertEqual(report.retained_source_bytes, 0)
                self.assertEqual(report.removed_files, ("source.bam",))
                self.assertTrue(report.output_verified)
                self.assertTrue(report.sync_confirmed)
                self.assertEqual({p.name for p in (root / "job").iterdir()}, {"lock", "state.json", "result.bam"})
                repeated = manage(clean_bam_job, root, data, c)
                self.assertEqual(repeated.state, "Cleaned", repeated)
                self.assertEqual(repeated.removed_files, ())
                recovered = run_job(root, data, c)
                self.assertEqual(recovered.state, "Complete", recovered)
                self.assertEqual(recovered.phase, "Released")
                self.assertFalse(recovered.source_reused)
                self.assertIsNone(recovered.transport)
                network.assert_not_called()
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(target.stat().st_ino, inode)
            self.assertEqual((root / "job/result.bam").stat().st_ino, inode)
            self.assertEqual((root / "job/lock").stat().st_ino, lock_inode)
            self.assertEqual(len(seen), before)
            self.observe("ReleasedOutputPreserved", report)

    def test_committed_cleanup_does_not_require_redundant_source_content(self):
        for change in ("corrupt", "missing"):
            with self.subTest(change=change), fixture() as (root, data, _, _, c):
                prepare(root, data, c, "Committed")
                source = root / "job/source.bam"
                source.write_bytes(b"obsolete") if change == "corrupt" else source.unlink()
                original = (root / "output.bam").read_bytes()
                result = manage(clean_bam_job, root, data, c)
                self.assertEqual(result.state, "Cleaned", result)
                self.assertEqual(result.phase, "Released")
                self.assertEqual((root / "output.bam").read_bytes(), original)
                self.assertEqual(run_job(root, data, c).state, "Complete")

    def test_committed_recovery_needs_only_the_accepted_output(self):
        for change in ("corrupt", "missing"):
            with self.subTest(change=change), fixture() as (root, data, _, seen, c):
                prepare(root, data, c, "Committed")
                source = root / "job/source.bam"
                source.write_bytes(b"obsolete") if change == "corrupt" else source.unlink()
                inode = (root / "output.bam").stat().st_ino
                before = len(seen)
                with patch.object(c, "open", side_effect=AssertionError("unexpected network")), patch.object(store, "filter_bam", side_effect=AssertionError("unexpected decoder")):
                    report = run_job(root, data, c)
                self.assertEqual(report.state, "Complete", report)
                self.assertFalse(report.source_reused)
                self.assertEqual(report.phase, "Committed")
                self.assertEqual((root / "output.bam").stat().st_ino, inode)
                self.assertEqual(len(seen), before)
                self.observe("CommittedWithoutRedundantInput", manage(inspect_bam_job, root, data, c))

    def test_committed_recovery_still_rejects_unsafe_redundant_source(self):
        with fixture() as (root, data, _, seen, c):
            prepare(root, data, c, "Committed")
            source = root / "job/source.bam"
            source.unlink()
            source.symlink_to(root / "fixture.bam")
            before = len(seen)
            report = run_job(root, data, c)
            self.assertEqual(report.state, "Failed", report)
            self.assertEqual(len(seen), before)

    def test_cleanup_preserves_verified_source_and_ready_result(self):
        for phase in ("Downloading", "Verified", "Ready"):
            with self.subTest(phase=phase), fixture() as (root, data, _, seen, c):
                prepare(root, data, c, phase)
                private_file(root / "job/source.partial", b"partial")
                private_file(root / "job/.genewire-abandoned.partial", b"decoder partial")
                if phase == "Verified":
                    os.link(root / "job/.genewire-abandoned.partial", root / "job/result.bam")
                if phase == "Downloading":
                    private_file(root / "job/result.bam", b"partial result")
                info = manage(inspect_bam_job, root, data, c)
                self.assertEqual(info.state, "Inspected", info)
                self.assertEqual(info.phase, phase)
                result = manage(clean_bam_job, root, data, c)
                self.assertEqual(result.state, "Cleaned", result)
                self.assertEqual(result.phase, phase)
                self.assertFalse((root / "output.bam").exists())
                self.assertFalse(list((root / "job").glob("*.partial")))
                self.assertEqual((root / "job/source.bam").exists(), phase != "Downloading")
                self.assertEqual((root / "job/result.bam").exists(), phase == "Ready")
                before = len(seen)
                self.assertEqual(run_job(root, data, c).state, "Complete")
                if phase != "Downloading":
                    self.assertEqual(len(seen), before)
                self.observe(f"Preserved{phase}", result)

    def test_ready_published_alias_is_preserved_without_advancing_the_receipt(self):
        with fixture() as (root, data, _, _, c):
            prepare(root, data, c, "Ready")
            os.link(root / "job/result.bam", root / "output.bam")
            inode = (root / "output.bam").stat().st_ino
            report = manage(clean_bam_job, root, data, c)
            self.assertEqual(report.state, "Cleaned", report)
            self.assertEqual(report.phase, "Ready")
            self.assertTrue(report.output_verified)
            self.assertTrue((root / "job/source.bam").exists())
            self.assertEqual(run_job(root, data, c).state, "Complete")
            self.assertEqual((root / "output.bam").stat().st_ino, inode)

    def test_cleanup_preflight_rejects_foreign_or_unsafe_entries_without_deletion(self):
        for fault in ("foreign", "symlink", "permissions", "fifo"):
            with self.subTest(fault=fault), fixture() as (root, data, _, _, c):
                prepare(root, data, c, "Verified")
                private_file(root / "job/source.partial", b"keep partial")
                keep = root / "keep"
                private_file(keep, b"keep external")
                bad = root / "job/.genewire-unsafe.partial"
                if fault == "foreign":
                    private_file(root / "job/unrelated", b"keep foreign")
                elif fault == "symlink":
                    bad.symlink_to(keep)
                elif fault == "permissions":
                    private_file(bad, b"not private")
                    bad.chmod(0o640)
                else:
                    os.mkfifo(bad, 0o600)
                report = manage(clean_bam_job, root, data, c)
                self.assertEqual(report.state, "Failed", report)
                self.assertEqual(report.removed_files, ())
                self.assertEqual((root / "job/source.partial").read_bytes(), b"keep partial")
                self.assertEqual(keep.read_bytes(), b"keep external")
                self.assertTrue((root / "job/source.bam").exists())

    def test_mismatched_or_invalid_receipt_and_conflicting_output_never_clean(self):
        for fault in ("query", "receipt", "destination", "source"):
            with self.subTest(fault=fault), fixture() as (root, data, _, seen, c):
                prepare(root, data, c, "Ready")
                source = root / "job/source.bam"
                if fault == "receipt":
                    (root / "job/state.json").write_text("{invalid")
                if fault == "destination":
                    (root / "output.bam").write_bytes(b"keep public")
                if fault == "source":
                    source.write_bytes(b"corrupt")
                before = len(seen)
                options = dict(expected_sha256="0"*64) if fault == "query" else {}
                report = manage(clean_bam_job, root, data, c, **options)
                self.assertEqual(report.state, "Failed", report)
                self.assertEqual(report.removed_files, ())
                self.assertTrue(source.exists())
                self.assertEqual(len(seen), before)
                if fault == "destination":
                    self.assertEqual((root / "output.bam").read_bytes(), b"keep public")

    def test_initialized_job_never_recreates_a_deleted_lock_inode(self):
        with fixture() as (root, data, _, seen, c):
            prepare(root, data, c, "Committed")
            (root / "job/lock").unlink()
            before = len(seen)
            for operation in (inspect_bam_job, clean_bam_job):
                self.assertEqual(manage(operation, root, data, c).error, "CheckpointInvalid")
            self.assertEqual(run_job(root, data, c).error, "CheckpointInvalid")
            self.assertFalse((root / "job/lock").exists())
            self.assertEqual(len(seen), before)
            self.assertTrue((root / "output.bam").exists())

    def test_active_download_blocks_inspection_and_cleanup(self):
        entered, release = threading.Event(), threading.Event()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "fixture.bam"
            write_bam(source)
            data = source.read_bytes()
            token = Cancellation()
            with service(data, block_gate=(entered, release)) as (origin, _, _), client(origin) as c:
                with ThreadPoolExecutor(max_workers=1) as executor:
                    task = executor.submit(run_job, root, data, c, cancellation=token)
                    try:
                        self.assertTrue(entered.wait(10))
                        for operation in (inspect_bam_job, clean_bam_job):
                            report = manage(operation, root, data, c)
                            self.assertEqual(report.error, "RecoveryBusy")
                            self.assertEqual(report.removed_files, ())
                    finally:
                        token.cancel()
                        release.set()
                    self.assertEqual(task.result(timeout=3).error, "Cancelled")
                self.assertEqual(manage(clean_bam_job, root, data, c).state, "Cleaned")

    def test_two_cleanup_owners_share_the_original_lock(self):
        with fixture() as (root, data, _, _, c):
            prepare(root, data, c, "Committed")
            entered, release = threading.Event(), threading.Event()
            finish = store._finish_release
            inode = (root / "job/lock").stat().st_ino

            def gate(*args):
                entered.set()
                if not release.wait(10):
                    raise OSError("test gate timed out")
                return finish(*args)

            with patch.object(store, "_finish_release", side_effect=gate):
                with ThreadPoolExecutor(max_workers=1) as executor:
                    task = executor.submit(manage, clean_bam_job, root, data, c)
                    try:
                        self.assertTrue(entered.wait(10))
                        self.assertEqual(manage(clean_bam_job, root, data, c).error, "RecoveryBusy")
                    finally:
                        release.set()
                    self.assertEqual(task.result(timeout=3).state, "Cleaned")
            self.assertEqual((root / "job/lock").stat().st_ino, inode)
            self.assertEqual(manage(clean_bam_job, root, data, c).state, "Cleaned")

    def test_interrupted_or_failed_release_is_completed_by_recovery(self):
        for fault in ("cancel", "sync"):
            with self.subTest(fault=fault), fixture() as (root, data, _, seen, c):
                prepare(root, data, c, "Committed")
                token = Cancellation()
                discard, sync = store._discard, store._sync_dir

                def cancel_after_unlink(path):
                    removed = discard(path)
                    if path.name == "source.bam" and removed:
                        token.cancel()
                    return removed

                def fail_after_unlink(path):
                    if path.name == "job" and not (root / "job/source.bam").exists():
                        raise OSError("sensitive sync failure")
                    return sync(path)

                context = patch.object(store, "_discard", side_effect=cancel_after_unlink) if fault == "cancel" else patch.object(store, "_sync_dir", side_effect=fail_after_unlink)
                with context:
                    result = manage(clean_bam_job, root, data, c, cancellation=token)
                self.assertEqual(result.error, "Cancelled" if fault == "cancel" else "StorageFailure")
                self.assertEqual(result.phase, "Releasing")
                self.assertFalse(result.sync_confirmed)
                self.assertFalse((root / "job/source.bam").exists())
                inode = (root / "output.bam").stat().st_ino
                before = len(seen)
                recovered = run_job(root, data, c)
                self.assertEqual(recovered.state, "Complete", recovered)
                self.assertEqual(recovered.phase, "Released")
                self.assertEqual((root / "output.bam").stat().st_ino, inode)
                self.assertEqual(len(seen), before)
                self.observe(f"Retried{fault.title()}Release", manage(inspect_bam_job, root, data, c))

    def test_precancelled_management_and_invalid_configuration_do_no_work(self):
        with fixture() as (root, data, _, seen, c):
            token = Cancellation()
            token.cancel()
            for operation in (inspect_bam_job, clean_bam_job):
                self.assertEqual(manage(operation, root, data, c, cancellation=token).error, "Cancelled")
                with self.assertRaisesRegex(GeneWireError, "InvalidQuery"):
                    manage(operation, root, data, c, cancellation=object())
                with self.assertRaisesRegex(GeneWireError, "InvalidQuery"):
                    operation(c, "\ud800", "chrSynthetic", 99, 101, root / "output.bam", root / "job",
                              expected_sha256=hashlib.sha256(data).hexdigest())
            self.assertFalse((root / "job").exists())
            self.assertEqual(seen, [])

    def test_dot_object_ids_fail_before_workspace_or_network(self):
        with fixture() as (root, data, _, seen, c):
            for object_id in (".", ".."):
                for operation in (inspect_bam_job, clean_bam_job, store.recover_bam):
                    with self.assertRaisesRegex(GeneWireError, "InvalidQuery"):
                        operation(c, object_id, "chrSynthetic", 99, 101,
                                  root / "output.bam", root / "job",
                                  expected_sha256=hashlib.sha256(data).hexdigest())
            self.assertFalse((root / "job").exists())
            self.assertEqual(seen, [])


if __name__ == "__main__":
    unittest.main()
