# ADR-0005: Observation as a contract

**Status:** Accepted
**Date:** 2026-08-04
**Supersedes:** none

## Context

Observation was the last concept in the ontology without a contract. Both
Insight and Decision reference `observation_id` values, and nothing validated
that those identifiers pointed at anything, or that the metric data copied
alongside them was accurate.

Two implementations already existed in Atlas and disagreed:

- `atlas_core.Observation`: `category`, `metric`, `value`, `summary`,
  `evidence: list[str]`. One metric. No timestamp.
- `atlas_memory.Observation`: `id` (UUID), `timestamp`, `summary`,
  `evidence: dict[str, Any]`. Many metrics, held in a field named `evidence`.

`evidence` meant opposite things in the two types: source references in one,
the measurement itself in the other. JAM's own use of the word, on Insight and
Decision, means observations cited. Any merge of the two Atlas types that
mapped `evidence` to `evidence` would have silently changed what the data
meant, and nothing would have failed.

## Decision

An Observation is a **measurement event**: one subject, one period, one source
query, carrying one or more metrics measured together.

1. **`metrics` is an array**, reusing the `metric` shape already defined in
   `insight.schema.json`. A query returns a row; metrics measured together stay
   together.
2. **`evidence` does not appear on an Observation.** Provenance is
   `source_ref`. The word `evidence` is reserved platform-wide for citing
   observations.
3. **`observed_at` is required**, with optional `period_start` and
   `period_end`. A weekly total is not true at an instant.
4. **No `confidence`.** A fact that needs hedging is an Insight.
5. **No `category`.** Categories classify recommended action.
6. **Citation precision lives in the Insight**, not the Observation. An
   Insight's `evidence` entry already carries an inline `metric` naming which
   one it used.
7. **The inline copy is cross-checked.** Where both documents are present, a
   citation whose metric disagrees with its Observation is an error.

## Alternatives considered

**One metric per Observation.** Would have made `evidence: [observation_id]`
precise with no inline copy. Rejected: it duplicates subject, period, and
provenance across every metric from a single query, and discards the fact that
they were measured together. Correlation between metrics is interpretation and
belongs in an Insight, but co-measurement is a fact and belongs here.

**Qualified references** — `evidence` entries as `{observation_id, metric}`
objects. Rejected as redundant: `insight.schema.json` already carries an inline
`metric` on each evidence item, so the precision exists. Adopting this would
have been a major version bump on both Decision and Insight for no gain.

**Composite key strings** — `obs_01J...#wine_attachment`. Rejected: invents a
syntax the whole platform must remember, to express something the evidence item
already expresses structurally.

## Consequences

The `metric` shape is now defined in two schemas. They must stay identical.
The validator compares them field by field, so drift fails rather than rots.

Atlas has work to do. `atlas_core.Observation` gains `obs_`-prefixed
identifiers, a timestamp, and a metrics array; `atlas_memory.Observation` is
deleted in favor of it. The ULID generator added in Atlas `#30` emits a bare
identifier with no prefix and does not currently conform.

The "one subject, one period, one query" rule is only partly machine-checkable.
The validator rejects metrics whose declared periods conflict and warns above
eight metrics, but a genuinely incoherent grouping under those limits will
pass and has to be caught in review.

## Open questions

- **Retention.** Insights and Decisions cite observations indefinitely. Nothing
  says how long an Observation must remain resolvable, and a citation that no
  longer resolves is worse than no citation.
- **Cross-engine citation.** Nothing currently prevents an Atlas Insight from
  citing a Friday Observation. The validator checks source agreement on
  `derived_from` for Insights, and the same rule probably belongs here.
- **`subject` is unconstrained.** Free text today. If it becomes the join key
  between observations of the same thing, it needs a registry, exactly as
  categories did.
