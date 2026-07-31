# Python Standards

Version: 1.0

## Purpose

This standard defines how Python is written across the BarelySmash platform.

Its goal is that code from any repository reads as though one person wrote it,
and that disagreements about style are settled by a tool rather than a
conversation.

---

## Version

Python 3.12 is the minimum. CI runs the minimum, because code that only works
on a newer interpreter will otherwise pass locally and fail in deployment.

Newer versions are fine for local development.

---

## Tooling

Two tools. Both are pinned to exact versions.

| Tool | Replaces | Enforced by |
| --- | --- | --- |
| Ruff | Flake8, isort, pyupgrade, Black | CI and pre-commit |
| mypy | — | CI |

Ruff handles both linting and formatting. Its formatter is Black-compatible in
output, so nothing is lost by dropping Black, and one tool with one
configuration is materially easier to keep consistent across six repositories
than four tools with four.

Pin the exact Ruff version. Its rule set moves quickly, and an unpinned upgrade
will fail CI on code that passed the day before. Bump it deliberately, in its
own commit.

---

## Configuration

Every repository carries this in `pyproject.toml`. It is not adjusted per
repository except where noted.

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM", "RUF"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true
```

The selected rule sets are pycodestyle, Pyflakes, isort, naming, pyupgrade,
bugbear, simplify, and Ruff's own. Anything beyond these is a per-repository
addition, never a subtraction.

Run both locally before pushing:

```
ruff check .
ruff format --check .
mypy .
```

---

## Typing

**Strict mode, everywhere.** Every function has annotated parameters and a
return type, including `-> None`.

Strict mypy fails on untyped third-party imports, and the market data and
point-of-sale libraries this platform depends on are frequently untyped. The
escape hatch is per-module and explicit:

```toml
[[tool.mypy.overrides]]
module = ["some_untyped_sdk.*", "another_one.*"]
ignore_missing_imports = true
```

**Never set `ignore_missing_imports` globally.** A blanket setting silently
disables checking for every future dependency, including ones that ship perfectly
good types. Listing modules individually keeps the cost visible and the list
short.

Where a type is genuinely dynamic — parsed JSON, for instance — name it rather
than repeating `dict[str, Any]`:

```python
JsonDict = dict[str, Any]
```

`Any` is permitted where it is accurate. It is not permitted as a way of
avoiding thought, and a bare `type: ignore` requires a comment naming the reason.

---

## Project Layout

```
pyproject.toml          Metadata, dependencies, tool configuration.
src/<package>/          Importable code.
tests/                  Tests, mirroring the src/ structure.
scripts/                Operational and tooling entry points.
```

The `src/` layout is deliberate: it makes the installed package the thing under
test, rather than whatever happens to be in the working directory.

**Repositories that are not packages** — a manual with a few tooling scripts,
for instance — may omit `src/` and packaging metadata. They still carry
`pyproject.toml` for tool configuration, and their scripts still pass Ruff and
mypy. JAM itself is the example.

---

## Conventions

**Imports are absolute.** Relative imports beyond a single leading dot make
moving a module a search-and-replace exercise.

**Names follow PEP 8**, enforced by Ruff's `N` rules. Modules and functions in
`snake_case`, classes in `PascalCase`, constants in `SCREAMING_SNAKE_CASE`.

**Docstrings** are required on public functions, classes, and modules whose
purpose is not obvious from the signature. A docstring that restates the
function name is worse than none, because it has to be maintained.

**No bare `except`.** Catch the exception you can handle. Each package defines
one base exception and derives from it, so callers can catch the package
without catching everything.

**No `print` in library code.** Use `logging`. `print` in a script that exists
to talk to a terminal is fine.

---

## Time

Every datetime is timezone-aware and UTC.

```python
from datetime import UTC, datetime

now = datetime.now(UTC)
```

`datetime.now()` without a timezone is never correct in this platform. The
Decision object mandates RFC 3339 with a `Z` suffix, and
`expires_at > created_at` is enforced by CI — a naive local timestamp will
eventually cross a boundary and produce a Decision that expires before it was
issued.

Serialize with `.isoformat().replace("+00:00", "Z")`.

---

## Identifiers

Generated identifiers are prefixed ULIDs, matching
[`architecture/decision-object.md`](../architecture/decision-object.md).

```
dec_01J8Z4K7M2QF9X3B7T5V0N6RCD
obs_01J8Z4K7M2QF9X3B7T5V0N6RCE
rec_01J8Z4K7M2QF9X3B7T5V0N6RCG
```

ULIDs sort lexically by creation time, which makes logs and object listings
readable without a secondary index. The prefix makes an identifier
self-describing wherever it appears.

---

## Dependencies

Runtime dependencies are declared in `pyproject.toml` with lower bounds.
Development and tooling dependencies are pinned exactly.

A lock file is committed. `uv` is the recommended resolver for its speed and
lock format; `pip-tools` is an acceptable alternative. Whichever is chosen, the
repository README says which.

Adding a dependency is a decision with a cost. Prefer the standard library where
it is adequate.

---

## Core Principle

> Style is settled by tools so that review can be spent on substance.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
