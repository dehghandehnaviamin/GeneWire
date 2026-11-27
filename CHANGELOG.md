# Changelog

Notable project changes will be recorded here. GeneWire has no software release yet.

## [Unreleased]

### Added

- First local Rust/Tokio htsget byte-stream core and synchronous PyO3/Python binding.
- Locked build/test dependencies, local development guide and M2 evidence ledger.
- Rust HTTP/failure checks and Python/native tests, including five tiny BAM queries
  and invalid-BAM/omitted-record negative controls. M2 remains in progress.

- Draft RFC 0001 and M1 profile/lifecycle, Rust/Python boundary, proposed security
  model and conformance plan with 30 unrun scenario expectations.

- Initial M0 use cases, primary-source comparison, synthetic evaluation plan,
  source register and proposed feasibility recommendation.
- Rust-core/Python-integration technology assessment following the owner's direction.

- Project overview, explicit pre-alpha status, conceptual architecture, and roadmap.
- Original SVG identity, README banner, social preview, and proposed design diagrams.
- Apache-2.0 licensing for original project material and third-party attribution.
- Contribution, governance, conduct, support, and security policies.
- GitHub issue forms, pull request template, and project decision/task registers.

The bootstrap itself contained no protocol or application implementation; the
later local M2 increment introduces the partial client described above.

### Changed

- M0 publication/owner continuation recorded; M1 is a draft for review.
- Three conceptual diagrams now show the proposed regional-streaming subset and
  distinguish transport completion from analysis/oracle outcomes.

- Lead use case is regional retrieval and streaming for analysis tools.
- Rust replaces the bootstrap's proposed Python/asyncio core; Python remains a
  possible high-level integration.
- Bootstrap approval/publication evidence and M0 review status are reconciled.
