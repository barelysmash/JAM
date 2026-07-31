# Git Workflow

Version: 1.0

## Purpose

This standard defines how changes move from a working tree to `main` in every
BarelySmash repository.

It is written to be followed by one person working alone and to still hold when
that stops being true.

---

## Branches

`main` is always releasable. Work never happens directly on it.

Every change starts on a branch cut from an up-to-date `main`.

```
git checkout main
git pull
git checkout -b feat/decision-object
```

### Naming

```
<type>/<short-kebab-description>
```

The type matches the commit type the branch will carry.

| Prefix | For |
| --- | --- |
| `feat/` | New capability |
| `fix/` | Corrected behavior |
| `docs/` | Documentation only |
| `refactor/` | Restructuring with no behavior change |
| `test/` | Tests only |
| `ci/` | Pipelines and automation |
| `chore/` | Tooling, dependencies, housekeeping |

### Always branch from main

Cutting a branch while another feature branch is checked out produces a stack:
the second branch carries the first one's commits, and its pull request shows
changes that have nothing to do with it.

Check before opening the pull request.

```
git log --oneline main..HEAD
```

If commits appear that belong to another branch, unstack it.

```
git rebase --onto main <wrong-base> <your-branch>
```

Stacking is occasionally deliberate, when a change genuinely depends on
unmerged work. In that case merge the branches in order, and say so in the
pull request.

### One concern per branch

A branch does one thing. Two unrelated fixes are two branches.

The test is whether the branch could be reverted in one action without taking
something unrelated with it.

---

## Commits

Commits follow [Conventional Commits](https://www.conventionalcommits.org).

```
<type>(<scope>): <subject>

<body>
```

### Subject

Imperative mood, lowercase, no trailing period, 72 characters or fewer.

It completes the sentence *"applying this commit will…"*.

```
feat(schemas): add Decision JSON Schema v1.0.0
docs(architecture): specify the Decision object
chore: ignore local scaffolding and tooling artifacts
```

Not:

```
Added the schema
updates
fixes stuff
```

### Scope

The area touched, usually a directory: `architecture`, `schemas`, `scripts`,
`glossary`, `adr`, `standards`. Omit it when a change is repository-wide.

### Body

The subject says what changed. The body says **why**, and what was considered
and rejected.

A body is expected on anything that would puzzle a reader six months later. It
is unnecessary on a typo fix.

Wrap at 72 characters.

### Granularity

One commit per concern, even within a branch. A branch that adds a
specification, its schema, and its examples is naturally three commits, and
each should stand on its own.

Stage explicit paths.

```
git add schemas/decision.schema.json schemas/examples/atlas-inventory.json
```

Never `git add -A`. It sweeps up scratch files, local scripts, and half-finished
work that was never meant to ship.

---

## Pull Requests

Every change reaches `main` through a pull request, including changes made
alone. The pull request is where CI runs and where the change becomes reviewable
later.

**Checks must pass.** A red pull request is not merged, and a failing check is
not worked around by disabling it.

**Merge commits, not squash.** The individual commits are the record. Squashing
collapses a specification, its schema, and its examples into one opaque change.

**Delete the branch on merge.** Enable automatic head branch deletion in
repository settings so this is not a manual step.

`scripts/ship.sh` in JAM performs the full sequence: push, open, wait for
checks, merge, clean up.

---

## History

Published history is never rewritten.

Never force-push `main`. Never force-push a branch someone else may have pulled.

Rebasing an unpushed local branch is fine and often the right way to keep a
history readable. Once a branch is on `origin`, prefer merging `main` into it
over rebasing it.

To undo a merged change, revert it. The mistake and its correction are both part
of the record.

---

## What Not to Commit

Every repository carries a `.gitignore` covering, at minimum, local scaffolding
scripts, language build artifacts, virtual environments, editor directories, and
operating system files.

Never commit credentials, API keys, or tokens. A secret that reaches a public
repository is compromised the moment it lands, and rewriting history does not
undo that — rotate it.

Generated files are committed only when downstream consumers need them without
running the generator.

---

## Line Endings

Every repository carries a `.gitattributes` normalizing text files to LF.

```
* text=auto eol=lf
```

Git stores LF and checks out the platform default, so Windows clones work
normally while committed bytes stay identical across machines.

Expect a one-time `CRLF will be replaced by LF` warning on files that predate
the rule. That is the normalization happening, not a problem.

---

## Core Principle

> The history is the record.
>
> Write it for the person who will read it without you there to explain.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
