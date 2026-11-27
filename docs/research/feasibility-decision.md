# M0 feasibility recommendation

**Date:** 2026-11-26

**State:** Owner authorized proceeding with this direction into M1 design after
M0 publication. No independent domain review or experimental validation yet.

**Scope:** Regional retrieval and streaming, as selected by the owner.

## Recommendation

**Conditional go for a reuse-first M1 design review. Do not start a new binary
wire protocol on the evidence currently available.**

Explore GeneWire as a client/profile, interoperability and validation effort for
regional analysis access using existing mechanisms. Prefer a small upstream
contribution or integration guide if that satisfies the actual need. This is an
engineering inference from the comparison, not a claim of market demand, novel
research, runtime feasibility or measured advantage.

The owner authorized M0 and selected Rust for the core direction, with Python
as a possible high-level layer. M0 publication was approved and verified; the
subsequent continuation authorizes the [M1 draft](../spec/README.md).
The owner subsequently authorized local M2 work and delegated product/business
decisions. Full contract qualification and later publication remain separate;
see [current local evidence](../project/M2-LOCAL.md).
The original goal remains an open interoperable
ecosystem; whether it needs its own wire protocol remains an open evidence question.

## Evidence chain

| Observation | Implication for GeneWire | Evidence |
| --- | --- | --- |
| Existing regional APIs and indexed analysis clients overlap with the chosen use case | They are mandatory baselines, not competitors to dismiss | [Regional comparison](standards-comparison.md#regional-retrieval-is-the-lead-comparison) |
| Byte transport, data representation and scientific acceptance are different layers | A faster connection cannot by itself establish a complete correct result | [Requirements R01–R11](use-cases.md) |
| Durable recovery of a consumed stream raises source-identity and downstream-state questions | Test conservative restart and explicit failure before promising transparent resume | [Faults F1–F9](evaluation-plan.md#faults-and-acceptance-observations) |
| Packaging, reference lookup and object metadata already have substantial prior art | Reuse those concepts instead of claiming that manifests or hashes are novel | [Metadata alternatives](standards-comparison.md#genomic-context-and-metadata) |
| No GeneWire implementation or experiments exist | Performance, cost and production feasibility are unproved | [Study limits](README.md#reading-the-evidence) |

## Options considered

| Option | Benefit | Main cost / uncertainty | M0 disposition |
| --- | --- | --- | --- |
| Document/configure existing tools | Smallest maintenance burden | May already solve the entire need | Try first |
| Build an interoperable htsget-oriented client/profile | Focuses on analysis integration and testable failure behavior | Existing implementations may already suffice; feature gap unproved | Candidate for M1 review |
| Extend an existing protocol upstream | Keeps one ecosystem | Requires a concrete unmet contract and community coordination | Only after a documented gap |
| Create a new binary protocol and transport binding | Full control and potential educational value | Duplicated deployment, compatibility and security work; no measured need | Not justified for the selected use case |
| Broader multi-object bulk transfer product | Useful in a different scope | Not the owner's selected lead scenario | Secondary research only |
| Stop or narrow GeneWire | Avoids unnecessary infrastructure | May reduce standalone project scope | Valid outcome if baselines satisfy requirements |

A separate educational protocol experiment could be worthwhile, but the owner
selected analysis access as the lead application. Educational value must not be
presented as evidence that production genomic tools need a new protocol.

## Candidate M1 scope, subject to approval

Begin with one synthetic indexed alignment source, one region and a streaming
analysis consumer. Evaluate htsget interoperability and direct HTSlib access.
Define explicit incomplete-result behavior, bounded consumption and source-aware
recovery. Keep variant queries, CRAM reference integration and overlapping-region
policies as separate reviewable additions.

M1 may propose interfaces, state models, security boundaries and conformance
vectors, but must not silently approve an experimental wire extension. M0 has
not assigned a port, frame format, endpoint, package, checksum suite or stable API.
The owner-selected Rust core and optional Python integration replace the
Python/asyncio core proposal. The binding and runtime remain design choices;
there is no profiling evidence to attribute a bottleneck to language or justify
a new parser. See [technology direction](technology-direction.md).

## Entry criteria and outstanding review

M0 identified the following review needs. The owner authorized M1 to refine the
design while unresolved domain/deployment assumptions remain explicit:

1. The owner accepted advancing the regional-access/reuse-first direction into M1.
2. Name an initial analysis consumer and confirm whether a caller can discard
   provisional output after failure.
3. Review the one-interval truth fixture and intended result semantics with an
   appropriate domain reviewer; no such review is claimed yet.
4. Select actual baseline implementations, supported formats and a controlled
   environment; record their versions and capability limitations.
5. Decide which requirements need specification versus which are deployment,
   integration or documentation work. Keep a reasoned reuse/extension decision.

There are no named external reviewers, operational endpoints, budget commitments
or throughput targets. Permission to use real data is neither requested nor needed.
If domain review is unavailable, keep the associated scientific claims provisional
and do not label the phase scientifically verified.

## Reconsideration and stopping conditions

Narrow or stop new protocol work if baselines satisfy the requirements. Reopen
the wire decision only with a minimal reproducer of an unmet need, alternatives,
compatibility/security analysis and evidence explaining why an extension is
insufficient. A baseline failure caused by wrong coordinates, a stale index,
missing credentials or an unsupported configuration is not such evidence.

An inability to provision fair baselines prevents comparative conclusions.
Unresolved scientific semantics prevent correctness claims. Any future benchmark
must include failures, limits and reproducibility artifacts. The plan is in
[evaluation-plan.md](evaluation-plan.md); none of those experiments ran in M0.
