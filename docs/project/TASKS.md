# Task register

This is a curated backlog, not a record of completed research. GitHub milestones
track the same sequence as [ROADMAP.md](../../ROADMAP.md). No deadline is promised.

## Bootstrap checklist

- [x] Inspect local Git state and preserve the existing `main` branch and remote.
- [x] Verify authenticated owner and the existing public, empty repository.
- [x] Prepare original branding and conceptual architecture diagrams.
- [x] Prepare README, contributor guidance, community files, and issue forms.
- [x] Record the approved license scope and preserve official license text.
- [x] Complete rendering, local/external link, template, and sensitive-content checks.
- [x] Configure topics, Discussions, private reporting, labels, and milestones.
- [ ] Inspect the complete staged diff, commit, and verify the remote push.
- [ ] Set the social preview through GitHub's repository settings.
- [ ] Obtain the owner's post-push approval before M0.

This checklist is a snapshot before publication. The bootstrap report records
completed remote operations; a later authorized edit can reconcile these boxes.

## M0 — Research and Feasibility (not started)

| Task | Concrete output / acceptance criteria |
| --- | --- |
| Define transfer use cases and boundaries | Short document naming actors, object dependencies, interruption scenarios, trust boundaries, and non-goals; no patient data |
| Compare existing standards and tools | Cited comparison of htsget/refget, established transports and file-transfer approaches; identify gaps and extension alternatives; avoid unsupported superiority claims |
| Specify synthetic evaluation workloads | Reproducible, privacy-safe workload plan with provenance, licensing, network/fault conditions, metrics and correctness checks; no benchmark claims |
| Record feasibility and scope decision | Reviewed go/no-go or extension recommendation, evidence, alternatives, risks and unresolved questions |

Do not execute these tasks until the bootstrap approval gate is satisfied.

## Later milestones

M1 requires a reviewed state model, wire proposal, resource limits and security
analysis. M2–M3 require implementation and fault evidence. M4 requires format and
domain review. M5 requires working contributor and user workflows. M6 requires
release validation. Decompose these into actionable issues when earlier evidence
establishes scope; do not create speculative placeholder issue activity.
