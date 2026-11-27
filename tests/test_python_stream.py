"""Loopback integration and independently decoded synthetic BAM; no patient data."""
from __future__ import annotations

import base64
from contextlib import contextmanager
import gc
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import shutil
import ssl
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory, TemporaryFile
import threading
import time
import unittest
from urllib.parse import parse_qs, urlsplit

from genewire import Client, Destination, GeneWireError
import pysam


@contextmanager
def service(payload: bytes = b"ABCD", *, delay: float = 0, custom_ticket=None, tls=None):
    seen = []
    received = threading.Event()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            seen.append((self.path, dict(self.headers)))
            received.set()
            time.sleep(delay)
            origin = f"{'https' if tls else 'http'}://127.0.0.1:{self.server.server_port}"
            if self.path.startswith("/reads/"):
                ticket = custom_ticket or {"htsget": {"format": "BAM", "urls": [
                    {"url": "data:;base64," + base64.b64encode(payload[:8]).decode()},
                    {"url": origin + "/block"},
                ]}}
                body = json.dumps(ticket).encode()
            else:
                body = payload[8:]
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    if tls:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(*tls)
        server.socket = context.wrap_socket(server.socket, server_side=True)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .01})
    thread.start()
    origin = f"{'https' if tls else 'http'}://127.0.0.1:{server.server_port}"
    try:
        yield origin, seen, received
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def client(origin, **kwargs):
    return Client(origin + "/reads/", {origin: Destination(["127.0.0.1"])},
                  loopback_http_for_tests=True, **kwargs)


class PythonStreamTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("openssl"), "OpenSSL CLI is required for the temporary TLS fixture")
    def test_untrusted_tls_certificate_is_rejected_without_retry(self):
        with TemporaryDirectory(prefix="genewire-tls-") as directory:
            cert, key = Path(directory) / "cert.pem", Path(directory) / "key.pem"
            subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
                            "-keyout", str(key), "-out", str(cert), "-days", "1", "-subj", "/CN=localhost"],
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
            with service(tls=(cert, key)) as (origin, seen, _), client(origin) as c, c.open("s", "chr", 0, 1) as stream:
                with self.assertRaisesRegex(GeneWireError, "NetworkPolicy"):
                    stream.read_chunk()
                self.assertEqual(stream.result().retries, 0)
                self.assertEqual(seen, [])

    def test_owned_bytes_result_and_context_cleanup(self):
        with service(b"abcdefghijklmnop") as (origin, seen, _), client(origin) as c:
            with c.open("synthetic", "chrSynthetic", 0, 1) as stream:
                saved = stream.read_chunk(2)
                result = saved + b"".join(stream.iter_chunks(3))
                self.assertEqual(result, b"abcdefghijklmnop")
                self.assertEqual(saved, b"ab")
                self.assertEqual(stream.finish().state, "TransportComplete")
                self.assertEqual(stream.result().source_consistency, "Unverified")
                self.assertEqual(stream.read_chunk(), b"")
            self.assertTrue(stream.result().cleanup_complete)
            self.assertEqual(len(seen), 2)

    def test_boolean_float_overflow_and_empty_coordinates_fail_before_network(self):
        with service() as (origin, seen, _), client(origin) as c:
            for start, end in [(True, 2), (0., 1), (0, 2**32), (1, 1), (-1, 1)]:
                with self.assertRaises(GeneWireError):
                    c.open("synthetic", "chrSynthetic", start, end)
            self.assertEqual(seen, [])

    def test_chunk_size_and_early_finish_are_explicit_errors(self):
        with service() as (origin, _, _), client(origin) as c, c.open("s", "chr", 0, 1) as s:
            for size in [0, -1, True, 256*1024 + 1]:
                with self.assertRaisesRegex(GeneWireError, "InvalidQuery"):
                    s.read_chunk(size)
            with self.assertRaisesRegex(GeneWireError, "InvalidState"):
                s.finish()
            self.assertEqual(b"".join(s.iter_chunks()), b"ABCD")

    def test_native_wait_releases_python_and_concurrent_read_is_rejected(self):
        with service(delay=.2) as (origin, _, received), client(origin) as c:
            s = c.open("s", "chr", 0, 1)
            outcome = []
            def read():
                try:
                    s.read_chunk()
                except GeneWireError as e:
                    outcome.append(str(e))
            t = threading.Thread(target=read)
            t.start()
            self.assertTrue(received.wait(2), "native read prevented Python progress")
            with self.assertRaisesRegex(GeneWireError, "InvalidState"):
                s.read_chunk()
            s.cancel()
            s.close()
            t.join(2)
            self.assertFalse(t.is_alive())
            self.assertEqual(outcome, ["Cancelled"])
            self.assertTrue(s.result().cleanup_complete)

    def test_stream_retains_runtime_after_client_is_collected(self):
        with service() as (origin, _, _):
            c = client(origin)
            s = c.open("s", "chr", 0, 1)
            del c
            gc.collect()
            self.assertEqual(b"".join(s.iter_chunks()), b"ABCD")
            s.close()

    def test_partial_close_and_original_exception_are_preserved(self):
        with service() as (origin, _, _), client(origin) as c:
            with self.assertRaisesRegex(ValueError, "consumer failed"):
                with c.open("s", "chr", 0, 1) as s:
                    self.assertEqual(s.read_chunk(1), b"A")
                    raise ValueError("consumer failed")
            self.assertEqual(s.result().state, "Cancelled")
            self.assertTrue(s.result().cleanup_complete)

    def test_deadline_includes_caller_pause(self):
        with service() as (origin, _, _), client(origin, timeout_ms=20) as c:
            s = c.open("s", "chr", 0, 1)
            end = time.monotonic() + 2
            while s.result().error is None and time.monotonic() < end:
                time.sleep(.001)
            with self.assertRaisesRegex(GeneWireError, "DeadlineExceeded"):
                s.read_chunk()
            s.close()

    def test_sensitive_remote_ticket_text_is_absent_from_errors(self):
        ticket = {"htsget": {"format": "BAM", "urls": [{"url": "https://sensitive.invalid/token-secret"}]}}
        with service(custom_ticket=ticket) as (origin, _, _), client(origin) as c, c.open("private-id", "private-reference", 0, 1) as s:
            with self.assertRaisesRegex(GeneWireError, "NetworkPolicy") as caught:
                s.read_chunk()
            self.assertNotIn("secret", repr(caught.exception))
            self.assertNotIn("private", repr(s.result()))


