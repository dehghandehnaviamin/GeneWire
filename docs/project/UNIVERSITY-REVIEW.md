# University review handoff — local M2 snapshot

The owner will arrange the final university review. This document prepares the
current narrow implementation for reproducible inspection; it is not a statement
that the project or scientific review is complete.

## What can be demonstrated now

1. A Rust-backed Python client requests one zero-based half-open BAM interval
   through an existing htsget service and exposes provisional ordered bytes.
2. A supervised mature decoder consumes the complete transport, applies an
   explicitly matching mapped-read overlap filter and stages a new BAM output.
3. Output is promoted only after transport/decoder success and owned cleanup.
   A failed decoder cannot turn transport success into scientific approval.
4. An independently built local htsget-rs server and HTSlib's own retrieval/indexed
   paths match the five original synthetic truth cases below.

## Review fixture and independent expectations

The original fixture has one reference `chrSynthetic` of length 1,000 and four
mapped records: A covers [0,1), D covers [94,104), B covers [99,100), and C covers
[100,101). All generated records use simple all-match alignments. Each expected
name appears once; no real individual, sample or clinical information is used.

| Query | Interval | Expected selected names |
| --- | --- | --- |
| Q1 | [0,1) | A |
| Q2 | [99,100) | B, D |
| Q3 | [100,101) | C, D |
| Q4 | [499,500) | Empty, with valid BAM context |
| Q5 | [99,101) | B, C, D |

The server can return a superset. The downstream selection policy is essential.
An intentionally omitted D still produces decodable BAM and successful transport
but fails independent truth. Invalid BAM can transport successfully and fail the
decoder. Keep both negative controls in the review.

## Reproduce and inspect

- Follow [local setup and analysis commands](../development.md).
- Run the Rust and Python suites, then the independently built server runner.
- Inspect [raw interoperability](evidence/2026-11-27-interop.json) and
  [raw resource measurements](evidence/2026-11-27-resources.json), including source
  hashes, binary hash, server version discrepancy and evaluation limits.
- Inspect [native dependency metadata](evidence/2026-11-27-dependencies.json) as a
  target-specific feature/license inventory, not a security-audit certificate.
- Compare outcomes with the [M2 ledger](M2-LOCAL.md) and
  [draft requirement/scenario map](../spec/conformance.md).

Current evidence is macOS arm64 only. A Linux/macOS CI workflow is prepared;
remote runs, complete native resource accounting and wider qualification remain
open. One opaque resource run per mode is not a comparative performance result.

## Questions for the independent reviewers

- Does the mapped-read interval/filter policy fit the intended research workflow?
- Which additional CIGAR, clipping, pairing, supplementary/secondary alignment and
  duplicate/multiplicity cases are required before broader correctness claims?
- How should unknown references, aliases, reference identity and unmapped records
  be treated in an expanded subset?
- What upstream completeness and snapshot assurances must a real service provide?
- Which realistic synthetic workloads and independently chosen truth generators
  should precede performance evaluation?
- Which failure semantics and provisional-output handling are acceptable to the
  intended analysis consumer?

Record reviewer names only with consent, reviewed source revision, test additions,
findings, disagreements and unresolved questions in the decision/evidence register.
No endorsement, audit, clinical suitability or release approval is inferred.
