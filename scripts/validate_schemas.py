#!/usr/bin/env python3
"""
Validate Decision documents against the JAM Decision schema.

Runs two layers of checks.

  Structural   The JSON Schema at schemas/decision.schema.json.

  Semantic     The rules from architecture/decision-object.md that JSON Schema
               cannot express: the expires_at ordering rule, the approval and
               reversibility rule, and supersedes source and category matching.

Plus a small set of style lints drawn from the spec's summary guidance. Lints
are warnings by default and become failures under --strict.

Usage
    python scripts/validate_schemas.py
    python scripts/validate_schemas.py --strict
    python scripts/validate_schemas.py path/to/decision.json ...

Exit codes
    0   everything passed
    1   at least one document failed
    2   the validator could not run
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    sys.stderr.write(
        "error: the jsonschema package is required\n"
        "       install it with: python -m pip install jsonschema\n"
    )
    raise SystemExit(2)

DEFAULT_SCHEMA = "schemas/decision.schema.json"
DEFAULT_GLOB = "schemas/examples/*.json"

HEDGE_WORDS = [
    "consider",
    "considering",
    "could",
    "may",
    "maybe",
    "might",
    "perhaps",
    "possibly",
    "potentially",
    "probably",
    "should probably",
]

RESET = "\033[0m"
RED = "\033[31m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
DIM = "\033[2m"


class Report:
    """Collects findings for a single document."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def note(self, message: str) -> None:
        """Informational only. Never fails, even under --strict."""
        self.notes.append(message)

    @property
    def ok(self) -> bool:
        return not self.errors


def parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def check_expiry(doc: dict, report: Report) -> None:
    """expires_at must be later than created_at."""
    if "expires_at" not in doc:
        return

    created = parse_timestamp(doc.get("created_at", ""))
    expires = parse_timestamp(doc["expires_at"])
    if created is None or expires is None:
        return

    if expires <= created:
        report.error(
            f"expires_at ({doc['expires_at']}) is not later than "
            f"created_at ({doc['created_at']})"
        )


def check_approval(doc: dict, report: Report) -> None:
    """requires_approval may be false only if every recommendation is reversible."""
    if doc.get("requires_approval", True):
        return

    irreversible = [
        rec.get("recommendation_id", "<unidentified>")
        for rec in doc.get("recommendations", [])
        if not rec.get("reversible", False)
    ]
    if irreversible:
        report.error(
            "requires_approval is false but these recommendations are not "
            "reversible: " + ", ".join(irreversible)
        )


def check_supersedes(doc: dict, report: Report, index: dict[str, dict]) -> None:
    """A superseding Decision must share source and category with its predecessor."""
    target_id = doc.get("supersedes")
    if not target_id:
        return

    if target_id == doc.get("decision_id"):
        report.error("supersedes points at the Decision's own decision_id")
        return

    target = index.get(target_id)
    if target is None:
        report.note(
            f"supersedes {target_id}, which is not among the documents being "
            "validated; source and category match cannot be checked here"
        )
        return

    if target.get("source") != doc.get("source"):
        report.error(
            f"supersedes {target_id} but source differs "
            f"({doc.get('source')} vs {target.get('source')})"
        )
    if target.get("category") != doc.get("category"):
        report.error(
            f"supersedes {target_id} but category differs "
            f"({doc.get('category')} vs {target.get('category')})"
        )


def check_summary_style(doc: dict, report: Report) -> None:
    """The spec asks for imperative summaries with no hedging."""
    summary = doc.get("summary", "")
    found = [
        word
        for word in HEDGE_WORDS
        if re.search(rf"\b{re.escape(word)}\b", summary, re.IGNORECASE)
    ]
    if found:
        report.warn(
            "summary hedges (" + ", ".join(sorted(set(found))) + "); "
            "the spec asks for imperative phrasing"
        )


def check_rationale_present(doc: dict, report: Report) -> None:
    """rationale is strongly expected for critical and high priority."""
    if doc.get("priority") in {"critical", "high"} and not doc.get("rationale"):
        report.warn(
            f"priority is {doc['priority']} but rationale is absent; "
            "the spec expects one"
        )


