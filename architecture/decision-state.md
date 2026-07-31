# Decision State

Version: 1.0

---

# Purpose

A Decision records what an engine concluded. A DecisionState records what a
consumer did about it.

The two are separate because they have different authors.
[ADR-0001](../adr/0001-decision-immutability.md) established that Decisions are
immutable and that lifecycle belongs elsewhere.
[ADR-0002](../adr/0002-decision-state-ownership.md) established that elsewhere
is here, one record stream per consumer.

---

# Position in the Pipeline

```
   Decision  ──────────────┬──────────────┐
   (engine)                │              │
                           ▼              ▼
                        JARVIS       Application
                           │              │
                           ▼              ▼
                    DecisionState   DecisionState
                    consumer:jarvis  consumer:restaurantos
```

Each consumer writes its own stream. No consumer writes another's.

---

# Rules

**Records are immutable.** A status change appends a new record. Nothing is
edited after it is written.

**One writer per key.** The key is `(decision_id, consumer_id)`. Only the named
consumer writes records for that pair.

**Current state is the latest record** for a key, by `status_at`.

**There is no global status.** A Decision accepted by one consumer and rejected
by another is in both states, accurately. Any view that shows a single status is
choosing which consumer to speak for, and should say which.

---

# Structure

```
DecisionState
├── schema_version
├── state_id
├── decision_id
├── consumer_id
├── consumer_version
├── status
├── status_at
├── actor
│   ├── type
│   └── id
├── recommendation_id
├── action_ref
├── reason
├── metadata
└── created_at
```

---

# Fields

## schema_version

Semver of this specification. Required.

## state_id

`dst_` followed by a 26-character ULID.

```
dst_01J8ZB4M7XQK2N5R9T3V6W8YCD
```

Required.

## decision_id

The Decision this concerns. Must reference a real emitted Decision.

Required.

## consumer_id

The consumer whose stream this belongs to. Lowercase snake_case.

```
jarvis
restaurantos
barelytrade
```

Engines are not consumers. Atlas and Friday emit Decisions; they do not act on
them.

`consumer_id` is pattern-validated but not registered against a controlled list.
That is a known gap, recorded in ADR-0002.

Required.

## consumer_version

Semver of the consumer build that wrote the record.

Without it, a change in how a consumer interprets Decisions cannot be correlated
with a change in what it did about them.

Required.

## status

| Status | Meaning | Terminal |
| --- | --- | --- |
| `surfaced` | Presented to a human or queued for action | no |
| `accepted` | Approved to act on | no |
| `rejected` | Declined | yes |
| `executed` | An Action was carried out | yes |
| `failed` | Execution was attempted and did not succeed | no |
| `expired` | Passed `expires_at` without resolution | yes |

Legal transitions:

```
surfaced  →  accepted | rejected | expired
accepted  →  executed | failed | expired
failed    →  accepted | rejected
rejected  →  (terminal)
executed  →  (terminal)
expired   →  (terminal)
```

`failed` is not terminal because a failed execution is commonly retried, and a
retry that succeeds should not require inventing a new Decision.

Note what is absent. There is no `superseded` status: supersession is a fact
about the Decision, recorded on the Decision, and duplicating it here would
create two places to disagree.

Required.

## status_at

When the transition happened. RFC 3339, UTC, `Z` suffix.

Distinct from `created_at`, which is when the record was written. They differ
when a consumer records a transition after the fact — a batch reconciling
overnight executions, for instance.

Required.

## actor

Who caused the transition.

| Field | Required | Notes |
| --- | --- | --- |
| `type` | yes | `human` or `system` |
| `id` | no | Identifier of the person or process |

The distinction matters for learning. A Decision auto-executed under
`requires_approval: false` is weaker evidence about recommendation quality than
one a human read and approved.

Required.

## recommendation_id

Which of the Decision's recommendations was acted on.

Required when `status` is `executed`. A Decision may carry several
recommendations, and "executed" without naming which one is not a usable record.

Optional otherwise.

## action_ref

Reference to the Action that was carried out — an order id, a work order
number, a purchase order reference.

Required when `status` is `executed`. This is the link that lets outcome
analysis reach the real-world result.

Optional otherwise.

## reason

Why. Free text, 500 characters maximum.

Required when `status` is `rejected` or `failed`. A rejection without a reason
tells the engine nothing it can learn from, and an unexplained failure cannot be
diagnosed later.

Optional otherwise, and worth supplying on `expired` when the reason is known.

## metadata

Consumer-specific detail. An object with no fixed shape.

Nothing in the platform may depend on `metadata` for correctness. It exists so
consumers can record context without waiting for a schema change.

Optional.

## created_at

When the record was written. RFC 3339, UTC.

Required.

---

# Validation Rules

```
status_at            <= created_at
executed             requires recommendation_id and action_ref
rejected             requires reason
failed               requires reason
transitions          must follow the table above
status_at ordering   later records in a key have later status_at
state_id             unique
all timestamps       RFC 3339, UTC, Z suffix
```

Rules spanning multiple records are checked when a whole stream is validated
together. A single record cannot know what preceded it.

---

# Versioning

The rules from
[the Decision object specification](decision-object.md) apply unchanged:
consumers ignore unknown fields, tolerate unknown enum values, and accept any
record whose major version matches theirs.

A new status value is a minor change. Removing one, or changing what one means,
is major.

---

# Example

```json
{
  "schema_version": "1.0.0",
  "state_id": "dst_01J8ZB4M7XQK2N5R9T3V6W8YCD",
  "decision_id": "dec_01J8Z4K7M2QF9X3B7T5V0N6RCD",
  "consumer_id": "restaurantos",
  "consumer_version": "2.1.0",
  "status": "executed",
  "status_at": "2026-07-29T16:04:11Z",
  "actor": { "type": "human", "id": "usr_bgamache" },
  "recommendation_id": "rec_01J8Z4K7M2QF9X3B7T5V0N6RCG",
  "action_ref": "po_2026_07_1841",
  "created_at": "2026-07-29T16:04:11Z"
}
```

Full validating examples live in `schemas/examples/decision-state/`.

---

# Core Principle

> The Decision is what was recommended.
>
> The DecisionState is what someone did about it, and who that someone was.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
