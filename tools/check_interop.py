"""Run a separately built htsget-axum on generated synthetic BAM only."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory, TemporaryFile
import time
import urllib.request

import pysam
from genewire import Client, Destination
from genewire.analysis import filter_bam
from _evidence import source_hashes

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
from test_python_stream import write_bam  # noqa: E402


def run(server: Path) -> dict:
    binary_hash = hashlib.sha256(server.read_bytes()).hexdigest()
    version = subprocess.check_output([str(server), "--version"], text=True, timeout=10).strip()
    cases = [(0, 1, ["A"]), (99, 100, ["B", "D"]), (100, 101, ["C", "D"]),
             (499, 500, []), (99, 101, ["B", "C", "D"])]
    with TemporaryDirectory(prefix="genewire-interop-") as directory:
        root = Path(directory)
        (root / "data").mkdir()
        bam = root / "data" / "synthetic.bam"
        write_bam(bam)
        pysam.index(str(bam))
        # Ask the OS for free loopback ports; startup is checked, never assumed.
        ports = []
        with socket.socket() as a, socket.socket() as b:
            for sock in (a, b):
                sock.bind(("127.0.0.1", 0))
                ports.append(sock.getsockname()[1])
        control, data = [f"http://127.0.0.1:{port}" for port in ports]
        config = root / "server.toml"
        config.write_text(
            'locations = "file://data"\n'
            f'ticket_server.addr = "127.0.0.1:{ports[0]}"\n'
            f'data_server.addr = "127.0.0.1:{ports[1]}"\n'
            'data_server.local_path = "data"\n'
        )
        environment = {k: v for k, v in os.environ.items() if not k.startswith("HTSGET_")}
        environment["RUST_LOG"] = "error"
        logs = TemporaryFile()
        process = subprocess.Popen([str(server), "--config", str(config)], env=environment, cwd=root,
                                   stdout=logs, stderr=logs)
        try:
            ready = time.monotonic() + 10
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            while True:
                try:
                    with opener.open(control + "/reads/service-info", timeout=.2) as response:
                        service_info = json.load(response)
                    break
                except OSError:
                    if process.poll() is not None or time.monotonic() >= ready:
                        logs.seek(0)
                        raise RuntimeError("independent server failed startup: " + logs.read(4096).decode(errors="replace")) from None
                    time.sleep(.02)
            destinations = {origin: Destination(["127.0.0.1"]) for origin in (control, data)}
            results = []
            with Client(control + "/reads/", destinations, loopback_http_for_tests=True) as client:
                for number, (start, end, expected) in enumerate(cases, 1):
                    # HTSlib's own htsget path performs ticket and block retrieval
                    # independently of GeneWire's Rust transport.
                    url = control + f"/reads/synthetic?format=BAM&referenceName=chrSynthetic&start={start}&end={end}"
                    baseline_process = subprocess.run([
                        sys.executable, "-c",
                        "import pysam,sys,json; a,b=map(int,sys.argv[2:]); "
                        "f=pysam.AlignmentFile(sys.argv[1], 'rb'); "
                        "print(json.dumps(sorted(r.query_name for r in f if "
                        "r.reference_name=='chrSynthetic' and r.reference_start<b and r.reference_end>a)))",
                        url, str(start), str(end),
                    ], capture_output=True, timeout=10)
                    if baseline_process.returncode:
                        raise RuntimeError("independent HTSlib htsget baseline failed: " + baseline_process.stderr[:1024].decode(errors="replace"))
                    htsget_baseline = json.loads(baseline_process.stdout)
                    stream = client.open("synthetic", "chrSynthetic", start, end)
                    output = root / f"q{number}.bam"
                    report = filter_bam(stream, output, "chrSynthetic", start, end, timeout_s=10)
                    if report.state != "AnalysisComplete":
                        raise RuntimeError(f"Q{number} analysis failed: {report.error}")
                    with pysam.AlignmentFile(str(output), "rb") as decoded:
                        observed = sorted(record.query_name for record in decoded)
                    with pysam.AlignmentFile(str(bam), "rb") as indexed:
                        baseline = sorted(record.query_name for record in indexed.fetch("chrSynthetic", start, end))
                    if observed != expected or baseline != expected or htsget_baseline != expected:
                        raise RuntimeError(f"Q{number} truth mismatch")
                    results.append({"case": f"Q{number}", "interval": [start, end],
                                    "expected": expected, "observed": observed,
                                    "indexed_baseline": baseline, "htslib_htsget_baseline": htsget_baseline,
                                    "report": asdict(report)})
            return {"server": version, "server_binary_sha256": binary_hash,
                    "server_build_source_revision": "2a91e661e6a287e3adf30e65c26a8f47697f3548",
                    "implementation_file_sha256": source_hashes(),
                    "python": platform.python_version(), "platform": platform.platform(),
                    "pysam": pysam.__version__, "htslib_samtools": pysam.__samtools_version__,
                    "server_features": "no-default-features; local file storage",
                    "fixture": "original synthetic A/B/C/D; generated BAM/BAI; no upstream bundled data",
                    "transport": "two explicit loopback HTTP origins; test mode only",
                    "service_info": service_info, "results": results}
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
            logs.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.server.resolve())
    args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Independent htsget server: Q1–Q5 matched, decoded and compared with indexed HTSlib; {args.report}")
