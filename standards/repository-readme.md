# Repository README

Version: 1.0

## Purpose

This standard defines what the README of every BarelySmash repository must
contain.

The README is the only document guaranteed to be read. It answers three
questions for someone who has just arrived: what this repository is, where it
sits in the platform, and how to run it.

It is not a manual. Anything that needs more than a screen belongs in a linked
document.

---

## Required Sections

In this order.

### 1. Title and role

The repository name, then one sentence naming what it is.

```
# Atlas

**Operational Intelligence Engine**
```

### 2. Platform context

Which layer of the platform this occupies, and a link to JAM.

Every repository is exactly one of: an intelligence engine, an application,
shared infrastructure, or the manual itself.
[`architecture/ecosystem.md`](../architecture/ecosystem.md) defines the
distinction; the README states which one applies and does not re-argue it.

### 3. Responsibilities

What this repository owns, as a short list.

Then what it deliberately does not own. The second list prevents more mistakes
than the first — an engine that never states it does not present intelligence
will eventually grow a user interface.

### 4. Contracts

What the repository consumes and what it emits.

Any repository producing or consuming Decision objects names the
`schema_version` range it supports and links to
[`architecture/decision-object.md`](../architecture/decision-object.md).

This section exists because contract drift is the failure mode most likely to
cross repository boundaries, and the README is where someone will look first.

### 5. Getting started

The shortest path from a fresh clone to something running.

Prerequisites with versions, then commands that can be copied verbatim.

If it cannot be run yet, say so plainly. Do not describe an intended future
setup as though it works.

### 6. Validation and tests

How to run the checks CI runs, locally.

```
python -m pip install jsonschema
python scripts/validate_schemas.py --strict
```

Someone who cannot reproduce a CI failure locally will start guessing at it in
pushes.

### 7. Repository structure

Top-level directories and one line each. Only directories that exist.

### 8. License

The license, named correctly, linking the license file.

### 9. Footer

```
**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
```

---

## Rules

### Document what exists

A README describes the repository as it is, not as it is intended to become.

Planned work may be listed, but only under an explicit heading that marks it as
planned. A reader must never have to test a claim to discover it was
aspirational.

This rule was written because JAM's own README violated it: it documented
`standards/`, `adr/`, `rfc/`, and `roadmap/` in its repository structure while
none of those directories existed.

### Links must be relative

```
[Decision Object](architecture/decision-object.md)
```

Not absolute GitHub URLs. Relative links survive forks, clones, and branch
renames, and they resolve in editors as well as on the web.

### Every claim must be checkable

If the README says a command works, it works today. If it names a license, that
is the license in the file. If it lists a directory, the directory is there.

A README that is wrong in a small verifiable way teaches readers to distrust the
parts they cannot verify.

### One screen to orientation

The first three sections fit on a screen. Anything longer belongs behind a link.

### No duplicated architecture

A README links to `architecture/`. It does not restate it.

Two copies of an explanation become two different explanations. Which is exactly
how JAM's README ended up with Philosophy, Vision, Architecture, Standards, and
Reference each appearing twice.

---

## Maintenance

The README is updated in the same commit as the change that dated it.

A structural change that adds a directory, alters a contract, or changes how the
repository is run is not complete until the README reflects it.

---

## Core Principle

> The README is a promise about the repository.
>
> Every sentence in it is checkable, and someone will check.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
