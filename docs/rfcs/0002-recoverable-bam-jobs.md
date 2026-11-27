# RFC 0002 — Recoverable verified BAM jobs

**Local M3 design, 2026-11-27.** The owner authorized starting M3 after the
proposed recovery work. This increment remains local; prior M2 publication
approval does not authorize an unrelated M3 push, release or deployment.

## Contract and tradeoff

The first recovery boundary is a complete encoded regional BAM response, pinned
by an expected SHA-256 supplied through a trusted external channel. A partial
htsget response cannot safely be appended to a fresh ticket: the current source
contract has neither authenticated immutable representation identity nor durable
consumer offsets. Discard partial input and start a new query. Reuse only a fully
downloaded, closed, synced and hash-verified spool. This trades disk space and
time-to-first-analysis for a small, testable recovery boundary.

The digest authenticates bytes only insofar as its external provenance is trusted.
It does not prove the regional records are complete or the scientific query is
correct. An htsget service that returns varying BAM encodings requires a trusted
digest for the exact response; this API does not discover that digest or relax it.

## Local transaction

An explicit mode-0700 workspace is a sibling of the destination on a local POSIX
filesystem. One nonblocking advisory lock serializes cooperating job owners.
Fixed private files store input, result and a bounded versioned JSON receipt.
The receipt stores a hash of the service/object/region/destination/limits/policy,
not credentials, URLs, genomic identifiers or absolute paths. BAM spool/result
files themselves can contain sensitive data: use synthetic fixtures here and
control workspace access in any future deployment.

| Durable receipt | Recovery action |
| --- | --- |
| Downloading | Remove this job's incomplete artifacts; open a fresh query |
| Verified | Rehash source; remove provisional decoder output; repeat analysis locally |
| Ready | Rehash source/result; publish the completed result without overwriting |
| Committed | Verify the original result inode and bytes at the destination; return its receipt |

Write and fsync files, rename receipts atomically and fsync the workspace
directory. Sync the decoded result before recording Ready. Publish with a
no-overwrite hard link; sync the destination directory before recording
Committed. A crash between link and receipt is reconciled by matching the
retained result inode at the destination. Identical bytes in an unrelated inode
are not accepted as this job's publication. An error after link creation reports
visible output separately from confirmed sync completion.

Unknown versions, malformed/oversized receipts, request mismatches, symlinks,
unexpected workspace entries, changed/truncated spools and conflicting outputs
fail closed. Do not silently reset a verified receipt or overwrite user output.
The source and result remain retained for later receipt verification; total
file payload is bounded by input plus output budgets, apart from transient
metadata and filesystem overhead. There is no automatic retry loop or job daemon.

## Scope and failure evidence

Reuse the supervised M2 decoder/filter and its bounded cancellation, diagnostics
and output behavior. A local verified-file adapter is explicitly distinct from
the Rust network stream. A recovery receipt does not reconstruct an unobserved
network report. Recovered calls perform no new network request after Verified.

Test actual process termination at download, verified source, decoding, ready
result and post-link boundaries; stale/corrupt state, conflicting output,
concurrent owners, limits, ENOSPC and sync failures. Compare recovered decoded
records with the existing tiny oracle. Test a receipt retry after publication
without creating a new output inode or issuing another request.

This is process-crash recovery on controlled local filesystems, not proven
power-loss durability, network-filesystem correctness, arbitrary child-process
reaping, same-user adversarial mutation, generic exactly-once analysis effects,
byte-offset resume, acknowledgements on a new wire protocol, or complete M3 exit.
Do not kill a stored PID during recovery: it may have been reused. A hard-killed
supervisor's orphan decoder cannot publish the result, but reaping that orphan
is not promised. Keep the private directory and parent stable, do not replace its
lock inode, and treat hostile same-user mutation as outside this local model.

Python's documented primitives are [fsync/link/replace](https://docs.python.org/3.14/library/os.html)
and [advisory flock](https://docs.python.org/3.14/library/fcntl.html#fcntl.flock).
Successful fsync calls are recorded honestly; storage-device power-loss behavior
requires separate qualification. See [M3 evidence](../project/M3-LOCAL.md).
