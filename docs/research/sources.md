# M0 primary-source register

**Accessed:** 2026-11-26. This register records what was reviewed, not a claim that
the documents represent every implementation or the newest member of every
standard family. No external specification is relicensed by linking it here.

| ID | Primary source and observed version | Reviewed scope / evidence limit |
| --- | --- | --- |
| S01 | [htsget specification](https://samtools.github.io/hts-specs/htsget.html), 1.3.1, printing revision 510c107; version history says July 2026 | Methods, parameters, block order/retries, security and service capabilities; no client/server conformance test |
| S02 | [samtools general manual](https://www.htslib.org/doc/samtools.html) and [view manual](https://www.htslib.org/doc/samtools-view.html), 1.25, released 2026-10-27 | Streaming, remote indexed access, region syntax and multiplicity; no binary selected or executed |
| S03 | [HTTP Semantics, RFC 9110](https://www.rfc-editor.org/rfc/rfc9110.html), June 2022 | Sections 13.1.5, 14 and 15.3.7; representation recovery, not application durability |
| S04 | [tus protocol](https://tus.io/protocols/resumable-upload), 1.0.0 | Core, checksum and expiration extensions; extensions are not universally deployed |
| S05 | [Amazon S3 multipart upload overview](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html), rolling service documentation | Part retry, completion, checksums and unfinished uploads; not proof of S3-compatible service parity |
| S06 | [rsync official manual](https://download.samba.org/pub/rsync/rsync.1), rolling manual | Partial-directory behavior and append caveats; runtime versions/options must be pinned later |
| S07 | [refget sequence API](https://samtools.github.io/hts-specs/refget.html), 2.0.0 | Sequence identifiers and retrieval; not the entire later refget suite |
| S08 | [DRS release drs-1.5.0](https://github.com/ga4gh/data-repository-service-schemas/releases/tag/drs-1.5.0), published 2025-03-25; [root schema](https://raw.githubusercontent.com/ga4gh/data-repository-service-schemas/drs-1.5.0/openapi/data_repository_service.openapi.yaml) and [DrsObject schema](https://raw.githubusercontent.com/ga4gh/data-repository-service-schemas/drs-1.5.0/openapi/components/schemas/DrsObject.yaml) | Blob/bundle metadata and access delegation; review uses the release tag rather than a moving development page |
| S09 | [BagIt, RFC 8493](https://www.rfc-editor.org/rfc/rfc8493.html), format 1.0, October 2018, Informational | Sections 2, 3 and 5; packaging and validation, not proof of active-adversary protection |
| S10 | [RO-Crate 1.3](https://www.researchobject.org/ro-crate/specification/1.3/index.html) and [introduction](https://www.researchobject.org/ro-crate/specification/1.3/introduction.html), Recommendation, published 2026-06-22 | Dataset/resource description and provenance; no recovery implementation evaluated |
| S11 | [Globus Transfer API](https://docs.globus.org/api/transfer/) v0.10 and [task submission](https://docs.globus.org/api/transfer/task_submit/) | Managed task and option-based integrity/encryption behavior; no service task submitted |
| S12 | [Crypt4GH file encryption specification](https://samtools.github.io/hts-specs/crypt4gh.pdf), printing 70fe9c5, 2019-10-21 | Container purpose and seekability; no cryptographic implementation review |
| S13 | [Digest Fields, RFC 9530](https://www.rfc-editor.org/rfc/rfc9530.html), February 2024 | Message-content versus representation integrity fields; not an authentication system |
| S14 | [QUIC, RFC 9000](https://www.rfc-editor.org/rfc/rfc9000.html), May 2021 | Streams and flow control; no transport benchmark |
| S15 | [SAM/BAM specification](https://samtools.github.io/hts-specs/SAMv1.pdf), 1.6, printing b5341fb, 2025-08-12 | Format and coordinate context for future fixtures; not comprehensive format certification |
| S16 | [CRAM specification](https://samtools.github.io/hts-specs/CRAMv3.pdf), 3.1, printing 07a4382, 2025-06-04 | Reference arrangements and indexing context; not every CRAM object needs an external reference |
| S17 | [VCF/BCF specification](https://samtools.github.io/hts-specs/VCFv4.5.pdf), VCF 4.5 / BCF 2.2, printing e821e4f, 2026-02-25 | Variant-format context; complex interval semantics remain a domain-review task |
| S18 | [PyO3 crate documentation](https://docs.rs/pyo3/0.30.1/pyo3/), 0.30.1, and [parallelism guide](https://pyo3.rs/main/parallelism.html), rolling guide | Native Python/Rust integration and interpreter detachment; local M2 now has a binding; a supported interpreter matrix remains unqualified |
| S19 | [maturin user guide](https://www.maturin.rs/), rolling guide | Packaging option for Rust extensions/mixed projects; reviewed as an M0 option; local M2 subsequently selected it |
| S20 | [Tokio crate documentation](https://docs.rs/tokio/1.54.1/tokio/), 1.54.1 | Candidate runtime and blocking-work boundaries; subsequently selected for local M2; not a throughput result |

## Version and interpretation cautions

The [GA4GH DRS product page](https://www.ga4gh.org/product/data-repository-service-drs/)
lists 1.4 as the last approved version, while the repository publishes the 1.5.0
release inspected above. This review distinguishes release availability from a
product approval label and makes no claim that 1.5.0 has that approval.

Format specifications, API versions, implementations and client command-line
coordinate syntax are separate compatibility dimensions. The selected sources
do not establish that all servers accept every listed format or extension.

For future experiments, pin source/implementation revisions and preserve the
effective configuration and fixture digests. Recheck rolling documentation before
publishing a conformance or operational claim. Negative findings here mean
"not established by this review", not that an ecosystem has no solution.
