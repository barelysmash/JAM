# Standards

Version: 1.0

## Purpose

Standards define how work is done across every BarelySmash repository.

Philosophy explains how the platform reasons. Architecture explains how it is
organized. Standards explain how it is built, and they apply to JARVIS, Atlas,
Friday, Foundation, RestaurantOS, BarelyTrade, and everything that follows.

A standard is binding. Where a repository cannot follow one, the exception is
recorded in that repository, with a reason.

---

## Index

| Standard | Covers | Enforcement |
| --- | --- | --- |
| [JAM Conformance](jam-conformance.md) | Repository alignment with JAM | Convention and CI |
| [Repository README](repository-readme.md) | What every repository must document about itself | Convention |
| [Git Workflow](git-workflow.md) | Branches, commits, pull requests, merges | Convention |
| [Python Standards](python.md) | Language version, tooling, typing, project layout | Tooling |
| [Testing Standards](testing.md) | What must be tested, and to what depth | CI |
| [Prompt Standards](prompt.md) | How prompts are written, versioned, and validated | CI |

---

## Enforcement

Standards fall into three kinds, and the kind matters more than the wording.

**Tooling.** A configured tool rejects the violation before it is committed.
Formatting and import order belong here.

**CI.** A check fails on push or pull request. Schema validation and test
requirements belong here.

**Convention.** Nothing catches a violation automatically. Commit message
style and README structure belong here.

Prefer tooling to CI, and CI to convention. A rule that depends on someone
remembering it will be followed inconsistently and eventually not at all.

Where a convention could be mechanized cheaply, mechanizing it is an
improvement worth making rather than a nice-to-have.

---

## Changing a Standard

Standards are versioned documents, not decisions. Editing one is ordinary work:
change it, explain the change in the commit body, and the new version applies.

A change that would be **contested** or is **expensive to reverse** across
repositories needs an [ADR](../adr/README.md) first. The standard then records
the outcome and links to it.

The test is the same one the ADR practice uses. If a reasonable person could
argue the other way and the choice would be costly to undo, write the record.

---

## Scope

A standard describes what to do, and where it is not obvious, why.

It does not describe how the platform is designed. When a standard finds itself
explaining the Decision object or the responsibilities of an engine, that
material belongs in `architecture/` and the standard should link to it.

Duplicated explanation drifts. Links do not.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
