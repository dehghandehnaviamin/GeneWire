# Stream lifecycle and completion

**GW-M1-DRAFT-01 — Proposed, unimplemented.** This is a local application state
model, not a wire state machine imposed on the server.

## State model

| State | Allowed work | Next states |
| --- | --- | --- |
| NEW | Validate query/configuration and reserve a client slot | TICKETING, FAILED, CANCELLED |
| TICKETING | Obtain and validate one ticket | FETCHING, RETRY_WAIT, FAILED, CANCELLED |
| FETCHING | Fetch the next ordered block while there is payload credit | FETCHING, RETRY_WAIT, DRAINING, FAILED, CANCELLED |
| RETRY_WAIT | Discard eligible undelivered attempt bytes; wait within budget | TICKETING or FETCHING as recorded by retry_target, FAILED, CANCELLED |
| DRAINING | All blocks ended and HTTP checks passed; deliver remaining queued bytes | TRANSPORT_COMPLETE, FAILED, CANCELLED |
| TRANSPORT_COMPLETE | Terminal transport success; next read returns EOF | None |
| FAILED | Terminal unsuccessful attempt; reads raise the recorded failure | None |
| CANCELLED | Terminal canceled attempt; reads raise cancellation | None |

Terminal outcome publication is serialized. The first terminal transition wins.
A late cancel cannot turn an already completed transport into cancellation, nor
can late worker success erase an earlier failure. A consumer/decoder has its own
outcome; it can fail even when transport is complete.

**Success rule:** TRANSPORT_COMPLETE requires all ticket blocks checked and the
delivery queue fully drained. A worker reaching EOF on its last HTTP response
is insufficient while undisclosed output remains. DRAINING can be short-lived,
including when there are no outstanding payload chunks.

## Exposure boundary

Maintain per-query bytes delivered and per-block exposure history. A byte becomes
exposed when its owned chunk is committed to the public Rust reader or Python
binding, not merely when it arrives from the socket. Internal queue entries retain
their source block/attempt identity. The public API does not expose those labels.

An already committed concurrent read may finish after another thread observes
failure/cancellation. It counts as provisional partial output. No new handoff may
be committed after terminal failure. Do not claim cancellation retracts a Python
bytes object, a written pipe segment or an effect in a downstream tool.

## Retry admission

For a ticket request, retries are allowed only for transient transport failure,
429 or selected 5xx responses, before a ticket is accepted. For data, all of the
following must hold:

1. The request is an idempotent block GET in the same accepted ticket attempt.
2. No byte of that block has ever been exposed.
3. Buffered but undelivered bytes from the failed block attempt are discarded.
   Earlier blocks are preserved; their bytes are never replayed.
4. Destination, credentials and any observed representation validator still pass
   policy. A changed validator is not permission to splice an old prefix.
5. Attempt count and phase/overall deadlines allow the retry.

TicketInvalid, Unsupported, NetworkPolicy, ResponseInvalid, AccessDenied,
ResourceLimit, consumer failure and cancellation are not automatically retried.
Transient classification must not hide TLS, range or authorization failures.

Proposed waits are 1 s then 2 s for three total attempts, with a valid Retry-After
honored if its full wait fits the remaining budget. Otherwise fail rather than
retry earlier than the server requested. Every attempt rechecks outbound policy.
Transport-protocol retransmission is separate from application block retries.

After any current-block exposure, a data failure ends the query. It does not
return to RETRY_WAIT, refresh a ticket or append a new query's output. The caller
may start a fresh query only as new work and must invalidate the old analysis.

## Recovery examples

| Observation | Required outcome |
| --- | --- |
| No current-block bytes exposed, transient fetch failure, retry budget remains | Retry that block after discarding its undelivered bytes |
| Earlier block exposed, current block not exposed, transient current-block failure | Retry only the current block; never repeat the earlier one |
| Current-block prefix exposed, then connection drops | FAILED / TransportFailed, may_have_partial_output true |
| Entire HTTP result received but not fully consumed, caller closes | CANCELLED, not transport success |
| Fresh ticket after a failed exposed prefix | New query identity; old prefix cannot be reused |
| HTTP stream completes but BAM decoder rejects the result | Transport may be complete; analysis is failed |

No persistent checkpoint format or resume token is defined. Future M3 work must
specify durable state, authenticated source identity, consumer replay policy and
cleanup before promising more. Upstream retry guidance alone does not establish
these application-level guarantees.

## Cancellation, close and cleanup

Cancellation signals work to stop, wakes blocked readers and prevents new
handoffs. Discard queued undelivered bytes. A terminal outcome and cleanup status
are distinct: cleanup is NotStarted, InProgress, Complete or Failed. Query slots
remain occupied until tasks and buffers actually release their resources.

Explicit close requests cancellation unless transport is already complete and
joins owned tasks up to the cleanup budget. If joining times out, report
CleanupTimeout with cleanup still InProgress; do not release the slot or claim
the work stopped. A subsequent close can retry waiting. Client shutdown follows
the same rule across its queries.

A finalizer/drop may signal best-effort cancellation; it is not the deterministic
cleanup interface. Blocking work requires a separate termination strategy:
Tokio task cancellation is cooperative and started blocking work cannot simply
be aborted. [Tokio task semantics](https://docs.rs/tokio/1.54.1/tokio/task/).

## Consumer supervision

The proposed supervisor owns the analysis process lifecycle. It treats early
exit, failed writes, nonzero exit or failure to consume/decode the full stream
as ConsumerFailed. It cancels active transport and joins the process under a
bounded policy. If transport already completed, that status remains immutable,
but analysis still fails.

AnalysisComplete requires transport complete, full decoder consumption, exit
success and the declared filtering/output policy. Staged output is promoted only
after this gate. A transport-only report must not be interpreted as this gate.
An oracle match is recorded only in a controlled test with independent truth.

No exactly-once effects, rollback of arbitrary analysis tools or recovery from
process/power loss is promised. An operator who cannot invalidate provisional
effects needs a different integration contract before using this design.
