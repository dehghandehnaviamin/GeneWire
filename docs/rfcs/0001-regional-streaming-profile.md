# RFC 0001 — Regional streaming over htsget

**State:** Design direction adopted for local M2 evaluation; full conformance
and independent scientific/security review remain unclaimed.
**Date:** 2026-11-26.

## Problem and scope

The owner selected regional retrieval for analysis tools, a Rust core and Python
integration. The [M0 review](../research/README.md) found substantial existing
support for regional access. M1 should define a small interoperable client
contract rather than create a new binary protocol without evidence.

The first proposed path is one mapped-read interval, BAM output, and an existing
htsget service. The Rust core moves an ordered encoded stream; a Python caller
can feed a mature analysis decoder. Transport completion and completed analysis
are separate outcomes. Variants, CRAM/reference resolution, multiple intervals,
field/tag projection, persistent checkpoints and a new wire format are deferred.

## Proposal

1. Reuse the htsget 1.3.1 GET/ticket/data-block model with a documented restricted
   client policy. Do not add a GeneWire endpoint, header, frame or assigned port.
2. Prefer Tokio for Rust execution and PyO3/maturin for an initial synchronous
   Python extension. Keep the Rust core usable independently of Python.
3. Expose bounded encoded-byte reads and an explicit final report. Do not label
   raw upstream output as an exact regional subset or a cryptographically
   verified scientific result.
4. Retry a block only while none of that block's bytes have crossed the public
   output boundary. A failure after exposure terminates the attempt as incomplete.
   A new query never inherits an old query's prefix.
5. Keep credentials, outbound access, resource limits, cancellation and cleanup
   explicit. No default disk cache, automatic token renewal or persistent resume.
6. Validate later implementation against a real htsget server, direct HTSlib
   access, independent synthetic truth, and deterministic failure scenarios.

The detailed draft is in [the specification index](../spec/README.md).

## First consumer and completion policy

The proposed first consumer is a Python workflow reading bounded BAM byte chunks
and streaming them to a supervised, fully decoding analysis process, with
samtools as the initial evaluation candidate. This is a design assumption for
review, not an identified production deployment or a working Python API.

All early output is provisional. The caller must discard or explicitly invalidate
downstream results on failure. The proposed supervised integration reports
analysis success only after transport success, complete decoder consumption,
successful process exit and its declared selection policy. Persisting externally
visible scientific results before that gate is outside the initial contract.

## Alternatives and tradeoffs

| Alternative | Benefit | Reason for current disposition |
| --- | --- | --- |
| Existing tools/configuration only | Least maintenance | Still a valid outcome if the baselines meet requirements |
| Rust subprocess + Python wrapper | Process separation and language independence | Retained fallback if native packaging or lifetime complexity outweighs integration benefits |
| Native Python async API immediately | Natural workflow integration | Deferred to avoid approving an untested Python/Tokio event-loop bridge |
| Entire-block buffering before exposure | Can make block retry simpler | Large blocks can exceed memory; disk spooling adds privacy, storage and cleanup contracts |
| Automatic byte-offset resume across new tickets | Appears convenient | Output/source identity is not established merely by matching a logical query |
| New binary wire protocol | Full design control | No demonstrated unmet transport requirement in M0 |

The conservative retry rule prioritizes unambiguous output over transparent
recovery. The tagline remains an aspiration; durable resumability is not part of
this proposed first subset.

## Compatibility, security and scientific implications

The profile intentionally supports less than the complete upstream API. Rejected
formats, access destinations or redirects can be valid upstream; report a local
unsupported-policy condition rather than declaring the server nonconformant.
Never silently broaden a query or fall back to full-file retrieval.

Rust does not establish the safety of native dependencies or correctness of
biological interpretation. The external decoder, source/index consistency,
authorization policy and trust in source completeness remain explicit boundaries.
The [security model](../spec/security-model.md) records threats and residual risks.

## Validation and open review

The [conformance plan](../spec/conformance.md) and
[candidate vectors](../spec/vectors/cases.json) are design inputs. Selected
behaviors now have [local executable evidence](../project/M2-LOCAL.md).
No package, endpoint, throughput target or release is established by this RFC.
Owner review, domain review of expanded query semantics, actual baseline
provisioning and broader dependency/support qualification remain. The owner
authorized local implementation and delegated product/business decisions.

Local adoption is an engineering direction, not proof that every requirement is
implemented or an approval for remote publication.