def check_schema_version(doc: dict, report: Report, schema_id: str) -> None:
    """The document's major version must match the schema's."""
    match = re.search(r"/decision/(\d+)\.\d+\.\d+/", schema_id)
    if not match:
        return

    declared = doc.get("schema_version", "")
    doc_major = declared.split(".")[0] if declared else ""
    if doc_major and doc_major != match.group(1):
        report.error(
            f"schema_version {declared} has a different major version than "
            f"the schema ({match.group(1)}.x.x)"
        )


def validate(paths: list[str], schema_path: str, strict: bool, color: bool) -> int:
    def paint(text: str, code: str) -> str:
        return f"{code}{text}{RESET}" if color else text

    try:
        schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.stderr.write(f"error: schema not found at {schema_path}\n")
        return 2
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"error: schema is not valid JSON: {exc}\n")
        return 2

    try:
        Draft202012Validator.check_schema(schema)
    except Exception as exc:
        sys.stderr.write(f"error: schema is not a valid JSON Schema: {exc}\n")
        return 2

    print(f"{paint('schema', DIM)}  {schema_path} is valid draft 2020-12")

    if not paths:
        print(f"{paint('warning', YELLOW)}  no documents matched; nothing to check")
        return 0

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    schema_id = schema.get("$id", "")

    documents: dict[str, dict] = {}
    reports: list[Report] = []
    index: dict[str, dict] = {}

    for path in paths:
        report = Report(path)
        reports.append(report)
        try:
            doc = json.loads(Path(path).read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.error(f"not valid JSON: {exc}")
            continue
        if not isinstance(doc, dict):
            report.error("top level value is not an object")
            continue
        documents[path] = doc
        decision_id = doc.get("decision_id")
        if isinstance(decision_id, str):
            index[decision_id] = doc

    seen: dict[str, str] = {}
    for report in reports:
        doc = documents.get(report.path)
        if doc is None:
            continue

        for error in sorted(validator.iter_errors(doc), key=lambda e: list(e.path)):
            location = "/".join(str(p) for p in error.path) or "<root>"
            report.error(f"{location}: {error.message}")

        check_expiry(doc, report)
        check_approval(doc, report)
        check_supersedes(doc, report, index)
        check_schema_version(doc, report, schema_id)
        check_summary_style(doc, report)
        check_rationale_present(doc, report)

        decision_id = doc.get("decision_id")
        if isinstance(decision_id, str):
            if decision_id in seen:
                report.error(
                    f"decision_id {decision_id} is also used by {seen[decision_id]}"
                )
            else:
                seen[decision_id] = report.path

    failures = 0
    warnings = 0
    for report in reports:
        if report.errors:
            failures += 1
            print(f"{paint('FAIL', RED)}    {report.path}")
        elif report.warnings:
            print(f"{paint('ok', GREEN)}      {report.path}")
        else:
            print(f"{paint('ok', GREEN)}      {report.path}")

        for message in report.errors:
            print(f"          {paint('error', RED)} {message}")
        for message in report.warnings:
            warnings += 1
            print(f"          {paint('warn', YELLOW)}  {message}")
        for message in report.notes:
            print(f"          {paint('note', DIM)}  {message}")

    total = len(reports)
    print()
    print(f"{total} document(s), {failures} failed, {warnings} warning(s)")

    if failures:
        return 1
    if warnings and strict:
        print(paint("failing because --strict treats warnings as errors", RED))
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Decision documents against the JAM Decision schema."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help=f"documents to validate (default: {DEFAULT_GLOB})",
    )
    parser.add_argument(
        "--schema",
        default=DEFAULT_SCHEMA,
        help=f"path to the schema (default: {DEFAULT_SCHEMA})",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat warnings as failures",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="disable colored output",
    )
    args = parser.parse_args()

    paths = args.paths or sorted(glob.glob(DEFAULT_GLOB))
    color = sys.stdout.isatty() and not args.no_color

    return validate(paths, args.schema, args.strict, color)


if __name__ == "__main__":
    raise SystemExit(main())
