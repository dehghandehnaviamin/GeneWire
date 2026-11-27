# Implemented contract review and planning boundary

Snapshot: 2026-11-27, D025. This reviews the existing single-region BAM contract;
it does not replace the draft profile or declare all of M3 complete. The owner
authorized autonomous execution until the defined work is exhausted and further
progress needs milestone replanning.

## Review of implemented choices

| Area | Reviewed behavior | Evidence and remaining boundary |
| --- | --- | --- |
| Query/admission | One named reference and zero-based half-open interval; BAM only; native and recovery reject dot-only IDs before work | [C27–C29 reference index](../spec/vectors/coverage-map.json); no multiregion, reference-alias or variant API |
| Retry | Three bounded ticket/block attempts; ticket attempts share one phase deadline; exposed current-block bytes forbid replay; fresh queries cannot splice a saved prefix | C03–C07 and C30; validators do not prove a global source snapshot |
| Destinations/credentials | Explicit immutable origin/IP pins, actual peer check, TLS verification, no ambient proxy/DNS/credentials; redirects stay at their original origin | C13–C16; no dynamic discovery or cross-origin credential remapping |
| Budgets | Bounded ticket/depth/block/header/read/result/time limits; logical accepted-payload window and copy accounting | C02, C11, C12, C19 and resource probes; allocator, HTTP, TLS, metadata and caller retention are not a process-memory cap |
| Terminal outcome/cleanup | Serialized output handoff and immutable terminal report; owned task cleanup is separate and query admission remains occupied after cleanup timeout | C20–C25; no hard termination guarantee for blocking kernel operations |
| Python/native lifetime | Python-owned immutable chunks, retained runtime, detached waits, one active reader; process tests create fresh clients | C21/C24/C25 and interpreter tests; inherited clients after fork, free-threading and subinterpreters remain unqualified |
| Supervised analysis | Full decode, mapped reference-span overlap and no-overwrite publication only after transport and decoder gates | C17/C18/C26 and B01–B16 below; arbitrary caller side effects cannot be rolled back |
| Recovery/storage | Private stable POSIX workspace/lock, externally pinned complete input, no offset splicing, original output inode/hash and recoverable source release | [M3 evidence](M3-LOCAL.md); Committed recovery no longer requires redundant input content |

The [machine-readable index](../spec/vectors/coverage-map.json) maps each candidate
C01–C30 to named tests with explicit subset limits. `tools/check_contract.py`
checks IDs and references structurally; it executes zero behavior tests. Actual
Rust/Python runs at the same source revision remain required. A mapping is not
exhaustive variant coverage, model checking, parser fuzzing or a security audit.
In particular C28 qualifies profile rejection, not nonexistent public APIs for
every proposed format/projection/multiregion argument.

## Expanded existing BAM policy

The policy remains MappedReadOverlapBam: include every mapped alignment whose
reference span intersects the requested half-open interval. Keep secondary,
supplementary, duplicate-marked and QC-fail records; exclude unmapped records
even if placed on a reference. Preserve record multiplicity, tested fields,
qualities, read-group tags and header. This selects alignments, not bases with
coverage: reference skips/deletions remain part of the span. It does not fetch
mates or deduplicate names. The expected cases are written before invoking the
production filter, and a separate indexed samtools region path must agree.

The original synthetic [B01–B16 tests](../../tests/test_bam_semantics.py) cover:

- Twelve explicit interval/reference cases: boundary inclusion/exclusion,
  repeated identical alignments, flags, skipped/deleted spans, clipping,
  insertion, zero-reference-consuming CIGAR, a second reference and empty output.
- A 6,000-record BAM larger than one I/O/BGZF block: recover after Verified,
  preserve the complete record multiset and avoid a new network request.
- A valid one-duplicate omission that passes analysis and fails the independent
  multiplicity oracle, plus truncated BAM and unknown-reference rejection.

Sources: [SAM/BAM 1.6, printing b5341fb, 2025-08-12](https://samtools.github.io/hts-specs/SAMv1.pdf)
defines alignment records, CIGAR reference consumption and one-base binning for
zero-reference-consuming CIGAR. The [samtools view manual](https://www.htslib.org/doc/samtools-view.html)
documents indexed region selection and its explicit one-based coordinates. The
actual locked comparison uses pysam 0.24.1 / HTSlib-samtools 1.24, not the manual's
newer executable version. These comparisons strengthen the existing BAM subset;
they add no CRAM/VCF/FASTQ/FASTA support or source-completeness proof.

## Where autonomous execution stops for replanning

After the D025 increment passes its local and observed cross-platform gates, the
concrete implementation/failure tasks of the current RFC 0002 subset are done.
The roadmap's broad full-M3 heading is deliberately still open. Its remaining
items change contracts or require an external target, rather than another
iteration of the same tiny-fixture/fault tests:

| Existing open area | Definition needed before executable work |
| --- | --- |
| Full M3 acceptance/acknowledgements | Define who acknowledges what, the supported storage failure model and filesystem/device qualification target; successful fsync calls and SIGKILL are not physical power-loss proof |
| Byte-offset/multi-object recovery | Define trusted source/version identity, authenticated replay/manifest contract and transaction/publication semantics; htsget tickets currently provide no safe cross-ticket splice contract |
| Production consumer and completeness | Select a real integration and its service/reference/query trust contract; synthetic success cannot invent a consumer or deployment evidence |
| M4 format extensions | Choose the next format and query shape, expected records/dependencies and independent baseline; the transport currently requests BAM only |
| M5 distribution/user workflows | Choose target interpreters/platforms and intended CLI/package interface; editable CI builds do not establish a distributable support matrix |
| M6 release/benchmarks | Define a release scope, controlled comparative workloads/hardware, dependency/security qualification and support policy; current resource probes are not comparative performance evidence |

The future milestone headings are not declared complete or silently removed.
This is the stopping boundary requested by the owner: review/redefine those
milestones from the observed implementation before starting a new architecture
or release track. External adoption, physical storage certification and broad
platform support cannot be fabricated through local autonomous work.

The prepared social card remains an unverified cosmetic bootstrap side task,
requiring authenticated repository-settings UI rather than the connected GitHub
API. It is not an engineering or release gate and is not counted as completed.
No credentials or private data are requested for tests.
