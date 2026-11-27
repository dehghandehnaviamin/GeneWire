"""Supervised analysis gates, provisional staging and bounded failure cleanup."""
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch

import pysam

from genewire import GeneWireError
from genewire.analysis import filter_bam, _supervise
from test_python_stream import client, service, write_bam


@unittest.skipUnless(os.name == "posix", "The analysis supervisor currently requires POSIX")
class AnalysisTests(unittest.TestCase):
    def test_full_decode_overlap_filter_and_staged_commit_for_q1_to_q5(self):
        cases = [(0, 1, ["A"]), (99, 100, ["B", "D"]), (100, 101, ["C", "D"]),
                 (499, 500, []), (99, 101, ["B", "C", "D"])]
        with TemporaryDirectory() as directory:
            source = Path(directory) / "source.bam"
            write_bam(source)
            with service(source.read_bytes()) as (origin, _, _), client(origin) as c:
                for i, (start, end, expected) in enumerate(cases):
                    stream = c.open("s", "chrSynthetic", start, end)
                    destination = Path(directory) / f"result-{i}.bam"
                    report = filter_bam(stream, destination, "chrSynthetic", start, end)
                    self.assertEqual(report.state, "AnalysisComplete", report)
                    self.assertEqual(report.transport.state, "TransportComplete")
                    self.assertTrue(report.output_committed)
                    self.assertTrue(report.cleanup_complete)
                    self.assertEqual(report.transport.cleanup, "Complete")
                    with pysam.AlignmentFile(str(destination), "rb") as bam:
                        self.assertEqual(sorted(r.query_name for r in bam), expected)
                self.assertEqual(list(Path(directory).glob("*.partial")), [])

    def test_decoder_failure_does_not_promote_invalid_bam(self):
        with TemporaryDirectory() as directory, service(b"invalid BAM") as (origin, _, _), client(origin) as c:
            stream = c.open("s", "chr", 0, 1)
            target = Path(directory) / "out.bam"
            report = filter_bam(stream, target, "chr", 0, 1)
            self.assertEqual(report.state, "Failed")
            self.assertEqual(report.error, "ConsumerFailed")
            self.assertFalse(report.output_committed)
            self.assertTrue(report.cleanup_complete)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_child_success_cannot_hide_late_transport_failure(self):
        ticket = {"htsget": {"format": "BAM", "urls": [
            {"url": "data:;base64,QUI="}, {"url": "https://unapproved.invalid/private"},
        ]}}
        with TemporaryDirectory() as directory, service(custom_ticket=ticket) as (origin, _, _), client(origin) as c:
            stream = c.open("s", "chr", 0, 1)
            report = _supervise(stream, [sys.executable, "-c", "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())"], Path(directory) / "out")
            self.assertEqual(report.error, "NetworkPolicy")
            self.assertEqual(report.transport.state, "Failed")
            self.assertTrue(report.transport.may_have_partial_output)
            self.assertFalse(report.output_committed)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_early_exit_nonzero_and_broken_input_do_not_promote_output(self):
        for code in ["pass", "raise SystemExit(7)"]:
            with self.subTest(code=code), TemporaryDirectory() as directory, service(delay=.1) as (origin, _, _), client(origin) as c:
                stream = c.open("s", "chr", 0, 1)
                report = _supervise(stream, [sys.executable, "-c", code], Path(directory) / "out")
                self.assertEqual(report.error, "ConsumerFailed")
                self.assertFalse(report.output_committed)
                self.assertTrue(report.cleanup_complete)
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_stalled_process_is_killed_and_a_blocked_native_read_is_cancelled(self):
        with TemporaryDirectory() as directory, service(delay=.5) as (origin, _, _), client(origin) as c:
            stream = c.open("s", "chr", 0, 1)
            started = time.monotonic()
            report = _supervise(stream, [sys.executable, "-c", "import time; time.sleep(30)"],
                                 Path(directory) / "out", timeout_s=.1, cleanup_timeout_s=1)
            self.assertEqual(report.error, "DeadlineExceeded")
            self.assertLess(time.monotonic() - started, 3)
            self.assertTrue(report.cleanup_complete)
            self.assertFalse(report.output_committed)
            self.assertEqual(report.transport.state, "Cancelled")

    def test_stdout_and_stderr_have_finite_budgets(self):
        for descriptor in [1, 2]:
            with self.subTest(descriptor=descriptor), TemporaryDirectory() as directory, service() as (origin, _, _), client(origin) as c:
                stream = c.open("s", "chr", 0, 1)
                command = [sys.executable, "-c", f"import os,sys; sys.stdin.buffer.read(); os.write({descriptor}, b'x'*131072)"]
                report = _supervise(stream, command, Path(directory) / "out", max_output_bytes=16)
                self.assertEqual(report.error, "ResourceLimit")
                self.assertFalse(report.output_committed)
                self.assertTrue(report.cleanup_complete)
                self.assertEqual(list(Path(directory).iterdir()), [])

    def test_decoder_failure_preserves_an_already_complete_transport(self):
        with TemporaryDirectory() as directory, service() as (origin, _, _), client(origin) as c:
            stream = c.open("s", "chr", 0, 1)
            report = _supervise(stream, [sys.executable, "-c", "import sys; sys.stdin.buffer.read(); raise SystemExit(7)"], Path(directory) / "out")
            self.assertEqual(report.error, "ConsumerFailed")
            self.assertEqual(report.exit_code, 7)
            self.assertEqual(report.transport.state, "TransportComplete")
            self.assertIsNone(report.transport.error)
            self.assertFalse(report.output_committed)

    def test_process_ignoring_termination_is_killed_under_the_cleanup_budget(self):
        with TemporaryDirectory() as directory, service() as (origin, _, _), client(origin) as c:
            stream = c.open("s", "chr", 0, 1)
            code = "import signal,sys,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); sys.stdin.buffer.read(); time.sleep(30)"
            report = _supervise(stream, [sys.executable, "-c", code], Path(directory) / "out", timeout_s=.2, cleanup_timeout_s=.2)
            self.assertEqual(report.error, "DeadlineExceeded")
            self.assertEqual(report.exit_code, -9)
            self.assertTrue(report.cleanup_complete)
            self.assertFalse(report.output_committed)

    def test_existing_destination_and_start_failure_preserve_files(self):
        with TemporaryDirectory() as directory, service() as (origin, _, _), client(origin) as c:
            target = Path(directory) / "existing"
            target.write_bytes(b"keep")
            for destination in [target, Path(directory) / "new"]:
                stream = c.open("s", "chr", 0, 1)
                report = _supervise(stream, [str(Path(directory) / "missing-executable")], destination)
                self.assertEqual(report.error, "ConsumerFailed")
                self.assertTrue(report.cleanup_complete)
                self.assertFalse(report.output_committed)
            self.assertEqual(target.read_bytes(), b"keep")
            self.assertEqual(list(Path(directory).iterdir()), [target])

    def test_invalid_limits_do_not_start_or_cancel_the_stream(self):
        with service() as (origin, seen, _), client(origin) as c, c.open("s", "chr", 0, 1) as stream:
            for kwargs in [{"timeout_s": float("nan")}, {"timeout_s": 2**4096}, {"timeout_s": True}, {"max_output_bytes": 0}, {"cleanup_timeout_s": -1}]:
                with self.assertRaisesRegex(GeneWireError, "InvalidQuery"):
                    filter_bam(stream, "unused.bam", "chr", 0, 1, **kwargs)
            self.assertEqual(stream.result().state, "New")
            self.assertEqual(seen, [])

    def test_flush_and_close_errors_still_remove_provisional_output(self):
        original_fdopen = os.fdopen

        class FailedOutput:
            def __init__(self, fd, mode):
                self.file = original_fdopen(fd, mode)

            def write(self, data):
                return self.file.write(data)

            def flush(self):
                raise OSError("sensitive filesystem diagnostic")

            def close(self):
                self.file.close()
                raise OSError("sensitive close diagnostic")

        with TemporaryDirectory() as directory, service() as (origin, _, _), client(origin) as c:
            stream = c.open("s", "chr", 0, 1)
            with patch("genewire.analysis.os.fdopen", side_effect=FailedOutput):
                report = _supervise(stream, [sys.executable, "-c", "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())"], Path(directory) / "out")
            self.assertEqual(report.error, "ConsumerFailed")
            self.assertFalse(report.output_committed)
            self.assertFalse(report.cleanup_complete)
            self.assertNotIn("sensitive", repr(report))
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_filter_region_must_match_the_original_stream_query(self):
        with service() as (origin, seen, _), client(origin) as c, c.open("s", "chr", 0, 1) as stream:
            with self.assertRaisesRegex(GeneWireError, "InvalidQuery"):
                filter_bam(stream, "unused.bam", "chr", 1, 2)
            self.assertEqual(stream.result().state, "New")
            self.assertEqual(seen, [])


if __name__ == "__main__":
    unittest.main()
