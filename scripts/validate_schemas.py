#!/usr/bin/env python3
"""
Validate JAM contract documents against their schemas.

Two document kinds are checked, each against its own schema:

  decision        schemas/examples/decision/*.json
  decision-state  schemas/examples/decision-state/*.json

Three layers of checking apply.

  Structural   The JSON Schema for the kind.

  Semantic     The rules the specifications state that JSON Schema cannot
               express. For Decisions: expires_at ordering, approval versus
               reversibility, supersedes matching. For DecisionState:
               transition legality and per-stream ordering.

  Registry     Decision categories must appear in
               glossary/decision-categories.json, belong to the emitting
               engine, and agree with glossary/decision-categories.md.

Style lints are warnings by default and failures under --strict. Notes are
informational and never fail.

Usage
    python scripts/validate_schemas.py
    python scripts/validate_schemas.py --strict
    python scripts/validate_schemas.py --kind decision-state path/to/record.json

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
from typing import Any

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    sys.stderr.write(
        "error: the jsonschema package is required\n"
        "       install it with: python -m pip install jsonschema\n"
    )
    raise SystemExit(2) from None

# A parsed JSON object. The schema constrains the shape; the type does not.
JsonDict = dict[str, Any]

DECISION_SCHEMA = "schemas/decision.schema.json"
DECISION_GLOB = "schemas/examples/decision/*.json"
STATE_SCHEMA = "schemas/decision-state.schema.json"
STATE_GLOB = "schemas/examples/decision-state/*.json"

DEFAULT_MANIFEST = "schemas/manifest.json"
DEFAULT_REGISTRY = "glossary/decision-categories.json"
DEFAULT_REGISTRY_DOC = "glossary/decision-categories.md"

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
]

# architecture/decision-state.md defines these. An empty set means terminal.
TRANSITIONS: dict[str, set[str]] = {
    "surfaced": {"accepted", "rejected", "expired"},
    "accepted": {"executed", "failed", "expired"},
    "failed": {"accepted", "rejected"},
    "rejected": set(),
    "executed": set(),
    "expired": set(),
}

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


def normalize(path: str) -> str:
    """Compare paths separator-insensitively. Windows glob yields backslashes."""
    return path.replace("\\", "/")


def parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


# ----------------------------------------------------------------- registry


def load_registry(path: str) -> dict[str, JsonDict] | None:
    """Load the category registry. Returns None if it is absent."""
    registry_file = Path(path)
    if not registry_file.exists():
        return None

    data = json.loads(registry_file.read_text(encoding="utf-8"))
    return {entry["category"]: entry for entry in data.get("categories", [])}


def parse_registry_doc(path: str) -> dict[str, str]:
    """Pull category and status out of the markdown registry tables."""
    doc_file = Path(path)
    if not doc_file.exists():
        return {}

    found: dict[str, str] = {}
    row = re.compile(r"^\|\s*`([a-z]+\.[a-z0-9_]+)`\s*\|\s*`(\w+)`\s*\|")
    for line in doc_file.read_text(encoding="utf-8").splitlines():
        match = row.match(line.strip())
        if match:
            found[match.group(1)] = match.group(2)
    return found


def check_registry_sync(json_path: str, doc_path: str) -> list[str]:
    """The markdown registry and the JSON registry must agree."""
    registry = load_registry(json_path)
    if registry is None:
        return []

    documented = parse_registry_doc(doc_path)
    if not documented:
        return [
            f"{doc_path} contains no parseable category rows; "
            "the registry and its documentation cannot be compared"
        ]

    problems = []
    for category in sorted(set(registry) - set(documented)):
        problems.append(
            f"{category} is in {json_path} but not documented in {doc_path}"
        )
    for category in sorted(set(documented) - set(registry)):
        problems.append(
            f"{category} is documented in {doc_path} but not in {json_path}"
        )
    for category in sorted(set(registry) & set(documented)):
        declared = registry[category].get("status")
        if declared != documented[category]:
            problems.append(
                f"{category} status disagrees: {json_path} says {declared}, "
                f"{doc_path} says {documented[category]}"
            )
    return problems


# ----------------------------------------------------------------- manifest


def schema_declared_version(path: str, name: str) -> str | None:
    """Read the version a schema declares in its $id."""
    try:
        schema = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    match = re.search(rf"/{re.escape(name)}/(\d+\.\d+\.\d+)/", schema.get("$id", ""))
    return match.group(1) if match else None


def check_manifest(path: str) -> list[str]:
    """The manifest and the schemas it describes must agree."""
    manifest_file = Path(path)
    if not manifest_file.exists():
        return []

    try:
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"{path} is not valid JSON: {exc}"]

    problems: list[str] = []
    listed: set[str] = set()

    for entry in manifest.get("schemas", []):
        name = entry.get("name", "<unnamed>")
        declared = entry.get("version")
        schema_path = entry.get("path")

        if not schema_path:
            problems.append(f"{name} has no path in {path}")
            continue

        listed.add(normalize(schema_path))

        if not Path(schema_path).exists():
            problems.append(f"{name} points at {schema_path}, which does not exist")
            continue

        actual = schema_declared_version(schema_path, name)
        if actual is None:
            problems.append(
                f"{schema_path} does not declare a {name} version in its $id"
            )
        elif actual != declared:
            problems.append(
                f"{name}: {path} says {declared} but {schema_path} declares {actual}"
            )

    for found in sorted(glob.glob("schemas/*.schema.json")):
        if normalize(found) not in listed:
            problems.append(f"{normalize(found)} is not listed in {path}")

    return problems


# ----------------------------------------------------------- decision checks


def check_expiry(doc: JsonDict, report: Report) -> None:
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


def check_approval(doc: JsonDict, report: Report) -> None:
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


def check_supersedes(doc: JsonDict, report: Report, index: dict[str, JsonDict]) -> None:
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


def check_summary_style(doc: JsonDict, report: Report) -> None:
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


def check_rationale_present(doc: JsonDict, report: Report) -> None:
    """rationale is strongly expected for critical and high priority."""
    if doc.get("priority") in {"critical", "high"} and not doc.get("rationale"):
        report.warn(
            f"priority is {doc['priority']} but rationale is absent; "
            "the spec expects one"
        )


def check_schema_version(doc: JsonDict, report: Report, schema_id: str) -> None:
    """The document's major version must match the schema's."""
    match = re.search(r"/(?:decision|decision-state)/(\d+)\.\d+\.\d+/", schema_id)
    if not match:
        return

    declared = doc.get("schema_version", "")
    doc_major = declared.split(".")[0] if declared else ""
    if doc_major and doc_major != match.group(1):
        report.error(
            f"schema_version {declared} has a different major version than "
            f"the schema ({match.group(1)}.x.x)"
        )


def check_category(
    doc: JsonDict, report: Report, registry: dict[str, JsonDict] | None
) -> None:
    """category must be registered, active, and owned by the emitting engine."""
    if registry is None:
        return

    category = doc.get("category")
    if not isinstance(category, str):
        return

    entry = registry.get(category)
    if entry is None:
        report.error(
            f"category {category} is not in the registry; "
            "add it to glossary/decision-categories.json and its documentation"
        )
        return

    if entry.get("status") == "deprecated":
        replacement = entry.get("superseded_by")
        tail = f"; use {replacement} instead" if replacement else ""
        report.warn(f"category {category} is deprecated{tail}")

    engine = entry.get("engine")
    source = doc.get("source")
    if engine and source and engine != source:
        report.error(f"category {category} belongs to {engine} but source is {source}")


# ------------------------------------------------------ decision-state checks


def check_state_timestamps(doc: JsonDict, report: Report) -> None:
    """A transition cannot be recorded before it happened."""
    status_at = parse_timestamp(doc.get("status_at", ""))
    created = parse_timestamp(doc.get("created_at", ""))
    if status_at is None or created is None:
        return

    if status_at > created:
        report.error(
            f"status_at ({doc['status_at']}) is later than "
            f"created_at ({doc['created_at']}); a transition cannot be "
            "recorded before it happened"
        )


def check_streams(documents: dict[str, JsonDict], reports: dict[str, Report]) -> None:
    """Per-key rules: transition legality and status_at ordering."""
    streams: dict[tuple[str, str], list[tuple[datetime, str, JsonDict]]] = {}

    for path, doc in documents.items():
        decision_id = doc.get("decision_id")
        consumer_id = doc.get("consumer_id")
        moment = parse_timestamp(doc.get("status_at", ""))
        if not isinstance(decision_id, str) or not isinstance(consumer_id, str):
            continue
        if moment is None:
            continue
        streams.setdefault((decision_id, consumer_id), []).append((moment, path, doc))

    for (decision_id, consumer_id), records in streams.items():
        records.sort(key=lambda item: item[0])
        key = f"{decision_id} / {consumer_id}"

        for index in range(1, len(records)):
            previous_at, _, previous = records[index - 1]
            current_at, path, current = records[index]
            report = reports[path]

            if current_at == previous_at:
                report.error(
                    f"two records in stream {key} share status_at "
                    f"{current.get('status_at')}; order cannot be determined"
                )
                continue

            before = previous.get("status", "")
            after = current.get("status", "")
            allowed = TRANSITIONS.get(before)

            if allowed is None:
                continue
            if not allowed:
                report.error(
                    f"stream {key} continues after {before}, which is terminal"
                )
            elif after not in allowed:
                report.error(
                    f"illegal transition in stream {key}: {before} to {after}; "
                    f"{before} may only become " + ", ".join(sorted(allowed))
                )


def check_state_references(
    doc: JsonDict, report: Report, decisions: dict[str, JsonDict]
) -> None:
    """Where the Decision is available, the record must be consistent with it."""
    decision_id = doc.get("decision_id")
    if not isinstance(decision_id, str):
        return

    decision = decisions.get(decision_id)
    if decision is None:
        report.note(
            f"references {decision_id}, which is not among the documents being "
            "validated; the Decision could not be cross-checked"
        )
        return

    recommendation_id = doc.get("recommendation_id")
    if recommendation_id:
        known = {
            rec.get("recommendation_id") for rec in decision.get("recommendations", [])
        }
        if recommendation_id not in known:
            report.error(
                f"recommendation_id {recommendation_id} is not one of the "
                f"recommendations on {decision_id}"
            )


# ------------------------------------------------------------------- driver


def load_documents(paths: list[str], reports: list[Report]) -> dict[str, JsonDict]:
    """Parse each path, recording failures on its report."""
    documents: dict[str, JsonDict] = {}
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
    return documents


def check_kind(
    kind: str,
    documents: dict[str, JsonDict],
    reports: dict[str, Report],
    registry: dict[str, JsonDict] | None,
    schema_id: str,
    decisions: dict[str, JsonDict],
) -> None:
    """Apply the semantic rules for one document kind."""
    if kind == "decision":
        index = {
            doc["decision_id"]: doc
            for doc in documents.values()
            if isinstance(doc.get("decision_id"), str)
        }
        for path, doc in documents.items():
            report = reports[path]
            check_expiry(doc, report)
            check_approval(doc, report)
            check_supersedes(doc, report, index)
            check_schema_version(doc, report, schema_id)
            check_category(doc, report, registry)
            check_summary_style(doc, report)
            check_rationale_present(doc, report)
    else:
        for path, doc in documents.items():
            report = reports[path]
            check_state_timestamps(doc, report)
            check_schema_version(doc, report, schema_id)
            check_state_references(doc, report, decisions)
        check_streams(documents, reports)


def unique_ids(
    documents: dict[str, JsonDict], field: str, reports: dict[str, Report]
) -> None:
    """No identifier may be used by two documents."""
    seen: dict[str, str] = {}
    for path, doc in documents.items():
        value = doc.get(field)
        if not isinstance(value, str):
            continue
        if value in seen:
            reports[path].error(f"{field} {value} is also used by {seen[value]}")
        else:
            seen[value] = path


def validate(
    targets: list[tuple[str, str, list[str]]],
    manifest_path: str | None,
    registry_path: str | None,
    registry_doc_path: str,
    strict: bool,
    color: bool,
) -> int:
    def paint(text: str, code: str) -> str:
        return f"{code}{text}{RESET}" if color else text

    registry: dict[str, JsonDict] | None = None
    if registry_path:
        try:
            registry = load_registry(registry_path)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            sys.stderr.write(f"error: registry at {registry_path} is unusable: {exc}\n")
            return 2

        if registry is None:
            print(
                f"{paint('registry', DIM)}  {registry_path} not found; "
                "category membership not enforced"
            )
        else:
            drift = check_registry_sync(registry_path, registry_doc_path)
            if drift:
                print(f"{paint('FAIL', RED)}    {registry_path}")
                for message in drift:
                    print(f"          {paint('error', RED)} {message}")
                print()
                print("registry and documentation disagree")
                return 1
            print(
                f"{paint('registry', DIM)}  {len(registry)} categories, "
                f"in step with {registry_doc_path}"
            )

    if manifest_path:
        drift = check_manifest(manifest_path)
        if drift:
            print(f"{paint('FAIL', RED)}    {manifest_path}")
            for message in drift:
                print(f"          {paint('error', RED)} {message}")
            print()
            print("the manifest and the schemas disagree")
            return 1
        if Path(manifest_path).exists():
            data = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
            names = ", ".join(
                f"{e.get('name')} {e.get('version')}" for e in data.get("schemas", [])
            )
            print(f"{paint('manifest', DIM)}  JAM {data.get('jam_version')}: {names}")

    all_reports: list[Report] = []
    decisions: dict[str, JsonDict] = {}

    for kind, schema_path, paths in targets:
        try:
            schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        except FileNotFoundError:
            sys.stderr.write(f"error: schema not found at {schema_path}\n")
            return 2
        except json.JSONDecodeError as exc:
            sys.stderr.write(f"error: {schema_path} is not valid JSON: {exc}\n")
            return 2

        try:
            Draft202012Validator.check_schema(schema)
        except Exception as exc:
            sys.stderr.write(
                f"error: {schema_path} is not a valid JSON Schema: {exc}\n"
            )
            return 2

        print(f"{paint('schema', DIM)}  {schema_path} is valid draft 2020-12")

        if not paths:
            print(f"{paint('note', DIM)}    no {kind} documents matched")
            continue

        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        kind_reports: list[Report] = []
        documents = load_documents(paths, kind_reports)
        by_path = {report.path: report for report in kind_reports}

        for path, doc in documents.items():
            for error in sorted(validator.iter_errors(doc), key=lambda e: list(e.path)):
                location = "/".join(str(p) for p in error.path) or "<root>"
                by_path[path].error(f"{location}: {error.message}")

        check_kind(kind, documents, by_path, registry, schema.get("$id", ""), decisions)
        unique_ids(
            documents, "decision_id" if kind == "decision" else "state_id", by_path
        )

        if kind == "decision":
            decisions.update(
                {
                    doc["decision_id"]: doc
                    for doc in documents.values()
                    if isinstance(doc.get("decision_id"), str)
                }
            )

        all_reports.extend(kind_reports)

    failures = 0
    warnings = 0
    for report in all_reports:
        if report.errors:
            failures += 1
            print(f"{paint('FAIL', RED)}    {report.path}")
        else:
            print(f"{paint('ok', GREEN)}      {report.path}")

        for message in report.errors:
            print(f"          {paint('error', RED)} {message}")
        for message in report.warnings:
            warnings += 1
            print(f"          {paint('warn', YELLOW)}  {message}")
        for message in report.notes:
            print(f"          {paint('note', DIM)}  {message}")

    print()
    print(f"{len(all_reports)} document(s), {failures} failed, {warnings} warning(s)")

    if failures:
        return 1
    if warnings and strict:
        print(paint("failing because --strict treats warnings as errors", RED))
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate JAM contract documents against their schemas."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="documents to validate (default: both example directories)",
    )
    parser.add_argument(
        "--kind",
        choices=["decision", "decision-state"],
        default="decision",
        help="document kind, when paths are given explicitly",
    )
    parser.add_argument(
        "--schema",
        default=None,
        help="override the schema for explicitly given paths",
    )
    parser.add_argument(
        "--manifest",
        default=DEFAULT_MANIFEST,
        help=f"path to the release manifest (default: {DEFAULT_MANIFEST})",
    )
    parser.add_argument(
        "--no-manifest",
        action="store_true",
        help="skip manifest checking",
    )
    parser.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY,
        help=f"path to the category registry (default: {DEFAULT_REGISTRY})",
    )
    parser.add_argument(
        "--registry-doc",
        default=DEFAULT_REGISTRY_DOC,
        help=f"path to the registry documentation (default: {DEFAULT_REGISTRY_DOC})",
    )
    parser.add_argument(
        "--no-registry",
        action="store_true",
        help="skip category registry enforcement entirely",
    )
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as failures"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="disable colored output"
    )
    args = parser.parse_args()

    targets: list[tuple[str, str, list[str]]]
    if args.paths:
        schema = args.schema or (
            DECISION_SCHEMA if args.kind == "decision" else STATE_SCHEMA
        )
        targets = [(args.kind, schema, args.paths)]
    else:
        targets = [
            (
                "decision",
                DECISION_SCHEMA,
                [normalize(p) for p in sorted(glob.glob(DECISION_GLOB))],
            ),
            (
                "decision-state",
                STATE_SCHEMA,
                [normalize(p) for p in sorted(glob.glob(STATE_GLOB))],
            ),
        ]

    manifest_path = None if args.no_manifest else args.manifest
    registry_path = None if args.no_registry else args.registry
    color = sys.stdout.isatty() and not args.no_color

    return validate(
        targets,
        manifest_path,
        registry_path,
        args.registry_doc,
        args.strict,
        color,
    )


if __name__ == "__main__":
    raise SystemExit(main())
