"""Single-run opaque transport resource probe; no genomic/performance ranking."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import platform
import resource
import subprocess
import sys
from tempfile import TemporaryDirectory
import threading
import time
import tracemalloc

from genewire import Client, Destination
from _evidence import source_hashes

PATTERN = bytes(range(256)) * 256


def rss() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def consume(origin: str, size: int, retain: bool) -> dict:
    with Client(origin + "/reads/", {origin: Destination(["127.0.0.1"])},
                loopback_http_for_tests=True, result_bytes=size) as client:
        before = rss()
        tracemalloc.start()
        started = time.perf_counter_ns()
        chunks = []
        checksum = hashlib.sha256()
        count = 0
        with client.open("synthetic", "chr", 0, 1) as stream:
            for chunk in stream.iter_chunks(65536):
                count += len(chunk)
                checksum.update(chunk)
                if retain:
                    chunks.append(chunk)
            report = stream.finish()
        report = stream.result()
        elapsed = time.perf_counter_ns() - started
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        if count != size:
            raise RuntimeError("byte count mismatch")
        memory = report.memory
        if (memory.current_payload_bytes != 0 or memory.peak_payload_bytes > 2 * 1024**2
                or memory.rust_output_copy_bytes != size or memory.python_output_copy_bytes != size):
            raise RuntimeError("accounted payload/copy boundary mismatch")
        return {"retained_by_caller": retain, "bytes": count, "sha256": checksum.hexdigest(),
                "elapsed_ns": elapsed, "rss_before_bytes": before, "rss_peak_bytes": rss(),
                "python_traced_current_bytes": current, "python_traced_peak_bytes": peak,
                "retained_chunks": len(chunks), "transport": asdict(report)}


def run(size: int) -> dict:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def do_GET(self):
            if self.path.startswith("/reads/"):
                body = json.dumps({"htsget": {"format": "BAM", "urls": [
                    {"url": f"http://127.0.0.1:{self.server.server_port}/block"},
                ]}}).encode()
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(200)
                self.send_header("Content-Length", str(size))
                self.end_headers()
                left = size
                try:
                    while left:
                        part = PATTERN[:min(left, len(PATTERN))]
                        self.wfile.write(part)
                        left -= len(part)
                except (BrokenPipeError, ConnectionResetError):
                    pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": .01})
    thread.start()
    try:
        origin = f"http://127.0.0.1:{server.server_port}"
        results = []
        with TemporaryDirectory(prefix="genewire-resource-") as directory:
            for retain in [False, True]:
                path = Path(directory) / "measurement.json"
                subprocess.run([sys.executable, str(Path(__file__).resolve()), "--client", origin,
                                "--bytes", str(size), "--retain", str(int(retain)),
                                "--report", str(path)], check=True, timeout=60)
                results.append(json.loads(path.read_text()))
        expected = hashlib.sha256()
        left = size
        while left:
            expected.update(PATTERN[:min(left, len(PATTERN))])
            left -= min(left, len(PATTERN))
        if any(r["sha256"] != expected.hexdigest() for r in results):
            raise RuntimeError("payload checksum mismatch")
        return {"platform": platform.platform(), "python": platform.python_version(),
                "implementation_file_sha256": source_hashes(),
                "method": "fresh client processes; server RSS excluded; one run per retention mode; 64 KiB reads",
                "limits": "opaque bytes, not valid BAM; logical accepted-payload extents and two output-copy counters exclude allocator slack, HTTP/TLS/JSON buffers and caller memory; not a process-memory cap or throughput benchmark",
                "results": results}
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bytes", type=int, default=64 * 1024 * 1024)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--client")
    parser.add_argument("--retain", type=int, choices=[0, 1], default=0)
    args = parser.parse_args()
    if not 0 < args.bytes <= 1024**3:
        parser.error("bytes must be positive and at most 1 GiB")
    result = consume(args.client, args.bytes, bool(args.retain)) if args.client else run(args.bytes)
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    if not args.client:
        print(f"Opaque transport resource measurements saved: {args.report}")
