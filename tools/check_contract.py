"""Validate draft-to-test references; this index does not execute behavior tests."""
import argparse
import ast
import json
from pathlib import Path
import re

from _evidence import source_hashes


def check(root):
    vectors = json.loads((root / "docs/spec/vectors/cases.json").read_text())
    index = json.loads((root / "docs/spec/vectors/coverage-map.json").read_text())
    ids = [case["id"] for case in vectors["cases"]]
    mapped = [case["id"] for case in index["cases"]]
    if len(set(mapped)) != len(mapped) or set(mapped) != set(ids):
        raise ValueError("candidate/reference IDs differ")
    observations = []
    for case in index["cases"]:
        if case["coverage"] != "mapped_subset" or not case["checks"] or not case["limits"]:
            raise ValueError("missing subset limits")
        for reference in case["checks"]:
            path = root / reference["file"]
            if not path.resolve().is_relative_to(root.resolve()):
                raise ValueError("test path escapes repository")
            text = path.read_text()
            name = reference["symbol"]
            if path.suffix == ".py":
                symbols = [node.name for node in ast.walk(ast.parse(text))
                           if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]
            elif path.suffix == ".rs":
                symbols = re.findall(r"#\[test\]\s*fn\s+(\w+)\s*\(", text)
            else:
                raise ValueError("not a test source")
            if symbols.count(name) != 1:
                raise ValueError(f"missing/ambiguous test reference: {reference}")
        observations.append(dict(case=case["id"], coverage="mapped_subset",
                                 references=case["checks"], limits=case["limits"]))
    return dict(kind="structural_test_reference_index", behavior_tests_executed=0,
                successful=True, candidate_cases=len(ids), observations=observations,
                limits=index["runtime_evidence"], implementation_file_sha256=source_hashes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    report = check(Path(__file__).resolve().parents[1])
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(f"{report['candidate_cases']} draft cases mapped; references valid; no behavior tests executed by this index")


if __name__ == "__main__":
    main()
