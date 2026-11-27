# Contributing to GeneWire

Thank you for helping make genomic data exchange easier to reason about.
GeneWire brings software and network protocol engineers together with
bioinformaticians, geneticists, computational biologists, security researchers,
technical writers, and performance engineers. Domain questions and documentation
reviews are as valuable as code.

> **Experimental · Pre-alpha · Research and Design.** This repository currently
> contains a local experimental Rust core, Python binding and tests alongside
> research/design documents. Follow [local development](docs/development.md) for
> verified setup/check commands and [M2 evidence](docs/project/M2-LOCAL.md) for
> exact scope. The narrow reference path passed [Linux/macOS CI](docs/project/CI-VALIDATION.md).
> No software release exists.

The subsequent [M3 job wrapper](docs/project/M3-LOCAL.md) has an observed
Linux/macOS CI run for its first subset. Changes to it require the recovery fault
harness in addition to the normal Python/native suite. Keep CI evidence tied to
its tested revision; full M3 qualification remains open.

The owner selected regional retrieval and streaming for analysis tools, a Rust
core and a possible Python high-level integration. See the
[research pack](docs/research/README.md) before proposing implementation or a new
wire protocol. Language direction does not imply a measured performance advantage.
The [candidate vectors](docs/spec/vectors/cases.json) describe expected scenarios;
they remain design inputs. Executable tests cover selected behaviors separately;
the JSON itself is not a test harness or valid BAM fixture set.

Please read the [Code of Conduct](CODE_OF_CONDUCT.md),
[status](docs/project/STATUS.md), [roadmap](ROADMAP.md), and
[security policy](SECURITY.md) before contributing.

## Find a useful contribution

| Area | Examples of useful contributions |
| --- | --- |
| Protocol design | State transitions, version negotiation, errors, RFC review |
| Networking | Transport comparisons, backpressure, cancellation, resource limits |
| Genomic integrations | Format semantics, reference identity, index dependencies |
| Security | Private vulnerability reports, abuse cases, checkpoint trust boundaries |
| Performance | Reproducible experiment plans, workload definitions, profiling |
| Testing | Future conformance vectors, fault models, synthetic fixture design |
| Documentation | Clear terminology, diagrams, accessibility, onboarding |
| Research | Primary-source reviews, evidence summaries, alternatives and limitations |
| Other languages | Independent implementation proposals after the specification is reviewable |

Use the repository's issue forms for bugs, features, protocol proposals, research,
and documentation. A bug today may concern a broken link or inconsistent diagram.
Do not report planned features as working software.

## Getting started

1. Find an existing issue or open a focused proposal. Discuss nontrivial work
   before investing in it. A maintainer can coordinate ownership; a public comment
   expressing interest is enough to begin coordination, and no one needs to be an
   organization member to contribute.
2. Fork `dehghandehnaviamin/GeneWire` using GitHub's **Fork** button.
3. Clone your fork. Replace `YOUR-USERNAME` in this working Git workflow:

   ```bash
   git clone https://github.com/YOUR-USERNAME/GeneWire.git
   cd GeneWire
   git remote add upstream https://github.com/dehghandehnaviamin/GeneWire.git
   git fetch upstream
   git switch -c docs/clarify-transfer-lifecycle upstream/main
   ```

4. Make a small change. Keep personal configuration, credentials, and datasets out
   of the repository. Use synthetic examples for scientific discussions.
5. Check the rendered Markdown, local links, image rendering, and factual claims.
   Run the applicable Rust/Python checks in the local development guide and describe
   documentation rendering/link checks honestly.
6. Commit using the convention below, then synchronize and publish your branch:

   ```bash
   git fetch upstream
   git rebase upstream/main
   git push -u origin docs/clarify-transfer-lifecycle
   ```

   Rebase only your own unpublished commits. If a branch is already shared, merge
   `upstream/main` into it or coordinate with collaborators; do not rewrite public history.
7. Open a pull request from your fork to upstream `main`. Fill in the template,
   link the issue, and respond to review. Draft PRs are welcome.

## Contribution workflow

```text
Find an issue → Discuss the approach → Coordinate ownership
     ↓
Create a feature branch → Make the change → Add relevant tests when tooling exists
     ↓
Run available checks → Open a pull request → Code review
     ↓
CI validation when configured → Maintainer merge
```

