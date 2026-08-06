"""Diagnose and repair safe JAM conformance issues."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from shutil import copy2
from typing import Final

from jam_sdk.manifest import ManifestError, load_manifest
from jam_sdk.validate import ValidationReport, validate_repository

REPAIRABLE_FILES: Final[tuple[str, ...]] = (
    ".github/workflows/ci.yml",
    ".gitignore",
    "docs/adr/ADR-0001-repository-role.md",
)


@dataclass(frozen=True, slots=True)
class DoctorAction:
    """One repair action proposed or applied by JAM Doctor."""

    path: str
    repairable: bool
    applied: bool
    message: str


@dataclass(frozen=True, slots=True)
class DoctorReport:
    """Diagnosis and repair result for one repository."""

    repository: str
    before: ValidationReport
    after: ValidationReport
    actions: tuple[DoctorAction, ...]

    @property
    def passed(self) -> bool:
        return self.after.passed

    def to_json(self) -> str:
        return json.dumps(
            asdict(self),
            indent=2,
            sort_keys=True,
        )


def doctor_repository(
    repository: Path,
    *,
    template_root: Path,
    fix: bool = False,
) -> DoctorReport:
    """Diagnose a repository and repair deterministic omissions."""

    root = repository.resolve()
    before = validate_repository(root)
    actions: list[DoctorAction] = []

    try:
        manifest = load_manifest(root)
    except ManifestError:
        manifest = None

    for relative_path in REPAIRABLE_FILES:
        destination = root / relative_path

        if destination.exists():
            continue

        if manifest is None:
            actions.append(
                DoctorAction(
                    path=relative_path,
                    repairable=False,
                    applied=False,
                    message="manifest required before repair",
                )
            )
            continue

        source = template_root / manifest.scaffold.template / relative_path

        if not source.is_file():
            actions.append(
                DoctorAction(
                    path=relative_path,
                    repairable=False,
                    applied=False,
                    message=f"template source missing: {source}",
                )
            )
            continue

        if fix:
            destination.parent.mkdir(parents=True, exist_ok=True)
            copy2(source, destination)

        actions.append(
            DoctorAction(
                path=relative_path,
                repairable=True,
                applied=fix,
                message=(
                    "restored from scaffold" if fix else "can be restored from scaffold"
                ),
            )
        )

    after = validate_repository(root)

    return DoctorReport(
        repository=str(root),
        before=before,
        after=after,
        actions=tuple(actions),
    )


def format_doctor_report(report: DoctorReport) -> str:
    """Render a human-readable doctor report."""

    lines = [
        f"JAM doctor: {report.repository}",
        "",
    ]

    if not report.actions:
        lines.append("No deterministic repairs required.")
    else:
        for action in report.actions:
            if action.applied:
                marker = "✓"
            elif action.repairable:
                marker = "→"
            else:
                marker = "!"
            lines.append(f"{marker} {action.path}: {action.message}")

    lines.extend(
        [
            "",
            "PASS" if report.passed else "FAIL",
        ]
    )

    return "\n".join(lines)
