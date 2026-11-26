# Existing standards and reuse opportunities

**Review date:** 2026-11-26. **Method:** primary-source desk review, no runtime tests.
Versions and source limitations are recorded in [sources.md](sources.md).

The comparison is scoped to the owner's regional-streaming priority. The
GeneWire dispositions are **inferences and proposals**, not findings of missing
features across an entire ecosystem. “Not specified here” means the reviewed
layer does not establish that contract; an implementation or extension may do so.

## Regional retrieval is the lead comparison

**Documented evidence — htsget 1.3.1:** a ticket describes ordered data blocks;
clients can retry failed blocks. A region response can include additional records,
and an empty result still has a valid formatted response. Capabilities and
temporary data-endpoint credentials need explicit handling.
[Methods](https://samtools.github.io/hts-specs/htsget.html#methods),
[data blocks and reliability](https://samtools.github.io/hts-specs/htsget.html#response-data-blocks),
[security](https://samtools.github.io/hts-specs/htsget.html#security-considerations).

**Inference:** regional streaming and block retry alone cannot establish a novel
GeneWire protocol. The relevant question is whether an interoperable client or
profile can make recovery and analysis completion easier to validate. Existing
htsget clients and direct indexed access are counterexamples that must be tested,
not assumed inadequate.

**Documented evidence — samtools 1.25 / HTSlib:** the tools support streams and
remote indexed alignment access; regional reads require suitable sorted/indexed
input. Options and multi-region modes affect output multiplicity. This is a
directly relevant baseline, not merely a fixture-creation tool.
[General manual](https://www.htslib.org/doc/samtools.html#DESCRIPTION),
[view manual](https://www.htslib.org/doc/samtools-view.html).

| Candidate | Role in this study | Recovery / integrity evidence | Proposed disposition |
| --- | --- | --- | --- |
| htsget | Primary existing regional API | Documented block retry; no tested GeneWire cross-process checkpoint contract | First interoperability baseline; evaluate reuse before extension |
| Direct HTSlib remote indexed access | Existing analysis-access alternative | Implementation/configuration-dependent; not exercised here | Compare query correctness, stream failure and resource behavior |
| HTTP range + validators | Byte retrieval building block | Conditional retrieval of a representation; application state still needed | Reuse when the serialized source identity is established |
| refget sequence API | Reference lookup by sequence identity | Addresses sequence lookup rather than analysis-stream completion | Evaluate as a dependency integration, not a competing transfer engine |
| DRS | Object resolution, metadata and bundles | Resolves access methods; actual data transfer is delegated | Evaluate when a deployment needs portable object resolution |

No row means conformance has been verified. There is no numerical product score
or benchmark ranking.

## Transport and whole-object alternatives

**HTTP semantics, RFC 9110:** Range addresses representation bytes, not genomic
coordinates. Servers may ignore it. If-Range uses a strong validator to decide
whether a partial response is appropriate; a full response can replace the range
request. A receiver must validate status, range and representation identity rather
than blindly append. These semantics are useful building blocks, not a durable
resume engine. [Sections 13.1.5 and 14](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.5).

**tus 1.0.0:** defines resumable HTTP uploads using server-reported offsets. Its
checksum and expiration extensions are optional, and authentication is delegated.
It is an upload alternative for UC07, not the primary regional-download solution.
An offset is not proof of GeneWire's desired final scientific result.
[Core and extensions](https://tus.io/protocols/resumable-upload).

**Amazon S3 multipart upload:** retries individual parts and completes an object;
unfinished uploads need completion or cleanup. The completed ETag is not
necessarily an MD5 of object data; explicit checksum facilities are distinct.
This is storage-specific upload behavior, not a genomic query interface or a
guarantee that another S3-compatible service behaves identically.
[Official overview](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html).

**rsync:** partial-file retention and delta reuse make it a whole-file comparison.
Its append modes have assumptions that make them unsuitable as an automatic
general recovery policy. SSH configuration, versions and checks remain part of
the deployment. It does not supply the chosen regional analysis API.
[Official manual](https://download.samba.org/pub/rsync/rsync.1).

**Globus Transfer API v0.10:** already provides managed transfer tasks. Submission
supports encryption and checksum-verification settings, with behavior dependent
on endpoint policy and submitted options. This counters any claim that GeneWire
invented reliable multi-file orchestration. Account, endpoint and service
requirements must be assessed; no task was submitted or cost incurred.
[API](https://docs.globus.org/api/transfer/),
[submission fields](https://docs.globus.org/api/transfer/task_submit/).

## Genomic context and metadata

**refget sequence API 2.0.0** uses sequence-derived identifiers for reference
retrieval. This review covers that API, not every product now grouped under the
refget name. Sequence identity and a serialized file's byte digest serve different
purposes. [Sequence API](https://samtools.github.io/hts-specs/refget.html).

**DRS 1.5.0** describes blobs, access methods, checksums and nested bundles. Its
bundle checksum does not bind member names in the same way as an arbitrary
manifest serialization. Do not invent a parallel object catalog without first
testing whether DRS is sufficient. A DRS response does not, by itself, demonstrate
the future client's cache isolation or stream-completion behavior.
[Released object schema](https://raw.githubusercontent.com/ga4gh/data-repository-service-schemas/drs-1.5.0/openapi/components/schemas/DrsObject.yaml).

**BagIt 1.0 / RFC 8493** already defines payload manifests, completeness, checksum
validation and optional remote-fetch lists. It is an informational packaging
specification, not a new network transport or protection against an active
attacker. Therefore “manifest plus hashes” is not a sufficient novelty claim.
[RFC 8493](https://www.rfc-editor.org/rfc/rfc8493.html).

**RO-Crate 1.3** describes datasets and related resources through JSON-LD metadata.
Evaluate reuse for provenance and relationships rather than inventing another
metadata vocabulary. It is not, by itself, the selected recovery state machine.
[Specification](https://www.researchobject.org/ro-crate/specification/1.3/index.html),
[introduction](https://www.researchobject.org/ro-crate/specification/1.3/introduction.html).

## Security and transport boundaries

Crypt4GH defines an encrypted genomic-file container with seekable access. It
does not replace deployment authorization or establish the client's completion
contract. Plaintext content, encrypted serialization and decoded records need
separate identity and verification policies.
[File encryption specification](https://samtools.github.io/hts-specs/crypt4gh.pdf).

RFC 9530 distinguishes digests of HTTP message content and of a representation.
Neither should be described as automatically authenticating an untrusted
manifest. Algorithm and trust-source choices remain M1 decisions.
[Digest Fields](https://www.rfc-editor.org/rfc/rfc9530.html).

QUIC has multiplexed streams and flow control; it does not define genomic query,
persisted recovery or scientific acceptance semantics. Adding a QUIC binding now
would add a comparison variable without evidence of a transport bottleneck.
[RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html).

## What remains unproved

The reviewed sources establish substantial overlap with GeneWire's initial
aspirations. A candidate opportunity is a small, testable regional-streaming
integration contract covering input semantics, bounded consumption, explicit
incomplete results and conservative recovery. This is **a hypothesis**. It could
be satisfied by existing tools, configuration, documentation, or upstream work.

Use the [evaluation plan](evaluation-plan.md) to disprove the hypothesis as readily
as to support it. No source review here establishes lower latency, less memory,
faster recovery, universal compatibility or a need for a new binary protocol.
