# Governance

GeneWire starts with a maintainer-led model. The initial repository owner and
maintainer is [Amin Dehghan (@dehghandehnaviamin)](https://github.com/dehghandehnaviamin).
There is no governing foundation, steering committee, or additional maintainer
roster at bootstrap.

## Maintainer responsibilities

Maintain a clear scope and roadmap; review contributions fairly; protect private
reports and scientific integrity; keep documentation aligned with evidence; manage
releases and repository access; enforce the Code of Conduct; and document material
decisions. Repository administration is not evidence of a scientific endorsement.

## Decisions

Discuss small, reversible changes in issues or pull requests. Substantial protocol,
transport, security, genomic-semantics, or compatibility decisions follow the
[lightweight RFC process](CONTRIBUTING.md#research-and-lightweight-rfcs). Seek domain
review and consensus, record alternatives and dissent, and leave reasonable time
for asynchronous international participation. No fixed response SLA is promised.

The maintainer makes the final decision when consensus cannot be reached, with a
written rationale in [DECISIONS.md](docs/project/DECISIONS.md). Accepted proposals
are not implementation claims. Reconsider a decision when new evidence changes
its assumptions. Contributors can request reconsideration in the original thread
or a linked issue with new evidence; conduct reports follow the private process
in [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Review and merge

All external changes receive maintainer review. Review considers scope,
correctness, scientific terminology, privacy, compatibility, licensing, evidence,
and documentation. Automated checks will be required when CI exists; there is no
CI workflow at bootstrap. For now, document manual checks. Security-sensitive
details stay in private advisories until coordinated disclosure.

The owner must approve the completed bootstrap before research begins. Later
agent-driven pushes require owner approval unless explicitly authorized for that
work. Never force-push or rewrite public history without explicit authorization.

## Future maintainers

Candidates should show sustained constructive contribution, sound technical
judgment, and respect for scientific integrity and private data. A public proposal
should state responsibilities and review evidence. Obtain the candidate's consent,
document the owner's decision, then grant the minimum necessary access. There is
no automatic promotion based on commit counts. Record additions and departures
here and review access when responsibilities change.

## Releases and continuity

Only maintainers may approve releases. Versioning, support windows, and signing
will be defined before the first alpha; none exist yet. If the owner becomes
unavailable, the community can use the Apache license to continue development in
a fork. Any transfer of the original repository requires the owner's participation.
