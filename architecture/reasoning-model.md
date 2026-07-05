# Reasoning Model

Version: 1.0

---

# Purpose

Every intelligence engine in the BarelySmash platform follows the same reasoning pipeline.

The domain changes.

The reasoning process does not.

---

# Reasoning Pipeline

```text
Raw Data
    │
    ▼
Events
    │
    ▼
Observations
    │
    ▼
Insights
    │
    ▼
Decisions
    │
    ▼
Actions
    │
    ▼
Executive Brief
```

---

# Event

An event is something that happened.

Examples

- TABC report imported.
- Stock price updated.
- Reservation created.
- Labor schedule changed.

Events are immutable.

---

# Observation

An observation is a measurable fact.

Examples

- Wine sales increased 12%.
- Lunch covers decreased 8%.
- NVDA closed above resistance.
- Labor cost reached 32%.

Observations contain no interpretation.

---

# Insight

An insight explains what the observations likely mean.

Examples

- Premium sampling likely increased wine attachment.
- Lunch traffic softened despite stable reservations.
- The breakout occurred on above-average volume.

Insights are hypotheses supported by evidence.

---

# Decision

A decision recommends a course of action.

Examples

- Continue premium sampling.
- Increase Casa Madero inventory.
- Buy NVDA.
- Reduce lunch staffing Tuesday.

Every Decision should include:

- source
- category
- priority
- confidence
- summary
- evidence
- recommendations
- timestamp

---

# Action

An action executes a decision.

Examples

RestaurantOS

- Create purchase order.
- Notify manager.

BarelyTrade

- Submit limit order.
- Adjust stop loss.

Actions are optional.

Not every decision should automatically execute.

---

# Executive Brief

An Executive Brief combines multiple Decisions into one coherent briefing.

JARVIS owns Executive Brief generation.

JARVIS never creates Decisions.

It synthesizes them.

---

# Core Principles

Events are immutable.

Observations are factual.

Insights explain.

Decisions recommend.

Actions execute.

Executive Briefs synthesize.

---

# Responsibilities

Atlas

Events

Observations

Insights

Decisions

Friday

Events

Observations

Insights

Decisions

Applications

Actions

JARVIS

Executive Brief