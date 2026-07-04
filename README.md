# JAM
JARVIS Architecture Manual

> Part of the **BarelySmash Intelligence Platform**.
>
> JAM is the architectural source of truth for JARVIS, Atlas, Friday, RestaurantOS, BarelyTrade, and future systems.

**JARVIS Architecture Manual**

JAM is the architectural source of truth for the BarelySmash Intelligence Platform.

It defines the vision, principles, standards, terminology, and architectural decisions that guide every repository in the ecosystem.

---

# Mission

Create intelligent software that augments human decision-making through specialized intelligence engines coordinated by a single executive orchestrator.

---

# Ecosystem

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

# Repository Structure

```
vision/
```

Long-term vision and philosophy.

```
architecture/
```

System design and responsibilities.

```
standards/
```

Engineering standards and conventions.

```
adr/
```

Architecture Decision Records.

```
roadmap/
```

Long-term plans and milestones.

```
rfc/
```

Requests for Comments before implementation.

```
glossary/
```

Shared terminology used across every repository.

---

# Core Principle

> **Engines produce decisions.**
>
> **Applications present decisions.**
>
> **JARVIS coordinates decisions.**

---

# License

MIT