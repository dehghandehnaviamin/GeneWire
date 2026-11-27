# Working on GeneWire

## Phase boundaries

This repository begins with documentation and assets only. Do not begin research,
protocol specification, or application development until the owner approves the
verified bootstrap. Then follow the approved milestone sequence in `ROADMAP.md`.
An initial push alone is not permission to start the next phase.

The owner approved M0 on 2026-11-26 and selected regional retrieval/streaming,
a Rust core and possible Python high-level integration. After M0 publication,
the owner instructed continuation into reuse-first M1 design. RFC 0001 and the
M1 contracts are the design basis for a local M2 prototype. The owner then
instructed local continuation and delegated product/business decisions. Proceed
with local implementation and checks; do not push, publish or deploy until later
authorization. Record choices and evidence in the decision register and M2 ledger.

On 2026-11-27 the owner explicitly authorized merging all prepared branches into
main and pushing main. That authorization covers the existing research, design,
prototype and accompanying publication-status updates; later unrelated pushes,
releases and deployments still require authorization.

The owner subsequently instructed continuing development and will arrange the
final university review. Continue local M2 engineering and prepare reproducible
evidence; do not treat the deferred review as scientific sign-off or a release
approval. Remote publication remains outside this later development instruction.

After the M2 follow-up plan, the owner explicitly approved completing resource
and process-failure checks, committing/pushing the prepared M2 changes, and
running CI on 2026-11-27. This authorization includes necessary CI fixes and
evidence/status updates on main. It does not authorize a release or deployment.

After the narrow M2 exit and Node.js 24 CI migration, the owner explicitly
instructed starting M3 recovery work. Continue local design, implementation and
failure checks for the verified BAM job subset in RFC 0002. Record evidence and
limits in the M3 ledger; do not infer M3 remote publication or release approval
from the earlier M2 push authorization.

Read `docs/project/STATUS.md`, `docs/project/TASKS.md`,
`docs/project/DECISIONS.md`, `CONTRIBUTING.md`, and `SECURITY.md` before work.
Keep status, roadmap, architecture diagrams, and contributor instructions aligned
with observed behavior. Label concepts and proposed interfaces explicitly.

## Work safely and honestly

- Inspect Git state and preserve existing work, history, and remotes.
- Never force-push or rewrite public history without explicit permission.
- Obtain owner approval for later remote pushes unless already authorized.
- Never add secrets, credentials, private genomic data, or machine-specific files.
- Prefer synthetic examples and retain source attribution and license notices.
- Do not invent benchmarks, tests, CI status, releases, contributors, or endorsements.
- Do not document install or development commands before they work.
- Keep changes small; use Conventional Commits and inspect the staged diff.
- Validate Markdown links, SVG structure, and rendered assets for documentation work.
- Future implementation changes require relevant behavior and failure-path checks.

## Tools and assets

Use `rg` for searches. Prefix shell commands with `rtk` where available; use
`rtk proxy` for commands without a specialized wrapper. Follow applicable local
environment instructions without committing machine-specific absolute paths.

SVG is the editable source of truth for visual assets. Retain accessible titles
and descriptions, fixed theme-safe surfaces, and readable labels. Regenerate
corresponding PNGs after visual changes and inspect actual renders. Keep temporary
rendering and validation scripts outside the repository during bootstrap.
