# M2 cross-platform CI evidence

Evaluation date: 2026-11-27. The narrow reference implementation at
[da92bc9](https://github.com/dehghandehnaviamin/GeneWire/commit/da92bc9a1d56b51bed7f7035e980c71da026b424)
passed [workflow 45995255517](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/45995255517).
Both jobs finished with success. This evidence qualifies that tested revision;
later implementation or workflow changes require their own checks. The archived
result is not a substitute for observing subsequent workflow runs.

| Observed job | Rust | Python/native | Skips | Runtime |
| --- | --- | --- | --- | --- |
| [Ubuntu](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/45995255517/job/140492922731) | 47 passed | 34 passed | 0 | Ubuntu 26.04.1 x86_64, CPython 3.14.10 |
| [macOS](https://github.com/dehghandehnaviamin/GeneWire/actions/runs/45995255517/job/140492923229) | 47 passed | 34 passed | 0 | macOS 26.7.2 arm64, CPython 3.14.10 |

Both used Rust 1.93.0, uv 0.13.10, locked project dependencies, pysam 0.24.1 /
HTSlib 1.24, and independently built the pinned htsget-rs source. Each passed
formatting, clippy, local HTTP/native tests, supervised BAM tests, Q1–Q5 against
the real local server and two independent HTSlib paths, and the 64 MiB resource
probe in both caller-retention modes.

## Permanent evidence

[Run summary](evidence/ci-45995255517/summary.json) records job/commit/artifact
identity, observed test counts and archive/report hashes. The GitHub-reported ZIP
digest is metadata; the downloaded JSON was independently checked against source
file hashes and result gates. Archived JSON adds source_commit provenance and is
not claimed byte-identical to the original ZIP entries.

- Ubuntu: [interoperability](evidence/ci-45995255517/ubuntu-interop.json),
  [resources](evidence/ci-45995255517/ubuntu-resources.json).
- macOS: [interoperability](evidence/ci-45995255517/macos-interop.json),
  [resources](evidence/ci-45995255517/macos-resources.json).

Each returned the expected five name/multiplicity sets, with successful full BAM
decode/filter and cleanup. For both resource modes on both runners, each named
output-copy counter equaled 67,108,864 bytes, accepted payload peak stayed below
2 MiB, and retained payload was zero after close. These are logical accepted
payload/copy counts; allocator slack, HTTP/TLS/JSON buffers, decoder RSS and
caller retention remain separate. Raw RSS/tracemalloc/timings are single-run
observations, not an advantage claim or hard process-memory ceiling.

## M2 exit scope

The engineering exit applies to the implemented single-region BAM reference
path, not the entire provisional M1 contract or every variant of C01–C30.

| Minimum gate | Evidence |
| --- | --- |
| Working Rust/Python build and CI | Both observed jobs and locked setup |
| Real existing server and full decode | Pinned independent htsget-rs, supervised mature decoder |
| Independent tiny truth | Q1–Q5 and independent htsget/indexed HTSlib comparisons |
| Declared transport/failure policy | Strict ticket/range/length/encoding/credential checks, bounded retry/deadline, no replay after exposure, fresh-query separation |
| Native ownership and cleanup | Owned bytes/runtime lifetime, serialized handoff/cancel checks, cleanup timeout/retry, panic translation |
| Analysis/process failure | Early/nonzero exit, SIGKILL, SIGINT, timeout, output/diagnostic budgets, staging and filesystem failure checks |
| Resource and outbound-policy review | Named payload/copy accounting plus RSS probes; target-specific dependency inventory, pins and TLS/IPv6 tests |

M2's narrow engineering gate is complete under D018. M3–M6 remain planned.
Hard-killed supervisor crash recovery, arbitrary descendants, full allocator
accounting, broader APIs/platform qualification, security audits, comparative
benchmarks and production/release approval are not supplied by this CI run.
Scientific review remains deferred to the owner's university process.
