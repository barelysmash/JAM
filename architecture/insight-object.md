# Insight Object

Version: 1.0

---

# Purpose

An Observation is a measured fact. A Decision is a recommended action. An
Insight is the interpretation that connects them.

`glossary/ontology.md` names it. `architecture/reasoning-model.md` places it.
This document specifies it.

[ADR-0004](../adr/0004-insight-as-a-contract.md) records why it became a
contract rather than remaining prose inside a Decision.

---

# Position in the Pipeline

```
Observations
     │
     ▼
  Insight   ◄── this document
     │
     ├──────────► Decision
     ├──────────► Decision
     └──────────► Decision
```

One Insight may support several Decisions. That is the point of separating it.

---

# What Qualifies

An Insight makes a claim that goes beyond what was measured.

```
Observation   Wine receipts rose 12% over four weeks.
Insight       Premium sampling is lifting wine attachment.
Decision      Extend the sampling program to Thursday service.
```

The Observation is checkable against a record. The Insight is an argument about
why, and could be wrong while every Observation supporting it is correct.

Restating a measurement in different words is not an Insight. If removing the
interpretation leaves the same information, there was no interpretation.

---

# Immutability

Insights are immutable once emitted, on the same terms as Decisions.

Revision happens by emitting a new Insight with `supersedes` set to the prior
`insight_id`. The superseded Insight remains in the record, because Decisions
already cite it and the reasoning behind those Decisions must stay recoverable.

---

# Structure

```
Insight
├── schema_version
├── insight_id
├── source
├── source_version
├── domain
├── statement
├── confidence
├── method
├── evidence[]
│   ├── observation_id
│   ├── statement
│   ├── metric
│   └── source_ref
├── supersedes
├── tags[]
├── created_at
└── expires_at
```

---

# Fields

## schema_version

Semver of this specification. Required.

## insight_id

`ins_` followed by a 26-character ULID.

```
ins_01J8ZC5N8YRBGA2S3BNXP4FJQC
```

Required.

## source

The engine that produced it: `atlas` or `friday`.

JARVIS is never a source. It synthesizes; it does not interpret.

Required.

## source_version

Semver of the engine build. Required, for the same reason it is required on a
Decision: an interpretation cannot be reproduced or explained after a reasoning
change ships without it.

## domain

The subdomain that reasoned about this. Lowercase snake_case.

Required.

Note that an Insight has **no category**. Categories classify what kind of
action is being recommended, and an Insight recommends nothing. The Decisions
that cite it carry the categories.

## statement

The interpretation. One sentence, declarative, 200 characters maximum.

Declarative rather than imperative — the contrast with a Decision's `summary` is
deliberate.

```
Insight     Premium sampling is lifting wine attachment on weekend service.
Decision    Extend premium sampling to Thursday service.
```

An Insight that reads as an instruction has skipped a step.

Required.

## confidence

Estimated probability that the interpretation holds. `0.0` to `1.0`.

**There is no emission floor.** This differs from Decisions deliberately.

A Decision below 0.30 should not be emitted, because recommending action on thin
grounds is worse than staying silent. An Insight is not asking anyone to act,
and a tentative interpretation is often worth recording — it is exactly the kind
of thing that becomes interesting when a later observation confirms it.

Confidence is derived by the engine from signal agreement, sample size, and data
recency. It is never a free-form number from a language model. See
`standards/prompt.md`.

Required.

## method

How the interpretation was reached. Lowercase snake_case.

```
trend_extrapolation
threshold_breach
correlation
seasonal_comparison
cohort_contrast
```

Optional, and worth supplying. When a class of interpretation turns out to
mislead, `method` is what makes that visible across many Insights at once.

## evidence

The Observations supporting the interpretation. Minimum one item.

Identical in shape to Decision evidence: `observation_id` and `statement`
required, `metric` and `source_ref` optional.

An Insight with no evidence is a belief. Engines must not emit one.

Required.

## supersedes

The `insight_id` this Insight replaces. Must share `source` and `domain`.

Optional.

## tags

Free-form lowercase labels. Nothing may depend on a tag for correctness.

Optional.

## created_at

RFC 3339, UTC, `Z` suffix. Required.

## expires_at

When the interpretation should no longer be relied on.

Interpretations decay more slowly than recommendations, so this is often absent
where the equivalent field on a Decision would be set. A seasonal pattern may
hold for a year; the decision to act on it expires in a week.

Must be later than `created_at`.

Optional.

---

# Validation Rules

```
evidence           length >= 1
statement          length <= 200
confidence         >= 0.0 and <= 1.0
expires_at         > created_at, when present
supersedes         references same source and domain
all timestamps     RFC 3339, UTC, Z suffix
```

---

# Relationship to Decision

A Decision cites the Insights it rests on through `derived_from`, an array of
`insight_id` values.

`derived_from` is optional. An engine that does not model interpretation
separately may emit Decisions without it, and existing Decisions remain valid.

A Decision's `evidence` continues to carry Observations directly. The two arrays
answer different questions: `evidence` is what was measured, `derived_from` is
what was concluded.

The relationship between a Decision's confidence and the confidence of its
supporting Insights is deliberately unspecified. See ADR-0004.

---

# Example

```json
{
  "schema_version": "1.0.0",
  "insight_id": "ins_01J8ZC5N8YRBGA2S3BNXP4FJQC",
  "source": "atlas",
  "source_version": "0.4.1",
  "domain": "beverage",
  "statement": "Premium sampling is lifting wine attachment on weekend service.",
  "confidence": 0.74,
  "method": "cohort_contrast",
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
  "tags": ["sampling", "weekend"],
  "created_at": "2026-07-29T14:20:00Z"
}
```

---

# Core Principle

> An Observation can be verified.
>
> An Insight can be wrong while every Observation behind it is right.
>
> That is why it is recorded separately.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