For documentation and assets, manual rendering and link checks are appropriate.
Implementation changes require meaningful automated tests. The reference CI
workflow has a verified Linux/macOS run; each later implementation change still
needs its own checks. Include applicable supervised-analysis and independent-server checks
from the development guide when changing the regional BAM path.

## Engineering standards

- **Quality:** keep changes focused, names explicit, and dependencies justified.
- **Types and language boundaries:** use explicit Rust types and ownership at core
  interfaces; future Python public interfaces should have type annotations.
  The local prototype uses Tokio/PyO3. Broader toolchain and interpreter support
  must be qualified before it is promised.
- **Tests:** test behavior and failure boundaries, including fragmented input,
  interruption, malformed lengths, cancellation, and corrupted recovery state.
- **Documentation:** update status, diagrams, and compatibility notes with behavior.
- **Compatibility:** identify wire changes and migration effects explicitly. Before
  a stable spec exists, do not imply backward compatibility. Later incompatible
  changes require versioning and review.
- **Security:** bound resource use, identify trust assumptions, and report exploitable
  weaknesses privately. Never include secrets or identifiable genomic data.
- **Genomic correctness:** specify coordinate conventions, reference identity,
  compression assumptions, and index relationships. Qualify expected behavior
  with independent fixtures and baselines; external review is an optional later task.
- **Performance:** supply a reproducible method and raw measurements. Include
  hardware, OS, dependency versions, workload, network conditions, repetitions,
  variability, and correctness checks. Label estimates and simulations clearly.

These are contribution expectations; consult the M2 ledger for observed behavior.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```text
feat(protocol): implement frame negotiation
fix(transfer): prevent invalid checkpoint recovery
docs(spec): clarify genomic coordinate semantics
test(codec): add fragmented frame test cases
perf(streaming): reduce buffer allocations
refactor(storage): isolate manifest persistence
```

These are message examples, not implemented capabilities. Use an imperative,
specific description. Mark breaking changes and explain their compatibility impact.

## Pull request requirements

Explain what changed and why; related issues; architectural, security, and
compatibility implications; testing or manual checks performed; and known
limitations. Use `Not applicable` with a reason when a category does not apply.
Attach before/after renders for visual changes. Keep generated PNGs synchronized
with SVG sources. Avoid unrelated reformatting and large, mixed-purpose patches.

Maintainer review is required before merging. Feedback should be actionable and
respectful. Contributors retain credit for their work; no approval or merge-time
guarantee is implied.

## Research and lightweight RFCs

Use the research form for experiments and the protocol form for substantial
protocol or specification changes. An RFC should cover:

1. Problem, use cases, and explicit non-goals.
2. Primary references and the limits of current evidence.
3. Proposal, alternatives, and interaction with existing standards.
4. State, wire, genomic, security, and compatibility implications as relevant.
5. Validation or experiment plan, success criteria, and unresolved questions.

Discuss first in an issue; after agreement on scope, submit a numbered Markdown
RFC under `docs/rfcs/` in a PR. [RFC 0001](docs/rfcs/0001-regional-streaming-profile.md)
is the first draft. Record outcomes in [DECISIONS.md](docs/project/DECISIONS.md). An accepted
proposal remains a design decision until implementation and verification exist.

This process applies to new protocol features, alternative transports, format
extensions, performance experiments, and specification amendments. See
[governance](GOVERNANCE.md) for decision-making and appeals.

## Scientific integrity and datasets

Make experiments reproducible. Verify dataset licensing and provenance before
using or linking to data. Prefer synthetic fixtures with documented generation
methods. Distinguish assumptions, published findings, measurements, and hypotheses.
Use accurate scientific terminology and disclose limitations and negative results.
Never fabricate research, benchmark results, or citations.

Do not contribute identifiable patient genomic data, clinical metadata, private
access tokens, or raw sensitive logs. Public availability alone does not establish
permission for redistribution. Adding a dataset exception to `.gitignore` requires
explicit maintainer review of licensing, privacy, and repository size.

## Licensing and attribution

Contribute only material you have the right to submit. Original contributions are
accepted under [Apache-2.0](LICENSE), matching the project. Identify third-party
sources and preserve required notices. Do not add a new license, CLA, or DCO
requirement without a documented maintainer decision. Attribute ideas and reviews
without inventing contributors or endorsements.

For general questions, see [SUPPORT.md](SUPPORT.md).
