"""Original synthetic BAM truth beyond Q1-Q5; no public or patient datasets."""
from collections import Counter
import hashlib
from pathlib import Path
import random
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import pysam

from genewire import GeneWireError, recovery
from genewire.analysis import filter_bam
from test_python_stream import client, service


# Written independently of the filter: (name, flag, reference, zero-based start,
# CIGAR, sequence). Repeated identical alignments must remain two records.
ALIGNMENTS = [
    ("left", 0, "chrSynthetic", 90, "10M", "A"*10),
    ("duplicate", 0, "chrSynthetic", 99, "2M", "CC"),
    ("duplicate", 0, "chrSynthetic", 99, "2M", "CC"),
    ("secondary", 256, "chrSynthetic", 99, "2M", "GG"),
    ("supplementary", 2048, "chrSynthetic", 99, "2M", "TT"),
    ("marked_duplicate", 1024, "chrSynthetic", 99, "2M", "AC"),
    ("qc_fail", 512, "chrSynthetic", 99, "2M", "GT"),
    ("unmapped_placed", 4, "chrSynthetic", 99, "2M", "AA"),
    ("right", 0, "chrSynthetic", 100, "10M", "C"*10),
    ("skip", 0, "chrSynthetic", 200, "5M10N5M", "G"*10),
    ("deletion", 0, "chrSynthetic", 240, "5M10D5M", "T"*10),
    ("clipped", 0, "chrSynthetic", 280, "5S5M", "A"*10),
    ("inserted", 0, "chrSynthetic", 300, "5M3I5M", "C"*13),
    ("zero_reference", 0, "chrSynthetic", 330, "3I", "GGG"),
    ("other_reference", 0, "chrOther", 99, "2M", "AC"),
    ("unmapped", 4, "*", -1, "*", "NN"),
]
CENTRAL = ["duplicate", "duplicate", "secondary", "supplementary", "marked_duplicate", "qc_fail"]
CASES = [
    ("B01", "chrSynthetic", 99, 100, ["left", *CENTRAL]),
    ("B02", "chrSynthetic", 100, 101, [*CENTRAL, "right"]),
    ("B03", "chrSynthetic", 101, 102, ["right"]),
    ("B04", "chrSynthetic", 210, 211, ["skip"]),
    ("B05", "chrSynthetic", 250, 251, ["deletion"]),
    ("B06", "chrSynthetic", 279, 280, []),
    ("B07", "chrSynthetic", 280, 281, ["clipped"]),
    ("B08", "chrSynthetic", 309, 310, ["inserted"]),
    ("B09", "chrSynthetic", 310, 311, []),
    ("B10", "chrSynthetic", 330, 331, ["zero_reference"]),
    ("B11", "chrOther", 99, 100, ["other_reference"]),
    ("B12", "chrSynthetic", 999, 1000, []),
]


def write_fixture(path, alignments=ALIGNMENTS):
    header = pysam.AlignmentHeader.from_dict({"HD": {"VN": "1.6", "SO": "coordinate"},
             "SQ": [{"SN": name, "LN": 1000000} for name in ("chrSynthetic", "chrOther")],
             "RG": [{"ID": "synthetic", "SM": "generated"}]})
    with pysam.AlignmentFile(str(path), "wb", header=header) as output:
        for name, flag, reference, start, cigar, sequence in alignments:
            qualities = "I" * len(sequence)
            line = f"{name}\t{flag}\t{reference}\t{start+1}\t42\t{cigar}\t*\t0\t0\t{sequence}\t{qualities}\tRG:Z:synthetic"
            output.write(pysam.AlignedSegment.fromstring(line, header))


def records(path):
    with pysam.AlignmentFile(str(path), "rb") as source:
        return [record.to_string() for record in source]


