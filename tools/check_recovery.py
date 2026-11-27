"""Run synthetic M3 process/storage faults and retain a source-bound summary."""
import argparse
import json
from pathlib import Path
import platform
import sys
import unittest

from _evidence import source_hashes


class EvidenceResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.observed = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.observed.append({
            "test": test.id(), "outcome": "passed",
            "crashes": getattr(test, "crash_observations", []),
            "truth": getattr(test, "truth_observations", []),
            "cancellation": getattr(test, "cancellation_observations", []),
        })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "tests"))
    suite = unittest.TestSuite(
        unittest.defaultTestLoader.discover(str(root / "tests"), pattern=pattern)
        for pattern in ("test_recovery.py", "test_cancellation.py")
    )
    result = unittest.TextTestRunner(verbosity=2, resultclass=EvidenceResult).run(suite)
    report = {
        "platform": platform.platform(), "python": platform.python_version(),
        "implementation_file_sha256": source_hashes(),
        "method": "synthetic loopback BAM; actual SIGKILL and explicit cancellation boundaries; injected filesystem errors; one local run",
        "limits": "process-crash recovery only; no byte-offset resume, power-loss or broad platform qualification; expected digest supplied by fixture",
        "tests_run": result.testsRun, "failures": len(result.failures),
        "errors": len(result.errors), "skips": len(result.skipped),
        "successful": result.wasSuccessful() and not result.skipped,
        "observations": result.observed,
    }
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    return 0 if report["successful"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
