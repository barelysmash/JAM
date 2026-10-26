# Unattended Automation

Version: 1.0

## Purpose

This standard defines how work gets done across the platform's repositories
when no person is in the cycle: scheduled jobs, cross-repository propagation,
and runs where a model edits code until a stated condition holds.

It exists because an unattended process has two properties a person does not.
It cannot ask, so every question it cannot answer is a stall or a guess. And
it cannot be embarrassed, so every write it can make is a write nobody
reviewed. The rules below are the rails that let such a process be trusted
with the platform's repositories anyway.

JARVIS runs these loops (`docs/LOOPS.md` in jarvis-v2 is the implementation
of record; ADR-0002 and ADR-0003 there are the decisions). The standard
applies to any repository that runs one or receives work from one.

---

## Vocabulary

**Routine.** A scheduled, unattended job, declared once in a registry
(`config/routines.yaml` in jarvis-v2) and realised as a timer. A routine is
either a *shell* routine — a script, no model — or a *goal* routine.

**Goal.** A repository, a *condition*, and a budget. The run iterates — edit,
run the condition, read the failure, edit — until the condition passes or the
budget runs out.

**Condition.** A shell command run from the repository root. Exit 0 is green.
It is the only thing that decides whether a goal is met.

**Backlog.** An ordered list of goals with no schedule of their own
(`config/backlog.yaml`). A *drain* routine runs the next eligible one.

**Hand-off.** What an unattended run leaves for a person: a branch, one
squashed commit, the same change as a `.patch` file, and a transcript. The
run stops there.

**Probe.** A run of a routine's preparation and condition with no model and no
branch, to see what a real run would chase.

**Finding.** A result the run was built to report — a repository at 10/11
conformance, a goal that stalled. A finding is a report line and an event,
and the run exits 0. A *failure* — exit non-zero — means the run itself could
not do its job.

---

## Rules

### 1. Loops consume JAM; they never change it

`jam validate`, the schemas and the category registry are inputs to every
loop. No unattended process proposes, edits or vendors changes *into* JAM.
Changes to JAM are a person's work, through the ordinary workflow.

### 2. The evaluator is a command, never a model

A goal's condition is a shell command declared in the registry. A model may
propose edits; it may not judge whether they are done, and it may not edit the
condition or the files the condition lives in. A model asked "is this
finished?" can be talked into yes. An exit code cannot.

Where green has to mean more than one thing — the types are clean *and* the
tests that exercise the same code still pass — the condition is one command
that runs both and fails on the first.

### 3. Every run stops before anything a person would want to review

An unattended run never pushes, opens a pull request, merges, or commits to
`main`. It prepares the change and hands off (see **Hand-off**). Landing it is
a person's step, through the repository's own guards: `ship.sh` where one
exists, otherwise the push → pull request → checks → squash-merge sequence of
the [Git Workflow](git-workflow.md). CI is the gate either way.

Granting a loop write access to a repository — the `--push` step that exists
in the code and is off — is a decision, not a configuration change. It is
recorded where the loop's registry lives, with the reason.

### 4. Isolation

A routine runs as a subprocess with no shared session, no shared conversation
and no shared memory with the executive. A goal run starts a fresh model
conversation and keeps its own checkout, its own interpreter and its own
state directory, outside the release, so deploys and rollbacks never touch
it. Two runs never work on the same repository at once; the lock is per
repository, not per routine, and a held lock is a finding.

### 5. What a proposer may not touch

By construction, not by instruction: the tests, the CI and tool configuration,
the contracts (`jam.yaml`, `VERSION`, vendored schemas), the deploy tree, the
scripts tree, and the condition's own files. The registry entry lists the
paths a run *may* write; everything else is read-only. An exception is an
explicit `unprotect:` list in the committed registry, where a reviewer sees
it.

The easiest way to make a red condition green is to delete the test, loosen
the config or edit the condition. None of those are writable.

### 6. Budgets, and a diff cap

Every goal run has a budget — iterations, wall-clock minutes, model tokens —
checked before each iteration, and a cap on the size of the change it may hand
off. A run that exceeds the cap stops and reports `too_large`; the cap is
raised by a person, in the registry, after reading the transcript. A run that
produces the same condition output three times in a row stops as `stalled`.

### 7. Every run leaves a record

A transcript of every model and tool call, a result file with the outcome,
the condition's output, and an event in the executive's event log with the
outcome and the patch path. A non-green run still leaves its branch; the
transcript is read before deciding whether the partial work is worth keeping.

### 8. Findings are not failures

A loop's exit status reports whether the loop could do its job, nothing else.
A regression found, a repository behind a contract version, a goal that ran
out of budget — all exit 0, with the finding in the report and the event. Exit
non-zero is reserved for "could not clone", "could not install", "crashed".

### 9. One source of truth for "landed"

A loop does not parse merged pull requests or tick its own bookkeeping to
decide that its work has been accepted. The condition passing on a fresh
clone of the base branch is the only evidence that a goal has landed, and the
same rule tells a propagation loop a repository has caught up: its pin matches
the release.

### 10. A backlog item is a goal, not a sentence

A task board is prose for people. An item becomes drainable only when a
person has written its condition into the backlog — the one piece of thinking
that must be done once, by someone, in a reviewed commit. No loop invents a
condition from a task's wording; see rule 2.

---

## What a repository must provide

To run loops, or to receive their work, a repository provides:

- a condition that can be run from its root with its own tooling
  (`mypy --strict <package>`, `pytest -q <file>`, `jam validate`);
- a landing path: `ship.sh`, or the Git Workflow sequence, with CI as the gate;
- `jam.yaml` with `manual_version`, so propagation can tell whether it is
  behind, and vendored schemas that are byte-identical to JAM's at that
  version, so propagation can tell what it vendored;
- a task board (`TASKS.md`) with one line per item, so a drained goal can tick
  exactly one of them on hand-off.

---

## Enforcement

| Rule | Kind |
| --- | --- |
| 1, 3, 10 | Convention — the registries are committed YAML, reviewed in pull requests |
| 2, 4, 5, 6, 7 | Tooling — the goal runner enforces them by construction and its tests pin them |
| 8, 9 | CI — a registry entry that cannot load fails the build; a run's exit code is the routine's |

Prefer tooling to CI, and CI to convention. A rail that depends on the model
remembering it is not a rail.
