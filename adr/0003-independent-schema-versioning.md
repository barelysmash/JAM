# ADR-0003: Independent Schema Versioning

Status: `Accepted`

Date: 2026-07-30

Supersedes: none

Superseded by: none

---

## Context

JAM shipped one contract, and one repository tag could represent it without
ambiguity. `scripts/release.sh` enforced that by refusing to tag unless the
version in the Decision schema's `$id` matched the tag.

Adding DecisionState broke the arrangement immediately.

The manual changed materially, so the next release is a minor bump to `v1.1.0`.
The Decision contract did not change at all. The gate therefore demands that
`decision.schema.json` declare `1.1.0`, which would tell every consumer pinned
to Decision `1.0.0` that their contract moved when it did not.

The gate was asking one number to describe two things that change on different
schedules. It cannot.

This will get worse rather than better. Observation, Event, and Action are all
plausible future contracts, each with its own rate of change.

---

## Decision

Schemas are versioned independently, each on its own contract.

The repository tag versions **the manual**, not any individual contract.

`schemas/manifest.json` maps a release to the schema versions it contains. The
manifest declares the release it belongs to, and the release gate verifies the
tag matches it.

---

## Rationale

**1. A version should change when the thing it names changes.**

Decision `1.0.0` was not altered by DecisionState arriving. Renumbering it would
make the version a statement about the repository rather than about the
contract, which is precisely what makes it useless for pinning.

**2. False alarms are expensive at this scale.**

A consumer pinned to a contract that gets renumbered for unrelated reasons has
to diff the schema to discover nothing changed for it. Across five repositories
and an indefinite number of releases, that happens often enough that people stop
checking — and then a real change gets waved through.

**3. Consumers pin per contract, not per repository.**

A repository that vendors only `decision.schema.json` cares about the Decision
version. Making it track a repository version means tracking changes to
documents it will never read.

**4. The manifest is needed regardless.**

The testing standard already asks vendoring repositories to record which release
their schema came from. A hand-written note does that badly. The manifest makes
"JAM v1.1.0" resolve mechanically to the contract versions it shipped.

---

## Alternatives Considered

**Lockstep versioning.**

Every schema carries the repository version. Adding DecisionState makes
everything `1.1.0`, Decision included.

This is a real option and its appeal is genuine: one number, no manifest, no
second file to keep in step, and a tag that unambiguously identifies every
contract in the release.

Rejected for reason 2. The churn is not free — it is paid by every consumer, on
every release, in attention. The chosen design trades that recurring cost for a
one-time structural cost, which is the better trade only because the manifest is
machine-checked. Without enforcement, lockstep would be the safer choice.

**Independent versions with no manifest.**

Schemas version themselves; the tag versions the manual; nothing connects them.

Rejected because a vendoring repository then cannot resolve what a release
contained. "Pinned to JAM v1.1.0" would be unanswerable without checking out the
tag and reading each schema, which is exactly the manual work the pin exists to
avoid.

**A repository per schema.**

Genuine independence, no manifest, no drift.

Rejected as disproportionate. The contracts and the reasoning that produced them
belong in one place, and five repositories to publish four JSON files would
create more coordination than it removes.

---

## Consequences

**Positive.**

Version numbers mean what they say. Consumers pin to the contract they depend
on. A release resolves mechanically to its contents, which is what the testing
standard needs.

**Negative.**

One more file that can drift from the thing it describes. This is the same
problem the category registry has, solved the same way — the validator fails if
the manifest and the schemas disagree — but it is a real cost and it is the
reason lockstep would otherwise win.

"What version is JAM" now has two correct answers: the release, and the version
of whichever contract is being discussed. Documentation has to be careful about
which one it means.

**Neutral.**

The manifest carries its own `manifest_version`, so its format can change
without disturbing what it describes.

---

## Open Questions

**Retiring a schema.** Nothing yet says what happens when a contract is
withdrawn. Removing its manifest entry would silently break pins; a
`deprecated` marker is the likely answer, following the category registry.

**Pre-1.0 contracts.** A new schema will start below `1.0.0` while it settles.
The manifest permits it, and nothing states what stability guarantee a `0.x`
contract carries.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
