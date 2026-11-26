# M0 — Research and feasibility

**Date:** 2026-11-26

**State:** Initial desk review complete; recommendation proposed for owner review.

The owner approved starting M0 after the verified bootstrap and selected
**regional retrieval and streaming for analysis tools** as the primary use case.
Whole-file exchange and dataset packaging are secondary comparisons. This
selection replaces the initial working assumption of bulk transfer as the lead
scenario.

The owner also selected a **Rust core with a possible Python high-level
integration**, replacing the bootstrap's Python/asyncio core proposal.

## Deliverables

| Deliverable | Purpose | Related issue |
| --- | --- | --- |
| [Use cases and requirements](use-cases.md) | Actors, query semantics, failure scenarios, trust boundaries and non-goals | [#1](https://github.com/dehghandehnaviamin/GeneWire/issues/1) |
| [Standards comparison](standards-comparison.md) | Cited alternatives, overlap, limits and reuse opportunities | [#2](https://github.com/dehghandehnaviamin/GeneWire/issues/2) |
| [Synthetic evaluation plan](evaluation-plan.md) | Workloads, correctness oracles, faults, metrics and reporting rules | [#3](https://github.com/dehghandehnaviamin/GeneWire/issues/3) |
| [Feasibility recommendation](feasibility-decision.md) | Conditional go for reuse-first design; no justification yet for a new binary wire protocol | [#4](https://github.com/dehghandehnaviamin/GeneWire/issues/4) |
| [Source register](sources.md) | Primary references, observed versions and evidence limits | All four |
| [Technology direction](technology-direction.md) | Rust/Python responsibilities, integration options and measurement questions | Cross-cutting owner constraint |

## Reading the evidence

**Owner requirement** means a preference supplied in the project conversation.
**Documented** means the cited standard or official manual describes the behavior.
**Proposed** means a GeneWire requirement, experiment, or design direction.
**Inference** means an interpretation of the reviewed material, not a measured
result or a claim that alternatives cannot implement the behavior.

No transfer, fixture generator, server, parser, benchmark, or conformance test was
implemented or run in M0. No patient dataset was accessed. External domain review
and a concrete deployment's constraints are still outstanding. Sources were read
on the date above; service documentation can change.

## Recommendation to review

Explore GeneWire as an interoperable client/profile and validation effort around
existing regional retrieval mechanisms. Require demonstrated unmet needs before
proposing wire extensions. Keep protocol conformance, genomic correctness,
pipeline completion, and cryptographic verification as separate claims.

The bootstrap diagrams remain conceptual discussion aids, not an approved M1
architecture. This directory contains no normative GeneWire API or wire format.
M1 has not started. Remote publication and closure of the GitHub issues require
separate review; a local research commit is not a published or accepted decision.
