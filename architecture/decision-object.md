# Decision Object

Version: 1.0

---

# Purpose

The Decision is the contract between engines and everything downstream.

Atlas and Friday produce Decisions.

Applications present them.

JARVIS synthesizes them into Executive Briefs.

`reasoning-model.md` names the Decision. This document specifies it.

Every field, constraint, and evolution rule defined here is binding on every
repository in the BarelySmash platform.

---

# Position in the Pipeline

```
Observations
     │
     ▼
  Insight
     │
     ▼
 Decision  ◄── this document
     │
     ├──────────────► Action        (application executes)
     │
     └──────────────► Executive Brief (JARVIS synthesizes)
```

A Decision carries its own evidence.

A consumer must never need to query the engine to understand why a Decision exists.

---

# Immutability

A Decision is immutable once emitted.

Engines never edit a Decision after publishing it.

Two consequences follow.

**Revision happens by replacement.**

To change a Decision, emit a new one with `supersedes` set to the prior
`decision_id`.

**Lifecycle state lives outside the Decision.**

Whether a Decision was accepted, rejected, or executed is a fact about the
*consumer*, not about the engine's reasoning. That state belongs in a separate
`DecisionState` record keyed by `decision_id`, owned by the application or by
JARVIS.

This mirrors the existing rule that Events are immutable, and it keeps engines
free of downstream concerns.

> The reasoning behind this choice, and the alternatives that were rejected
> along the way, are recorded in [ADR-0001](../adr/0001-decision-immutability.md).

---

# Structure

```
Decision
├── schema_version
├── decision_id
├── source
├── source_version
├── domain
├── category
├── priority
├── confidence
├── summary
├── rationale
├── evidence[]
│   ├── observation_id
│   ├── statement
│   ├── metric
│   └── source_ref
├── recommendations[]
│   ├── recommendation_id
│   ├── statement
│   ├── action_type
│   ├── parameters
│   ├── reversible
│   └── estimated_impact
├── requires_approval
├── supersedes
├── tags[]
├── created_at
└── expires_at
```

---

# Fields

## schema_version

The version of *this specification* the Decision conforms to. Semver.

Not the version of the engine. See `source_version` for that.

Required.

---

## decision_id

Globally unique. Format: `dec_` followed by a 26-character ULID.

```
dec_01J8Z4K7M2QF9X3B7T5V0N6RCD
```

ULIDs are chosen over UUIDs because they sort lexically by creation time, which
makes logs and object stores readable without a separate index.

The `dec_` prefix makes an identifier self-describing when it appears in a log
line, a URL, or a support conversation. Evidence and recommendations use `obs_`
and `rec_` on the same rule.

Required.

---

## source

The engine that produced the Decision.

| Value | Engine |
| --- | --- |
| `atlas` | Operational Intelligence |
| `friday` | Trading Intelligence |

JARVIS is never a valid source. JARVIS synthesizes Decisions. It does not
create them.

Required.

---

## source_version

The version of the engine build that produced the Decision.

Without this, a Decision cannot be reproduced or explained after a reasoning
change ships. Semver.

Required.

---

## domain

The subdomain inside the engine that reasoned about this. Lowercase snake_case.

Atlas examples: `beverage`, `labor`, `inventory`, `reservations`.

Friday examples: `equities`, `options`, `risk`, `portfolio`.

Required.

---

## category

The kind of decision, namespaced by engine.

```
atlas.inventory
atlas.labor
atlas.pricing
atlas.maintenance
friday.position
friday.risk
friday.allocation
```

Format: `<engine>.<category>`, lowercase snake_case after the dot.

Namespacing avoids a growing flat enum where terms collide across domains.
`position` means something precise in Friday and nothing at all in RestaurantOS.

The authoritative category registry lives in `glossary/`.

Required.

---

## priority

How much it costs to act late.

| Value | Meaning | Consumer behavior |
| --- | --- | --- |
| `critical` | Acting late causes irreversible loss | Surface immediately, out of band |
| `high` | Acting late causes measurable loss | Top of the next Executive Brief |
| `medium` | Value degrades slowly | Include in the regular brief |
| `low` | Informational | Include in the digest or roll-up |

Priority is defined by cost of delay, not by magnitude of impact. A large but
patient opportunity is `medium`. A small but closing window is `high`.

Required.

---

## confidence

The engine's estimated probability that the insight underlying the Decision
holds. A number from `0.0` to `1.0`.

| Range | Meaning |
| --- | --- |
| 0.90 – 1.00 | Near-certain. Evidence is direct and unambiguous. |
| 0.70 – 0.89 | Strong. Multiple independent signals agree. |
| 0.50 – 0.69 | Moderate. Signal is present, alternatives remain plausible. |
| 0.30 – 0.49 | Weak. Suggestive only. |
| below 0.30 | Do not emit. |

**0.30 is the emission floor.** An engine that cannot reach 0.30 has an
Observation, not a Decision.

**Confidence is not priority.** A near-certain low-stakes finding is
`confidence: 0.95, priority: low`. A speculative but time-critical one is
`confidence: 0.42, priority: critical`. Engines that collapse these two into one
number produce briefs that cannot be triaged.

Required.

---

## summary

One sentence. Imperative mood. 140 characters maximum.

This string is what lands in the Executive Brief, so it carries the weight.

Good:

```
Increase Casa Madero inventory by 6 cases ahead of the holiday window.
```

Bad:

```
It may possibly be worth considering whether inventory levels for certain
wine SKUs could potentially be adjusted upward at some point.
```

No hedging. No "consider." The Decision recommends; the human decides.

Required.

---

## rationale

