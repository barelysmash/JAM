# The Observation Object

**Contract version 1.0.0.** Schema: `schemas/observation.schema.json`.
Examples: `schemas/examples/observation/`.

An Observation records what was measured. It is the ground layer of the
reasoning model: Observations are interpreted into Insights, Insights are
reasoned into Decisions, and Decisions are acted on.

## What an Observation is

**One measurement event.** One subject, one period, one source query, taken
by one engine at one moment. The metrics inside it were measured *together*,
which is the reason they are grouped rather than split.

An Observation is a fact. It carries no `confidence`, because a fact that
needs hedging is an interpretation and belongs in an Insight. It carries no
`category`, because categories classify recommended action and an Observation
recommends nothing.

## What an Observation is not

It is not causal. `summary` states what was measured, not why it happened.
"Wine attachment rose four points" is an Observation. "Wine attachment rose
because sampling worked" is an Insight wearing an Observation's clothes, and
the validator warns on the causal language that gives it away.

## Fields

| Field | Required | Notes |
|---|---|---|
| `schema_version` | yes | Semver of this specification. |
| `observation_id` | yes | `obs_` followed by a 26-character ULID. |
| `source` | yes | `atlas` or `friday`. JARVIS is never a source. |
| `source_version` | yes | Engine build, for reproducibility. |
| `domain` | yes | The subdomain measured. |
| `subject` | no | What was measured, where `domain` is not specific enough. |
| `summary` | yes | Factual, declarative, never causal. |
| `metrics` | yes | One to thirty-two, measured together. |
| `source_ref` | no | Provenance: the query, report, or system. |
| `observed_at` | yes | When taken. Never earlier than `period_end`. |
| `period_start` / `period_end` | no | Both or neither. |
| `supersedes` | no | Corrects an earlier Observation. Same source and domain. |
| `tags` | no | |

`evidence` deliberately does not appear. On an Insight or a Decision,
`evidence` means *observations cited*. An Observation cites nothing; its
provenance is `source_ref`. Reusing the word for a metrics payload, as the
Atlas memory layer currently does, means the same field name carries two
opposite meanings across the platform.

## Grouping metrics

`metrics` is an array because a query returns a row. Metrics that share a
subject, a period, and a source query belong to one measurement event, and
splitting them discards the fact that they were measured together.

The constraint that keeps this from becoming a bucket: **one subject, one
period, one query.** A nightly job that dumps thirty unrelated metrics into a
single Observation has violated the spec even though the schema permits it,
because no single factual `summary` can describe thirty unrelated numbers. The
validator warns above eight metrics and requires a period when there is more
than one.

## Citing a specific metric

An Insight's `evidence` entry carries `observation_id` **and** an inline
`metric`. That inline copy is what makes a citation precise: it names which
metric of a multi-metric Observation was used.

The copy is a snapshot, and snapshots drift. Where both documents are
available, the validator requires the inline metric to match the Observation
it names — same `name`, and the same `value`, `unit`, `delta`, and `period`
wherever the citation states them. A citation that disagrees with its source
is an error, not a warning.

## Correcting an Observation

Observations are immutable, as Decisions are (`adr/0001`). A measurement
taken against bad data is corrected by emitting a new Observation with
`supersedes` pointing at the old one, sharing `source` and `domain`.

Consumers that cited the superseded Observation are not rewritten. What they
concluded from the data they had remains what they concluded.
