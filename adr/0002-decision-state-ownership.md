# ADR-0002: DecisionState Ownership

Status: `Accepted`

Date: 2026-07-30

Supersedes: none

Superseded by: none

---

## Context

[ADR-0001](0001-decision-immutability.md) established that Decisions are
immutable and that lifecycle state lives in a separate `DecisionState` record
keyed by `decision_id`.

It did not say who owns that record, and named the question as unresolved.

The gap matters because more than one consumer sees the same Decision. JARVIS
surfaces it in an Executive Brief. RestaurantOS may execute an Action from it.
A human may reject it in one place while another system is still holding it as
outstanding.

The obvious reading of ADR-0001 is one state record per Decision, holding the
current status. That reading has a problem: it requires every consumer to write
to the same record, which is the coordination problem ADR-0001 raised and then
deferred rather than solved.

---

## Decision

`DecisionState` records are owned per consumer, keyed by
`(decision_id, consumer_id)`.

Each consumer writes only its own records and never another consumer's.

Records are immutable. A status change appends a new record rather than editing
an existing one. The current state for a given pair is the record with the
latest `status_at`.

---

## Rationale

**1. "Accepted" is not one fact.**

JARVIS putting a Decision in a brief and RestaurantOS executing an Action from
it are different events, by different actors, at different times. A single
status field forces a choice about which of them the Decision "is" — and any
choice is wrong for the consumer that lost.

**2. The lost-update problem does not go away by itself.**

ADR-0001 rejected an in-place status field partly because multiple consumers
acting on one Decision invites lost updates. A single shared state record
reintroduces exactly that, one layer down. Per-consumer keys remove it
structurally: there is only ever one writer per key.

**3. Learning needs the actor, not just the outcome.**

The cognitive loop's fourth step asks whether recommendations were good. That
question is unanswerable without knowing who acted and who did not. A
recommendation accepted by the operator and ignored by the automation is a
different signal from one nobody saw.

**4. It keeps write boundaries aligned with repository boundaries.**

Each repository writes its own records. No repository needs write access to
another's state, which matches how `ecosystem.md` divides responsibility and
avoids a shared table that every service must coordinate around.

---

## Alternatives Considered

**One record per Decision, with a status field.**

The straightforward reading of ADR-0001. Rejected for reasons 1 and 2 above: it
needs many writers and it flattens distinct events into one.

**One record per Decision, holding a map of consumer to status.**

Preserves per-consumer detail in a single object, which makes "what is the state
of this Decision" a single lookup — genuinely the strongest argument against the
chosen design.

Rejected because the coordination problem is unchanged. Whoever owns that record
accepts writes from every consumer, so concurrent updates to different keys in
the same object still contend, and the ownership boundary in reason 4
disappears.

**Deriving state from the Action log alone.**

Already rejected in ADR-0001: a rejected Decision produces no Action, so
"declined" and "not yet seen" become indistinguishable. Restated here because it
is the option people reach for when they see how much machinery the alternative
requires.

---

## Consequences

**Positive.**

One writer per key, so no coordination and no lost updates. A per-consumer audit
trail that answers who acted and when. Write boundaries that match repository
boundaries.

**Negative.**

There is no single authoritative status for a Decision. Answering "what is
outstanding right now" becomes an aggregation across consumers, on top of the
supersedes resolution ADR-0001 already required. That is two levels of
indirection between a Decision and a simple answer, and it is the cost most
likely to prompt someone to revisit this.

A Decision can be accepted by one consumer and rejected by another. This is
accurate rather than contradictory, but any interface presenting a single status
is making an editorial choice and should say so.

**Neutral.**

Whether a recommendation actually worked is not recorded here. `DecisionState`
covers what was done, not what resulted.

---

## Open Questions

**Outcome recording.** Learning needs to compare recommendations against
results, and `executed` only says an Action was taken. A separate outcome record
is likely, and it is deliberately not specified here.

**Consumer identity.** `consumer_id` is pattern-validated but not registered,
unlike Decision categories. A registry becomes worthwhile once consumers
outnumber the handful in `ecosystem.md`.

**Retention.** Append-only transitions accumulate faster than Decisions do.
There is no volume pressure yet, so this is deferred rather than overlooked.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