Two to four sentences connecting the evidence to the recommendation.

Where `summary` says what to do, `rationale` says why the evidence supports it.

Optional, but strongly expected for `critical` and `high` priority.

---

## evidence

An array of the Observations that support the Decision. Minimum one item.

A Decision with no evidence is an opinion. Engines must not emit one.

Each item:

| Field | Required | Notes |
| --- | --- | --- |
| `observation_id` | yes | `obs_` + ULID. Traces back to the Observation record. |
| `statement` | yes | The observation in plain language. Factual, no interpretation. |
| `metric` | no | Structured form of the same fact. |
| `source_ref` | no | Pointer to the underlying record, report, or dataset. |

`metric` carries `name`, `value`, `unit`, `delta`, and `period`.

Keeping the structured metric alongside the plain statement lets applications
render a chart while JARVIS renders a sentence, from one payload.

Required.

---

## recommendations

An array of proposed courses of action. Minimum one item.

Each item:

| Field | Required | Notes |
| --- | --- | --- |
| `recommendation_id` | yes | `rec_` + ULID. |
| `statement` | yes | Imperative. What to do. |
| `action_type` | no | Names an executable Action the application supports. |
| `parameters` | no | Object. Arguments for that Action. |
| `reversible` | no | Whether the Action can be undone. Defaults to `false`. |
| `estimated_impact` | no | `value`, `unit`, `direction`, `horizon`. |

`action_type` is the seam between reasoning and execution. When it is absent,
the recommendation is advisory only and no automated path exists.

`reversible` defaults to `false` deliberately. An engine that has not thought
about reversibility should not have its recommendation auto-executed.

Required.

---

## requires_approval

Whether a human must approve before any Action executes.

Boolean. Defaults to `true`.

The existing rule stands: not every decision should automatically execute. The
default encodes it.

An engine may set this to `false` only when every recommendation in the Decision
is marked `reversible: true`.

Optional.

---

## supersedes

The `decision_id` this Decision replaces.

The superseded Decision remains in the record. It is not deleted.

Must reference a Decision from the same `source` and `category`.

Optional.

---

## tags

Free-form lowercase strings for filtering and grouping.

```
["holiday", "q4", "high-margin"]
```

Tags are for convenience. Nothing in the platform may depend on a tag for
correctness.

Optional.

---

## created_at

When the engine emitted the Decision.

RFC 3339, UTC, `Z` suffix.

```
2026-07-29T14:22:05Z
```

Required.

---

## expires_at

When the Decision stops being actionable.

RFC 3339, UTC. Must be later than `created_at`.

This field is what lets JARVIS assemble a brief that is actually current. A
Friday position call may expire within the session; an Atlas inventory call may
hold for a week. Without it, every brief accumulates stale recommendations and
the human learns to skim.

Omit it only when the Decision genuinely does not decay.

Optional.

---

# Validation Rules

An emitted Decision must satisfy all of the following.

```
evidence            length >= 1
recommendations     length >= 1
summary             length <= 140
confidence          >= 0.30 and <= 1.00
expires_at          > created_at, when present
supersedes          references same source and category
requires_approval   false only if every recommendation is reversible
all timestamps      RFC 3339, UTC, Z suffix
```

Validation failures are engine bugs. A Decision that fails validation is not
emitted, and the failure is logged against `source_version`.

---

# Versioning

`schema_version` is semver, and consumers are bound by two rules.

**Ignore unknown fields.**

A consumer that receives a field it does not recognize continues normally.

**Tolerate unknown enum values.**

A consumer that receives an unrecognized `category` or `source` degrades
gracefully — it renders the Decision without the category-specific treatment
rather than dropping or erroring.

Together these let engines ship ahead of applications, which they will.

Change classification:

| Change | Bump |
| --- | --- |
| New optional field | Minor |
| New enum value | Minor |
| New validation rule that existing valid Decisions already satisfy | Minor |
| Field removed or renamed | Major |
| Optional field becomes required | Major |
| Constraint tightened | Major |
| Semantics of an existing field change | Major |

Consumers must accept any Decision whose major version matches theirs.

---

# Example

Abbreviated. Full validating examples live in `schemas/examples/`.

```json
{
  "schema_version": "1.0.0",
  "decision_id": "dec_01J8Z4K7M2QF9X3B7T5V0N6RCD",
  "source": "atlas",
  "source_version": "0.4.1",
  "domain": "beverage",
  "category": "atlas.inventory",
  "priority": "high",
  "confidence": 0.81,
  "summary": "Increase Casa Madero inventory by 6 cases ahead of the holiday window.",
  "evidence": [
    {
      "observation_id": "obs_01J8Z4K7M2QF9X3B7T5V0N6RCE",
      "statement": "Casa Madero units sold rose 12% over the trailing four weeks.",
      "metric": {
        "name": "units_sold",
        "value": 214,
        "unit": "bottles",
        "delta": 0.12,
        "period": "P4W"
      }
    }
  ],
  "recommendations": [
    {
      "recommendation_id": "rec_01J8Z4K7M2QF9X3B7T5V0N6RCG",
      "statement": "Raise the next Casa Madero purchase order to 6 cases.",
      "action_type": "create_purchase_order",
      "parameters": { "sku": "CM-RES-750", "cases": 6 },
      "reversible": true
    }
  ],
  "requires_approval": true,
  "created_at": "2026-07-29T14:22:05Z",
  "expires_at": "2026-08-12T00:00:00Z"
}
```

---

# Core Principle

> A Decision recommends a course of action, carries the evidence for it, and
> states how much it trusts itself.
>
> Anything less is an Observation.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
