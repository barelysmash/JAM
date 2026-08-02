# BarelySmash Ontology

Version: 1.0

## Purpose

This document defines the core concepts used throughout the BarelySmash Intelligence Platform.

Every engine and application should use these terms consistently.

---

## Event

Something happened.

Immutable.

Examples

- TABC report imported.
- Stock trade executed.
- Reservation created.

---

## Observation

A measured fact.

No interpretation.

Example

Wine sales increased 12%.

---

## Insight

> Specified in [`architecture/insight-object.md`](../architecture/insight-object.md).

An interpretation of one or more observations.

Example

Premium sampling likely increased wine attachment.

---

## Decision

> Specified in [`architecture/decision-object.md`](../architecture/decision-object.md).

A recommended course of action.

Example

Continue premium sampling.

---

## Action

Execution of a decision.

Example

Generate purchase order.

---

## Executive Brief

A synthesized collection of decisions prepared for a human decision maker.

Owned by JARVIS.