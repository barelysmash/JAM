# Decision Categories

Version: 1.0

## Purpose

This document is the authoritative registry of `category` values for the
Decision object.

`architecture/decision-object.md` defines the field. This document defines what
may go in it.

A category names the *kind* of decision. It is not the subject matter — that is
`domain` — and it is not the urgency — that is `priority`.

---

## Naming

Categories are namespaced by the engine that emits them.

```
<engine>.<category>
```

The segment after the dot is lowercase snake_case.

Namespacing exists because the same word means different things in different
engines. `position` is precise in Friday and meaningless in RestaurantOS.
Without the namespace, a flat vocabulary would either collide or grow
awkward compound names.

JARVIS emits no categories. It synthesizes Decisions; it does not produce them.

---

## Enforcement

The schema at `schemas/decision.schema.json` validates the *shape* of a
category with a pattern. It does not validate membership in this registry.

This is deliberate. Tightening the schema to an enumeration would be a
constraint change, and by the versioning rules in `architecture/decision-object.md`
that requires a major version bump every time a category is added. Membership is
enforced one layer up instead, by `scripts/validate_schemas.py`, which reads
`glossary/decision-categories.json`.

The practical effect: adding a category is a minor change, and an unregistered
category still fails validation.

---

## Status

| Status | Meaning |
| --- | --- |
| `active` | In use. Engines may emit it. |
| `deprecated` | Still valid on historical Decisions. Engines must stop emitting it. |

Categories are never deleted. A Decision emitted last quarter must remain
readable next year, and removing a category would break that.

A deprecated category carries `superseded_by` when a replacement exists.

---

## Atlas

Operational Intelligence. Restaurants, venues, and the physical business.

| Category | Status | Definition |
| --- | --- | --- |
| `atlas.inventory` | `active` | Stock levels, order quantities, and par adjustments. |
| `atlas.pricing` | `active` | Changes to the price of an item already offered. |
| `atlas.menu` | `active` | Composition of what is offered: additions, removals, placement. |
| `atlas.labor` | `active` | Scheduling, staffing levels, and role coverage. |
| `atlas.vendor` | `active` | Supplier selection, terms, and substitution. |
| `atlas.maintenance` | `active` | Equipment service, repair, and replacement. |
| `atlas.marketing` | `active` | Promotions, campaigns, and sampling programs. |
| `atlas.compliance` | `active` | Regulatory obligations, licensing, and filings. |

`atlas.pricing` and `atlas.menu` are easy to confuse. Changing what a bottle
costs is `atlas.pricing`. Deciding whether to carry the bottle at all is
`atlas.menu`.

---

## Friday

Trading Intelligence. Markets, positions, and capital.

| Category | Status | Definition |
| --- | --- | --- |
| `friday.position` | `active` | Opening or adding to a position in a specific instrument. |
| `friday.exit` | `active` | Managing an existing position: stops, targets, and trims. |
| `friday.risk` | `active` | Portfolio-level risk posture and exposure limits. |
| `friday.allocation` | `active` | Distribution of capital across strategies or sectors. |
| `friday.hedge` | `active` | Protective overlays against identified exposure. |
| `friday.watchlist` | `active` | Candidates to monitor that are not yet actionable. |

`friday.position` and `friday.exit` split on direction of intent. Getting in is
`position`. Getting out, or deciding where getting out would happen, is `exit`.

`friday.watchlist` is the narrowest case that still qualifies as a Decision. It
recommends a real action — add this instrument to the monitored set — and
carries evidence for it. A Decision that recommends nothing is an Observation
and must not be emitted.

---

## Adding a Category

A new category is warranted when an engine has a decision type that no existing
category describes without distortion.

It is not warranted when an existing category fits but feels imprecise. That is
what `domain` and `tags` are for.

To add one:

1. Add the row to the table above.
2. Add the matching entry to `glossary/decision-categories.json`.
3. Set `since_version` to the next minor version of the Decision spec.
4. Bump the minor version of `architecture/decision-object.md`.

Both files must agree. `scripts/validate_schemas.py` fails if they drift.

Consumers must already tolerate unrecognized categories, so an engine may emit a
newly registered category before applications know how to render it.

---

## Deprecating a Category

1. Set its status to `deprecated` in both files.
2. Set `superseded_by` if a replacement exists.
3. Leave the row in place. Permanently.

Engines that continue emitting a deprecated category will produce validation
warnings, which become failures under `--strict`.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
