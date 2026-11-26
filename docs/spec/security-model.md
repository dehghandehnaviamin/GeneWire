# Proposed security and privacy model

**GW-M1-DRAFT-01 — Design model only.** No implementation exists to audit and
none of the controls below is verified. Private reporting remains in
[SECURITY.md](../../SECURITY.md).

## Assets and assumptions

Protect credentials, genomic payload, queried intervals/object identifiers,
provisional scientific results, local resources and the integrity of terminal
reports. The control service is selected by a trusted operator but its response
still needs validation. A remote endpoint, ticket, redirect, input record or
co-tenant may be malicious or faulty.

Valid TLS and a trusted service do not establish scientific completeness. P0
trusts the service's query semantics subject to independent synthetic evaluation;
it cannot prove absence of omitted real records. There is no signature scheme,
patient-consent system, key management service or compliance claim in this draft.

## Proposed outbound policy

Use HTTPS with certificate/hostname validation and TLS 1.2 or later; do not
expose a production "ignore verification" option. Operator-managed test trust
roots are distinct from disabling validation. Plain HTTP is permitted only by an
explicit isolated test configuration restricted to loopback; tests must prove
that this mode cannot leak into production configuration.

Require explicit allowed service/data origins and ports. Validate both normalized
hostnames and actual connection addresses against the configured network policy,
including IPv6, redirects and DNS changes. A name-only allowlist is not sufficient
to prevent access to disallowed internal/metadata destinations. DNS and connection
checks must bind to the actual socket; otherwise outbound-policy claims remain
unverified and deployment is blocked.

Disable automatic redirects, environment/system proxies, cookies and application
retries in the chosen HTTP adapter. Handle redirects explicitly with a finite
limit. Revalidate every hop. Origin changes require an operator rule and
destination-specific credentials; never reuse authorization blindly. Disable
Referer propagation and reject URL userinfo, unsupported schemes, malformed
headers and header injection.

Control credentials belong only to their configured control origin. Data requests
use only permitted per-block headers/credentials. Reject Host, Cookie,
Proxy-Authorization, hop-by-hop and connection-control overrides; do not bypass
policy to satisfy an unsafe ticket. Cap header count/size before sending. Header
name matching is case-insensitive. Never put credentials in default headers on
a shared general-purpose client.

These are local policy constraints. The upstream specification's credential and
redirect behavior does not make a ticket authority to access arbitrary resources.
A policy-rejected upstream response is not automatically a protocol violation.
[Upstream data-block rules](https://samtools.github.io/hts-specs/htsget.html#https-data-block-urls).

## Threats and proposed mitigations

| ID | Threat / boundary | Proposed control | Required evidence |
| --- | --- | --- | --- |
| T01 | Ticket/redirect accesses an internal service or metadata address | Explicit origin/address policy bound to the connection; no uncontrolled proxies | C14, C15; dual-stack and DNS-change tests |
| T02 | Control token leaks to data origin or redirect target | Separate clients/scopes; per-origin credential rules; sanitized diagnostics | C13, C14, C16 |
| T03 | Large/recursive ticket or stalled source exhausts resources | Ticket/depth/block/header/result limits; finite phase/overall budgets | C02, C11, C12, C19 |
| T04 | Partial data is replayed into an analysis as new output | Per-block exposure accounting; no replay after exposure; no cross-ticket checkpoint reuse | C04–C07 |
| T05 | Range/encoding mismatch silently duplicates or changes serialized bytes | Explicit response validation; HTTP decoding disabled | C08–C10 |
| T06 | Transport success masks broken/omitted scientific output | Separate transport/analysis/oracle levels; fully decoding controlled consumer | C17, C18; domain-reviewed truth expansion |
| T07 | Cancellation/FFI lifetime produces stale memory or orphan work | Owned outputs, serialized handoffs, task joins and truthful cleanup status | C12, C20–C25 |
| T08 | Query metadata or sensitive records enter logs/cache | No default persistence; redact URLs, headers, IDs, coordinates and payload | C16; failed-path inspection |
| T09 | Malicious source/index/reference yields a plausible wrong result | Scope restriction, independent truth and explicit service/dependency assumptions | C17–C18; later format-specific review |
| T10 | Dependency/build configuration weakens intended controls | Pin versions/features, review unsafe/native boundaries and test effective behavior | M2 setup/security review |

No local output path is accepted by the byte-stream core. A later filesystem
exporter must define traversal, symlink, permissions and atomic promotion policy
separately. No downloaded filename becomes a filesystem instruction.

## Residual risks and disclosure

An authorized but incorrect service can omit records undetectably without an
independent truth source. A downstream consumer can persist provisional output
or reveal query metadata. Libraries, TLS stacks, DNS resolvers and native tooling
remain dependencies. Python callers can retain unbounded returned output. Task
shutdown may exceed the wait budget; report it rather than claim termination.

P0 has no disk cache, durable checkpoint or persistent credential store.
Introducing one changes trust/privacy boundaries and requires a new reviewed
decision. Do not export payloads, tokens or failure logs to public services for
tests. Use controlled synthetic fixtures and credentials only.

This design is not a security audit, production approval or guarantee of privacy.
