"""Private full-decode worker; invoked only through the supervised BAM adapter."""
import sys


def main() -> int:
    import pysam

    reference, start, end = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    with pysam.AlignmentFile("-", "rb") as source:
        if reference not in source.references:
            return 1
        with pysam.AlignmentFile("-", "wb", template=source) as output:
            for record in source:
                if (not record.is_unmapped and record.reference_name == reference
                        and record.reference_start < end
                        and record.reference_end is not None and record.reference_end > start):
                    output.write(record)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        # Child stderr is deliberately not a channel for URLs or genomic records.
        raise SystemExit(1)
