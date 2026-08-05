# {{PROJECT_NAME}}

> Built with JAM — the JARVIS Architecture Manual.

**Platform role:** {{PLATFORM_ROLE}}

{{PROJECT_NAME}} is an independently deployable BarelySmash system.

## Responsibilities

Document the domain responsibilities owned by this repository.

## Exclusions

Document the responsibilities this repository explicitly does not own.

## Architecture

This repository:

- owns its domain models and state;
- remains independently deployable and testable;
- communicates across repository boundaries through explicit, versioned contracts;
- does not depend on JARVIS internals;
- does not share another engine's database.

## Package

The primary Python package is `{{PACKAGE_NAME}}`.

## Development

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

Install development dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run validation:

```bash
python -m ruff check .
python -m mypy src
python -m pytest
```

## JAM Conformance

This repository follows the applicable architecture and engineering standards
defined by JAM.

Repository-specific exceptions must be documented explicitly and must not
silently redefine JAM standards.

---

**BarelySmash**

*Observe. Understand. Decide. Learn. Repeat.*
