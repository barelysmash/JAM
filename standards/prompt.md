# Prompt Standards

Version: 1.0

## Purpose

This standard defines how prompts are written, stored, versioned, and validated
across the BarelySmash platform.

A prompt that produces a Decision is part of the reasoning layer. It carries the
same weight as the code around it, and it fails in ways code does not: silently,
plausibly, and differently each time.

---

## Prompts Are Artifacts

**A prompt lives in a file, never inline in a string literal.**

Inline prompts cannot be diffed usefully, cannot be reviewed without reading the
surrounding code, and cannot be versioned independently of the module that
happens to contain them.

```
prompts/<name>/v<N>.md          The prompt.
prompts/<name>/README.md        What it is for, and how it is evaluated.
prompts/<name>/eval/            Cases, with expected properties.
```

Every prompt file opens with front matter:

```yaml
---
id: atlas.inventory.weekly_review
version: 3
model: claude-sonnet-4-5
temperature: 0.0
produces: decision
schema_version: "1.0.0"
---
```

`produces: decision` binds the prompt to the Decision contract. Everything in
the next section follows from it.

---

## Prompts That Produce Decisions

**Output is validated before it is emitted.** Every time, in production, not
only in tests.

Model output is parsed and validated against `schemas/decision.schema.json`
using the same validator CI runs. This is not optional and it is not sampled.

**Invalid output is discarded whole.** It is never partially used, never
repaired by hand-written fallbacks, and never emitted with the failing fields
stripped. It is logged against the prompt id and version, and the engine either
retries or produces nothing.

An engine that emits nothing is behaving correctly. An engine that emits a
malformed Decision has broken the contract every consumer depends on.

**Evidence must be real.** The model receives the Observations and may only
reference `observation_id` values it was given. It is instructed explicitly not
to invent identifiers, and the emitting code verifies every referenced id exists
before the Decision leaves the engine.

A fabricated observation id is the most dangerous output this platform can
produce: a Decision that looks fully traceable and traces to nothing.

**Confidence is derived, not invented.** A language model asked for a
probability produces a number shaped like one. Confidence is computed by the
engine from signal agreement, sample size, and data recency, or it is a
calibrated mapping from a small ordinal scale the prompt is allowed to choose
from. It is never a free-form float from the model.

The
[Decision object specification](../architecture/decision-object.md) defines what
confidence means and sets the 0.30 emission floor. A prompt that cannot support
a defensible confidence should produce an Observation instead.

**Categories come from the registry.** The prompt is given the valid categories
from [`glossary/decision-categories.md`](../glossary/decision-categories.md) and
constrained to them. It does not invent category names.

---

## Writing Them

**State the role, then the task, then the constraints, then the output format.**
In that order. Constraints stated after the output format are followed less
reliably.

**Be specific about what not to do.** "Do not hedge" outperforms "be
confident". Negative constraints are followed more reliably than positive
aspirations.

**Give examples of both.** One good output and one bad one, with the reason it
is bad. A single positive example is often read as a template to imitate rather
than a standard to meet.

**Specify the output format exactly.** For structured output, give the schema
and require nothing but the object — no preamble, no explanation, no code
fences.

**Do not ask for reasoning and structured output in one response** unless the
reasoning is a field. Mixed output invites the model to explain rather than
comply.

**Keep the prompt in one voice.** Prompts accrete over time as failures are
patched. A prompt that reads as five people arguing produces output that behaves
like it.

---

## Versioning

**Prompt version is part of `source_version`.** A Decision must be reproducible,
and it cannot be if the prompt that produced it changed without a trace.

Prompt versions are integers, incremented for any change to content, model, or
temperature. Whitespace does not count.

**Old versions are kept.** A superseded prompt file stays in the repository. It
is what a Decision emitted last quarter was actually produced by.

**Model changes are prompt changes.** Moving to a different model, or a
different version of the same model, increments the prompt version and requires
the evaluation set to be re-run. A prompt tuned against one model is not
validated against another.

---

## Evaluation

**Every prompt that produces Decisions has an evaluation set.** A prompt without
one cannot be changed safely, because there is no way to tell an improvement
from a regression.

Cases live in `prompts/<name>/eval/`. Each pairs an input with the properties
its output must satisfy. Assert on properties, not exact text — a prompt that
must produce one exact string is a template, not a prompt.

Properties worth asserting:

- The output validates against the Decision schema.
- Evidence references only supplied observation ids.
- Category is in the registry and belongs to the emitting engine.
- Summary is imperative and within 140 characters.
- Confidence is at or above the emission floor.
- A case with insufficient evidence produces no Decision.

That last one is the case most often missing. A prompt is easy to tune into
producing something for every input, and a Decision manufactured from thin
evidence is worse than silence.

**Run evaluations in CI** when a prompt file changes. Set `temperature: 0.0` for
evaluation regardless of the production setting, so runs are comparable.

---

## Safety

**No secrets in prompts.** No API keys, credentials, or connection strings.
Prompt files are committed.

**No personally identifying information.** Customer names, payment details, and
contact information are stripped or tokenized before they reach a model. Atlas
reasons about aggregates and SKUs, not about named individuals.

**Untrusted content is data, not instruction.** Vendor emails, review text, and
scraped market commentary are wrapped and explicitly labeled as content to be
analyzed rather than followed. A prompt that interpolates untrusted text into
its instruction section can be steered by whoever wrote that text.

---

## Core Principle

> A prompt is source code with a nondeterministic compiler.
>
> Version it, evaluate it, and never trust its output unvalidated.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
