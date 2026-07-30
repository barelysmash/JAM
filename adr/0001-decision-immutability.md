# ADR-0001: Decision Immutability

Status: `Accepted`

Date: 2026-07-30

Supersedes: none

Superseded by: none

---

## Context

Atlas and Friday emit Decisions. JARVIS and the applications consume them.

Downstream, a Decision accumulates state that the emitting engine knows nothing
about. Someone accepts it. Someone rejects it. An application executes an Action
derived from it, or the recommendation is quietly ignored until it expires.

The question is where that state lives.

The obvious answer is a `status` field on the Decision itself, flipped in place
as the Decision moves through its life. It is one record instead of two, one
query instead of a join, and it is what most systems do.

Two things made that answer less obvious than it looked.

The ontology already declares Events immutable. Decision sits two steps from
Event in the same pipeline, and giving adjacent concepts opposite mutability
rules is the kind of inconsistency that produces bugs for years.

More importantly, the platform's motto commits it to learning. Learning from a
Decision requires comparing what was recommended against what actually
happened — which requires the original recommendation to still exist in the
form it was made.

---

## Decision

A Decision is immutable once emitted.

Lifecycle state lives in a separate `DecisionState` record keyed by
`decision_id`, owned by the consumer.

Revision happens by emitting a new Decision whose `supersedes` field names the
one it replaces. The superseded Decision remains in the record.

---

## Rationale

**1. Mutation destroys provenance.**

A Decision is a claim an engine made at a specific moment, from specific
evidence, at a specific `source_version`. Editing it after the fact erases what
was actually recommended and leaves no way to tell that anything changed.

The cognitive loop's fourth step is *Learn*. Without an intact record of past
recommendations, there is nothing to learn from — only a record of what the
system currently believes, which is exactly the thing that needs auditing.

**2. Lifecycle state belongs to the consumer, not the producer.**

Whether a Decision was accepted is a fact about the human or application that
received it. It says nothing about the engine's reasoning.

Writing it onto the engine's output inverts the dependency: applications would
need write access to the reasoning layer's records, and the boundary between
producing intelligence and acting on it — which `ecosystem.md` is built
around — stops being enforceable.

**3. Consistency with Event.**

Events are immutable by existing rule. A pipeline in which the first stage
cannot be edited but the third can invites the assumption that any stage can be,
and that assumption will eventually be made by someone reading quickly.

**4. Multiple consumers, one Decision.**

JARVIS may surface a Decision in a brief while an application acts on it
independently. An in-place status field makes that a lost-update problem. Keyed
state per consumer does not.

---

## Alternatives Considered

**A mutable `status` field on the Decision.**

Rejected. It is the cheapest option and it defeats the primary purpose of the
record. Every argument above applies directly to it.

**An append-only history array embedded in the Decision.**

Keeps the full record while retaining a single object, which is genuinely
appealing. Rejected because consumers would still be writing into the engine's
output, so the ownership problem in point 2 survives intact — and the Decision
would grow without bound, which is a poor property for something JARVIS loads in
volume to assemble a brief.

**Deriving state entirely from Actions taken.**

If an Action references the Decision that motivated it, current state could be
inferred from the Action log without any state record at all.

Rejected because rejection produces no Action. A Decision that was seen and
declined would be indistinguishable from one nobody has looked at yet, and the
difference between those two matters more than almost anything else the state
record would capture.

---

## Consequences

**Positive.**

The full history of what was recommended survives, so recommendation quality can
be measured against outcomes rather than asserted. Engines are write-only with
respect to their own output, which keeps the producer and consumer boundary
clean. A supersedes chain reads as an audit trail of how thinking changed.

**Negative.**

Two records where one would do. Any view of current state requires resolving
both the supersedes chain and the `DecisionState` record, which makes the
simplest possible query — "what is outstanding right now?" — meaningfully harder
than a `WHERE status = 'open'`.

Storage grows monotonically, and superseded Decisions accumulate with no
retention rule yet defined.

**Neutral.**

`DecisionState` is named here but not specified. This decision creates that
obligation without discharging it.

---

## Open Questions

**What `DecisionState` actually contains.** Status vocabulary, who transitioned
it, when, and whether a rejection carries a reason. Needs its own specification
alongside `architecture/decision-object.md`.

**Who owns it.** JARVIS assembles the briefs and so knows what was surfaced;
applications execute and so know what was acted on. One record with two writers
or two records with one each — unresolved. Resolving it likely requires knowing
whether JARVIS is a service or a synthesis step, which is itself undecided.

**Retention.** Immutable and unbounded are a bad pair over a long enough
horizon. There is no volume pressure yet, so this is deferred deliberately
rather than overlooked.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
