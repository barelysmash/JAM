# JARVIS System Vision

## Mission

Build an executive intelligence platform that augments human decision-making through specialized intelligence engines coordinated by a single executive orchestrator.

---

## Philosophy

Every component has exactly one responsibility.

Specialization creates expertise.

Coordination creates intelligence.

---

## Core Architecture

```
                    JARVIS
             Executive Orchestrator
                     │
      ┌──────────────┼──────────────┐
      │                             │
 Atlas Engine                 Friday Engine
Operational Intelligence     Trading Intelligence
      │                             │
RestaurantOS                 BarelyTrade
```

---

## Definitions

### JARVIS

Coordinates specialized intelligence engines.

Never owns domain logic.

---

### Atlas

Produces operational decisions.

Examples:

- Restaurant performance
- Labor optimization
- Inventory intelligence
- Forecasting

---

### Friday

Produces trading decisions.

Examples:

- Entries
- Exits
- Risk
- Position sizing
- Portfolio management

---

## Applications

Applications present decisions.

Examples:

- RestaurantOS
- BarelyTrade

Applications never generate intelligence.

---

## Design Principle

> Engines produce decisions.

> Applications present decisions.

> JARVIS coordinates decisions.