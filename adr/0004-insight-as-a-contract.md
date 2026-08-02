# ADR-0004: Insight as a Contract

Status: `Accepted`

Date: 2026-07-30

Supersedes: none

Superseded by: none

---

## Context

`glossary/ontology.md` names four concepts in the reasoning chain: Event,
Observation, Insight, Decision. `architecture/reasoning-model.md` places Insight
between Observation and Decision, as the interpretation that turns measured
facts into something worth acting on.

The Decision object does not represent it.

`evidence[]` holds Observations — factual statements with metrics. There is no
field anywhere in the contract for the interpretation that connected those
observations to the recommendation. The chain the platform describes is
Observation → Insight → Decision, and the chain the contract carries is
Observation → Decision.

This was not noticed while JAM was the only repository. It surfaced immediately
on contact with Atlas, whose reasoning pipeline builds
`Decision → Insight → Observation` exactly as the reasoning model describes.
Emitting a JAM Decision from an Atlas Decision would have silently discarded the
Insight layer.

The omission matters for the fourth step of the loop. When a recommendation
turns out badly, the useful question is usually not *was the data wrong* but
*was the interpretation wrong*. An unrecorded interpretation cannot be reviewed.

---

## Decision

Insight is a first-class contract with its own specification, schema, and
identifier space (`ins_`).

Insights are immutable and independently addressable, on the same terms as
Decisions.

The Decision object gains an optional `derived_from` array of `insight_id`
values. `evidence` is unchanged and continues to carry Observations.

---

## Rationale

**1. The ontology already claims Insight is a distinct concept.**

Either it is distinct, in which case it deserves a contract, or it is not, in
which case the ontology and the reasoning model should stop naming it. Carrying
a concept in the documentation that no contract represents is how documentation
becomes decorative.

**2. Interpretations are reusable; recommendations are not.**

One Insight commonly supports several Decisions. "Premium sampling is lifting
wine attachment" can justify an inventory decision, a labor decision, and a
marketing decision. Embedding the interpretation inside each Decision would
copy it three times, and the three copies would drift.

**3. It is the layer where reasoning quality actually lives.**

Observations are measurements and are right or wrong on their own terms.
Recommendations follow from interpretations. When a Decision disappoints, the
interpretation is the thing to examine, and examining it requires that it exist
as a record.

**4. Atlas already built it this way.**

The pipeline in `atlas-core` produces observations, then insights, then
decisions, as separate stages with separate types. The contract was the thing
out of step, not the implementation.

---

## Alternatives Considered

**`rationale` absorbs the interpretation.**

The Decision object already has a free-text `rationale` field, which in practice
is where an interpretation would be written.

Rejected because free text is not addressable. Two Decisions resting on the same
interpretation have no way to say so, nothing can count how often an
interpretation preceded a poor outcome, and the confidence attached to the
interpretation is lost — `rationale` has no number in it. It is the cheapest
option and it forecloses the learning the platform exists to do.

**`evidence` accepts either observation or insight references.**

A single polymorphic array, with each item declaring which kind it points at.
Fewer fields, and it reflects that both are things a Decision rests on.

Rejected because it makes every consumer branch on item type to do anything
useful, and it blurs a distinction worth keeping sharp: evidence is what was
measured, insight is what someone concluded. A brief that renders those
identically is misleading.

**Leave it as it is.**

Defensible while the platform has one engine and one consumer, since nothing
breaks. Rejected because the cost of adding a contract rises steeply once
repositories are pinning to schema versions, and this one is already known to be
missing.

---

## Consequences

**Positive.**

The contract now matches the ontology and the reasoning model. Interpretations
are addressable, reusable across Decisions, and reviewable when a recommendation
disappoints. Atlas can emit its pipeline without discarding a layer.

**Negative.**

A third contract to version, document, and keep in step. Consumers that only
want a Decision now resolve one more reference to see the full reasoning chain,
and `derived_from` is optional, so they must handle its absence.

Confidence now appears on both Insight and Decision, and the relationship
between the two numbers is not defined. See the open questions.

**Neutral.**

`derived_from` is optional, so existing Decisions remain valid and this is a
minor version change to the Decision schema rather than a major one. An engine
that does not model insights separately can continue emitting Decisions without
it.

---

## Open Questions

**How Decision confidence relates to Insight confidence.** A rule that a
Decision may not exceed the confidence of its supporting Insights was considered
and not adopted: several independent moderate insights can reasonably support a
more confident decision than any one of them alone. Something weaker is probably
true and is not yet stated.

**Whether Observation becomes a contract too.** Both Insight and Decision
reference `observation_id` values that nothing validates, because Observation
has no schema. It is the last concept in the ontology without one, and Atlas's
`Observation` type currently has no identifier at all.

**Insight supersession across Decisions.** When an Insight is superseded, the
Decisions that cite it are not automatically stale, but nothing says how a
consumer should treat them.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
