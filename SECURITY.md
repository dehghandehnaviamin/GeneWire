# Security policy

## Current support status

GeneWire is **experimental and pre-alpha, with a local prototype**. There are no
released or supported software versions, security audit results, production
guarantees, or independently verified security guarantees. No response-time SLA or bug
bounty is offered. Future release support will be documented before release.

## Report privately

Use [GitHub private vulnerability reporting](https://github.com/dehghandehnaviamin/GeneWire/security/advisories/new)
for potential vulnerabilities, sensitive design weaknesses, or accidental exposure.
If GitHub reporting is unavailable, contact the maintainer at
[amin.dehghandehnavi@gmail.com](mailto:amin.dehghandehnavi@gmail.com) with a minimal
description and ask for a suitable secure channel before sending sensitive details.
Email is not a promise of end-to-end confidentiality.

Include the affected document or future version/commit, impact, assumptions,
minimal reproduction using synthetic data, and any proposed mitigation. Omit
credentials and patient information. Do not publish exploit details in issues,
discussions, or PRs before coordination. Do not test against third-party systems
or datasets without authorization.

The maintainer will aim to acknowledge, assess, and coordinate remediation and
disclosure with the reporter, agreeing on timing and credit. No fixed response
deadline is guaranteed. Ask for an update through the same private channel if
needed. Disclosure should describe affected versions or design scope, mitigation,
remaining limitations, and credit only with the reporter's consent.

## Genomic privacy and design requirements

Genomic information and related metadata can be sensitive. Do not upload patient
data, sample identifiers, access tokens, private endpoints, or raw production logs.
Use synthetic examples and remove identifying metadata from reports and fixtures.

Future research must examine peer identity, authorization boundaries, encrypted
transport, integrity verification, replay and stale-checkpoint risks, bounded
resource use, cancellation, retention, and metadata exposure. These are unresolved
requirements. A checksum alone does not authenticate a peer, and encryption alone
does not authorize a transfer or establish consent.

The [M1 security model](docs/spec/security-model.md) proposes controls and
candidate tests for the initial regional-streaming subset. The
[local implementation ledger](docs/project/M2-LOCAL.md) records partial controls,
checks and gaps. These do not constitute an audit or production approval.

Access control, legal permission, consent, data minimization, retention, and
deployment policy cannot be inferred from successful data transmission. GeneWire
does not claim clinical suitability or regulatory compliance.
