# JAM

**JARVIS Architecture Manual**

> Part of the **BarelySmash Intelligence Platform**.
>
> JAM is the architectural source of truth for JARVIS, Atlas, Friday,
> Foundation, RestaurantOS, BarelyTrade, and future systems.

JAM defines the philosophy, vision, architecture, standards, and terminology
that guide every repository in the BarelySmash ecosystem.

---

# Reading Guide

New contributors should read these documents in order.

## Foundations

The commitments everything else rests on.

- [Manifesto](MANIFESTO.md)
- [Core Values](CORE_VALUES.md)
- [Motto](MOTTO.md)

## Philosophy

The principles that define how intelligence systems reason.

- [Cognitive Loop](philosophy/0000-cognitive-loop.md)

## Vision

What we are building.

- [System Vision](vision/0000-system-vision.md)
- [Platform Charter](vision/0001-platform-charter.md)

## Architecture

How the platform is organized.

- [Ecosystem](architecture/ecosystem.md)
- [Reasoning Model](architecture/reasoning-model.md)
- [Insight Object](architecture/insight-object.md)
- [Decision Object](architecture/decision-object.md)
- [Decision State](architecture/decision-state.md)

## Standards

How we build.

- [Repository README](standards/repository-readme.md)
- [Git Workflow](standards/git-workflow.md)
- [Python Standards](standards/python.md)
- [Testing Standards](standards/testing.md)
- [Prompt Standards](standards/prompt.md)

## Reference

Supporting material.

- [Ontology](glossary/ontology.md)
- [Decision Categories](glossary/decision-categories.md)
- [Architecture Decision Records](adr/README.md)
- RFCs *(coming soon)*
- Roadmap *(coming soon)*

---

# Mission

Build intelligence systems that improve human decision-making through
specialized cognition coordinated by JARVIS.

---

# Ecosystem

```
                          Barry
                            │
                            ▼
                         JARVIS
                  Executive Orchestrator
                            │
            ┌───────────────┼───────────────┐
            │                               │
        Atlas                            Friday
 Operational Intelligence         Trading Intelligence
            │                               │
      RestaurantOS                     BarelyTrade

  ───────────────────────────────────────────────────
                       Foundation
        Shared technical capabilities. No business logic.
```

---

# Repository Structure

```
philosophy/     How intelligence systems reason.
vision/         What is being built, and why.
architecture/   System design, responsibilities, and contracts.
schemas/        Machine-readable contracts, with validating examples.
glossary/       Shared terminology and controlled vocabularies.
adr/            Architecture Decision Records.
standards/      Engineering standards and conventions.
scripts/        Tooling that enforces what the manual specifies.
```

Planned: `rfc/` for proposals ahead of implementation, and `roadmap/` for
milestones.

---

# Validation

The contracts in this repository are enforced, not merely described.

`scripts/validate_schemas.py` checks every Decision document against
`schemas/decision.schema.json`, applies the rules JSON Schema cannot express,
and verifies that the category registry agrees with its documentation. It runs
on every push and pull request.

To run it locally:

```
python -m pip install jsonschema
python scripts/validate_schemas.py --strict
```

---

# Core Principle

> Intelligence Systems produce decisions.
>
> Applications present decisions.
>
> JARVIS coordinates decisions.

---

# License

[PolyForm Noncommercial 1.0.0](LICENSE.md)

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