class BamSemanticsTests(unittest.TestCase):
    def observe(self, **observation):
        self.__dict__.setdefault("semantic_observations", []).append(observation)

    def test_explicit_span_flag_multiplicity_and_field_truth_against_indexed_samtools(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.bam"
            write_fixture(source)
            pysam.index(str(source))
            all_records = records(source)
            with service(source.read_bytes()) as (origin, _, _), client(origin) as c:
                for case, reference, start, end, expected in CASES:
                    with self.subTest(case=case), c.open("synthetic", reference, start, end) as stream:
                        output = root / (case + ".bam")
                        report = filter_bam(stream, output, reference, start, end)
                        self.assertEqual(report.state, "AnalysisComplete", report)
                        with pysam.AlignmentFile(str(source), "rb") as original, pysam.AlignmentFile(str(output), "rb") as decoded:
                            self.assertEqual(decoded.header.to_dict(), original.header.to_dict())
                        actual = records(output)
                        names = [line.split("\t")[0] for line in actual]
                        self.assertEqual(Counter(names), Counter(expected))
                        expected_records = [line for line in all_records if line.split("\t")[0] in expected]
                        self.assertEqual(Counter(actual), Counter(expected_records))
                        # Independent HTSlib index/region parser; the production
                        # full-decode filter is not used to select this baseline.
                        baseline = pysam.view("-F", "4", str(source), f"{reference}:{start+1}-{end}").splitlines()
                        self.assertEqual(Counter(actual), Counter(baseline))
                        self.observe(case=case, expected=sorted(expected), observed=sorted(names),
                                     full_fields_preserved=True, indexed_samtools_matched=True)

    def test_large_multiblock_source_and_recovered_result_preserve_all_records(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.bam"
            generator = random.Random(20261127)
            alignments = [(f"record{i}", 0, "chrSynthetic", i*10, "100M",
                           "".join(generator.choices("ACGT", k=100))) for i in range(6000)]
            write_fixture(source, alignments)
            data = source.read_bytes()
            self.assertGreater(len(data), 65536)
            expected = Counter(records(source))
            with service(data) as (origin, seen, _), client(origin) as c:
                arguments = (c, "synthetic", "chrSynthetic", 0, 100000,
                             root / "output.bam", root / "job")
                options = dict(expected_sha256=hashlib.sha256(data).hexdigest())
                original = recovery._write_state

                def interrupt(job, state):
                    original(job, state)
                    if state["phase"] == "Verified":
                        raise GeneWireError("Cancelled")

                with patch.object(recovery, "_write_state", side_effect=interrupt):
                    self.assertEqual(recovery.recover_bam(*arguments, **options).error, "Cancelled")
                before = len(seen)
                report = recovery.recover_bam(*arguments, **options)
                self.assertEqual(report.state, "Complete", report)
                self.assertTrue(report.source_reused)
                self.assertEqual(len(seen), before)
                self.assertEqual(Counter(records(root / "output.bam")), expected)
                self.observe(case="B13", source_bytes=len(data), records=6000,
                             new_network_requests=0, full_fields_preserved=True)

    def test_a_missing_duplicate_is_detected_by_the_oracle_not_transport(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "omission.bam"
            write_fixture(source, ALIGNMENTS[:2] + ALIGNMENTS[3:])
            with service(source.read_bytes()) as (origin, _, _), client(origin) as c, c.open("s", "chrSynthetic", 100, 101) as stream:
                output = root / "output.bam"
                report = filter_bam(stream, output, "chrSynthetic", 100, 101)
                self.assertEqual(report.state, "AnalysisComplete", report)
                names = [line.split("\t")[0] for line in records(output)]
                self.assertNotEqual(Counter(names), Counter([*CENTRAL, "right"]))
                self.assertEqual(Counter(names)["duplicate"], 1)
                self.observe(case="B14", analysis="AnalysisComplete", oracle="Mismatch", duplicate_omission_detected=True)

    def test_truncated_source_and_unknown_reference_never_publish(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.bam"
            write_fixture(source)
            for number, (data, reference) in enumerate(((source.read_bytes()[:-40], "chrSynthetic"), (source.read_bytes(), "absent"))):
                with self.subTest(reference=reference), service(data) as (origin, _, _), client(origin) as c, c.open("s", reference, 0, 1000) as stream:
                    output = root / f"failed-{number}.bam"
                    report = filter_bam(stream, output, reference, 0, 1000)
                    self.assertEqual(report.state, "Failed", report)
                    self.assertEqual(report.error, "ConsumerFailed")
                    self.assertFalse(output.exists())
                    self.assertFalse(list(root.glob("*.partial")))
                    self.observe(case="B15" if number == 0 else "B16", incomplete_output_rejected=True)


if __name__ == "__main__":
    unittest.main()