def write_bam(path: Path, *, include_d: bool = True) -> None:
    header = {"HD": {"VN": "1.6", "SO": "coordinate"}, "SQ": [{"SN": "chrSynthetic", "LN": 1000}]}
    with pysam.AlignmentFile(str(path), "wb", header=header) as bam:
        records = [("A", 0, 1), ("D", 94, 10), ("B", 99, 1), ("C", 100, 1)]
        for name, pos, size in records:
            if name == "D" and not include_d:
                continue
            record = pysam.AlignedSegment()
            record.query_name = name
            record.query_sequence = "A" * size
            record.flag = 0
            record.reference_id = 0
            record.reference_start = pos
            record.mapping_quality = 60
            record.cigar = [(0, size)]
            bam.write(record)


class SyntheticBamTests(unittest.TestCase):
    def test_successful_transport_can_still_fail_a_mature_decoder(self):
        with service(b"invalid BAM") as (origin, _, _), client(origin) as c, c.open("s", "chr", 0, 1) as stream:
            payload = b"".join(stream.iter_chunks())
            self.assertEqual(stream.finish().state, "TransportComplete")
            decoded = subprocess.run([sys.executable, "-c", "import pysam; list(pysam.AlignmentFile('-', 'rb'))"],
                                     input=payload, capture_output=True, timeout=10)
            self.assertNotEqual(decoded.returncode, 0)

    def test_a_decodable_omission_is_not_detected_by_transport(self):
        with TemporaryDirectory(prefix="genewire-omission-") as directory:
            path = Path(directory) / "missing.bam"
            write_bam(path, include_d=False)
            with service(path.read_bytes()) as (origin, _, _), client(origin) as c, c.open("s", "chrSynthetic", 99, 100) as stream:
                output = Path(directory) / "received.bam"
                with output.open("wb") as file:
                    for chunk in stream.iter_chunks():
                        file.write(chunk)
                self.assertEqual(stream.finish().state, "TransportComplete")
                with pysam.AlignmentFile(str(output), "rb") as bam:
                    selected = sorted(r.query_name for r in bam if r.reference_start < 100 and r.reference_end > 99)
                self.assertEqual(selected, ["B"])
                self.assertNotEqual(selected, ["B", "D"])

    def test_q1_to_q5_through_native_stream_and_external_htslib_decoder(self):
        # Truth is handwritten from the M0 coordinate example, not computed by
        # GeneWire or copied from the decoder's selection results.
        queries = [(0, 1, ["A"]), (99, 100, ["B", "D"]), (100, 101, ["C", "D"]),
                   (499, 500, []), (99, 101, ["B", "C", "D"])]
        with TemporaryDirectory(prefix="genewire-synthetic-") as directory:
            path = Path(directory) / "synthetic.bam"
            write_bam(path)
            payload = path.read_bytes()
            # The loopback service deliberately overreturns all four records:
            # exact selection must be a separate declared decoder/filter policy.
            with service(payload) as (origin, seen, _), client(origin) as c:
                for start, end, expected in queries:
                    with c.open("synthetic", "chrSynthetic", start, end) as stream, TemporaryFile() as out, TemporaryFile() as errors:
                        process = subprocess.Popen([
                            sys.executable, "-c",
                            "import pysam,sys,json; a,b=map(int,sys.argv[1:]); "
                            "f=pysam.AlignmentFile('-', 'rb'); "
                            "print(json.dumps(sorted(r.query_name for r in f "
                            "if r.reference_name=='chrSynthetic' and r.reference_start<b and r.reference_end>a)))",
                            str(start), str(end),
                        ], stdin=subprocess.PIPE, stdout=out, stderr=errors)
                        try:
                            for chunk in stream.iter_chunks(7):
                                process.stdin.write(chunk)
                            process.stdin.close()
                            transport = stream.finish()
                            self.assertEqual(process.wait(timeout=10), 0)
                            self.assertEqual(transport.state, "TransportComplete")
                            out.seek(0)
                            self.assertEqual(json.load(out), expected)
                        finally:
                            if process.poll() is None:
                                process.kill()
                                process.wait()
                            process.stdin.close()
                requested = [parse_qs(urlsplit(path).query) for path, _ in seen if path.startswith("/reads/")]
                self.assertEqual([(int(q["start"][0]), int(q["end"][0])) for q in requested], [(a,b) for a,b,_ in queries])


if __name__ == "__main__":
    unittest.main()
