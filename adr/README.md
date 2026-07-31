# Architecture Decision Records

Version: 1.0

## Purpose

An ADR records a decision that was hard to make and would be expensive to
reverse.

It exists so that a future reader — usually a future version of the person who
made the call — can recover the reasoning without excavating commit messages
and old conversations.

An ADR is not documentation of how the system works. That belongs in
`architecture/`. An ADR documents *why the system works that way rather than
some other way*, and what was given up in the process.

---

## When to Write One

Write an ADR when a choice meets all three tests.

**It was contested.** A real alternative existed and had a defensible case.

**It is expensive to reverse.** Undoing it would mean changing multiple
repositories, migrating data, or breaking a contract.

**It is not self-evident from the code.** A reader who understands the system
could still reasonably ask "why not the other way?"

Most decisions fail at least one test. Choosing a library, naming a field,
picking a directory layout — these are not ADRs. Recording them dilutes the
set until nobody reads it.

---

## Status

| Status | Meaning |
| --- | --- |
| `Proposed` | Under consideration. Not yet binding. |
| `Accepted` | In force. The system reflects this. |
| `Rejected` | Considered and declined. Kept so the argument is not relitigated. |
| `Superseded` | Replaced by a later ADR. Names its replacement. |
| `Deprecated` | No longer relevant, but not replaced. The context disappeared. |

An ADR is never deleted and never edited to change its decision. Reversing an
ADR means writing a new one that supersedes it, and updating the old record's
status to point forward.

This mirrors the Decision object's own rule, which is fitting given the subject
of ADR-0001.

---

## Numbering

Four digits, zero padded, assigned in order: `0001`, `0002`, and so on.

Numbers are never reused, including for rejected records. A gap in the sequence
is a bug.

File names are `NNNN-kebab-case-title.md`.

---

## Writing One

Copy `0000-template.md`, take the next number, fill it in, add a row to the
index below.

Keep it short. An ADR that runs past two pages is usually two ADRs, or it is
carrying design documentation that belongs in `architecture/`.

State the alternatives honestly. An ADR that makes the chosen option sound
obvious has failed — if it were obvious there would be nothing to record.

---

## Index

| ADR | Title | Status | Date |
| --- | --- | --- | --- |
| [0001](0001-decision-immutability.md) | Decision Immutability | `Accepted` | 2026-07-30 |
| [0002](0002-decision-state-ownership.md) | DecisionState Ownership | `Accepted` | 2026-07-30 |

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
