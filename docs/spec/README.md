# M1 — Regional streaming design

**State:** Draft for review. **Design identifier:** GW-M1-DRAFT-01.
**Date:** 2026-11-26. The first local M2 implementation covers part of this design;
see [actual evidence and remaining gaps](../project/M2-LOCAL.md).

The owner instructed continuation after M0 publication. This is approval to
develop the reuse-first M1 design. Subsequent local continuation authorized M2;
external scientific sign-off and remote publication are not inferred. The proposed first path is a Rust htsget-oriented core
with a synchronous Python high-level extension.

| Document | Contract |
| --- | --- |
| [RFC 0001](../rfcs/0001-regional-streaming-profile.md) | Problem, proposal, alternatives and approval scope |
| [RFC 0002](../rfcs/0002-recoverable-bam-jobs.md) | Subsequent local M3 verified-source BAM jobs; separate from byte-stream resume |
| [Regional access profile](regional-streaming.md) | Inputs, upstream behavior, output meaning, resource limits and errors |
| [Stream lifecycle](stream-lifecycle.md) | State transitions, exposure boundary, retry, cancellation and final outcomes |
| [Rust/Python boundary](rust-python.md) | Runtime ownership, proposed API responsibilities, buffers and integration |
| [Security model](security-model.md) | Trust boundaries, abuse cases, mitigations and remaining risks |
| [Conformance plan](conformance.md) | Baselines, correctness gates and requirement-to-case mapping |
| [Candidate vectors](vectors/cases.json) | Machine-readable scenario expectations, not executable tests |

The three [architecture diagrams](../../assets/diagrams) now represent this
**proposed M1 subset**. They identify partial local components; their complete contracts remain design targets.

## Conventions and compatibility

Requirements marked P01–P18 are proposed GeneWire client requirements, not new
requirements imposed on htsget servers. GW-M1-DRAFT-01 is a document identifier,
not a network protocol version or a negotiated capability.

The client would reuse existing upstream HTTP/htsget behavior. No custom wire
encoding, negotiation field, endpoint, frame magic, port or IANA assignment is
defined. An unknown or unsupported feature must fail explicitly, not silently
select an incompatible profile. Draft APIs and defaults can change before any
release; there is no backward-compatibility promise yet.

## Evidence and sources

The design separates upstream facts from proposed client choices:

- [htsget 1.3.1](https://samtools.github.io/hts-specs/htsget.html): the reviewed
  upstream request, ticket and ordered-block mechanism.
- [HTTP Semantics, RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html):
  response status, ranges, validators and framing-related interpretation.
- [PyO3 0.30.1](https://docs.rs/pyo3/0.30.1/pyo3/) and
  [interpreter detachment](https://docs.rs/pyo3/0.30.1/pyo3/marker/struct.Python.html):
  a native Python interface and its ownership/attachment boundary.
- [Tokio 1.54.1 tasks](https://docs.rs/tokio/1.54.1/tokio/task/):
  cooperative cancellation and the distinction between signaling abort and joining.
- [reqwest 0.13.5 client configuration](https://docs.rs/reqwest/0.13.5/reqwest/struct.ClientBuilder.html):
  candidate controls for redirects, proxies, deadlines and content decoding.
- [samtools 1.25 manual](https://www.htslib.org/doc/samtools.html) and
  [view](https://www.htslib.org/doc/samtools-view.html): evaluation consumer and
  direct indexed-access baseline.
- [htsget-rs](https://github.com/umccr/htsget-rs): candidate local interoperability
  server, selected for future evaluation rather than deployed here.

Sources were rechecked on 2026-11-26. These reviewed versions are design inputs,
not by themselves a lockfile. The local prototype now pins actual dependencies;
its HTSlib decoder version differs from the reviewed manual. Further feature and
security review remains in the M2 ledger. No benchmark result from another project is a
GeneWire result. The broader prior-art record remains in
[M0 sources](../research/sources.md).

## Readiness

M1 produces reviewable contracts and candidate tests. It does not establish
scientific correctness, secure deployment, interoperability or performance.
See [the conformance gates](conformance.md#m2-entry-and-exit-evidence) before
implementation and [RFC review questions](../rfcs/0001-regional-streaming-profile.md#validation-and-open-review).
