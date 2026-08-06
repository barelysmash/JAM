"""Adopt JAM safely inside an existing repository."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from shutil import copy2
from typing import Final, Literal

import yaml

from jam_sdk.manifest import (
    JamIdentity,
    JamManifest,
    PythonIdentity,
    RepositoryIdentity,
    ScaffoldIdentity,
)
from jam_sdk.validate import ValidationReport, validate_repository

RepositoryType = Literal[
    "engine",
    "application",
    "foundation",
    "orchestrator",
]

PythonLayout = Literal[
    "single-package",
    "monorepo",
]

JAM_DECLARATION: Final[str] = "> Built with JAM — the JARVIS Architecture Manual."
MANUAL_VERSION: Final[str] = "1.3.0"
CONFORMANCE_VERSION: Final[str] = "1.0"
SCAFFOLD_VERSION: Final[str] = "1.0.0"

BASELINE_FILES: Final[tuple[str, ...]] = (
    ".github/workflows/ci.yml",
    ".gitignore",
)


class InitError(ValueError):
    """Raised when JAM cannot safely initialize a repository."""


@dataclass(frozen=True, slots=True)
class InitAction:
    """One initialization action."""

    path: str
    operation: Literal["create", "append", "preserve"]
    applied: bool
    message: str


@dataclass(frozen=True, slots=True)
class InitReport:
    """Result of adopting JAM in an existing repository."""

    repository: str
    dry_run: bool
    actions: tuple[InitAction, ...]
    validation: ValidationReport

    @property
    def passed(self) -> bool:
        return self.validation.passed

    def to_json(self) -> str:
        return json.dumps(
            asdict(self),
            indent=2,
            sort_keys=True,
        )


def initialize_repository(
    repository: Path,
    *,
    project_name: str,
    package_name: str | None,
    platform_role: str,
    repository_type: RepositoryType,
    scaffold_template: str,
    template_root: Path,
    python_layout: PythonLayout = "single-package",
    package_paths: tuple[str, ...] = (),
    include_baseline: bool = False,
    dry_run: bool = False,
) -> InitReport:
    """Add JAM metadata and safe baseline files to an existing repository."""

    root = repository.resolve()
    try:
        python_identity = PythonIdentity(
            layout=python_layout,
            package=package_name,
            packages=package_paths,
        )
    except ValueError as exc:
        raise InitError(f"Invalid Python configuration: {exc}") from exc

    _validate_inputs(
        root=root,
        project_name=project_name,
        platform_role=platform_role,
        scaffold_template=scaffold_template,
        python_identity=python_identity,
    )

    actions: list[InitAction] = []

    manifest = JamManifest(
        schema_version="1.0",
        repository=RepositoryIdentity(
            name=project_name,
            type=repository_type,
            role=platform_role,
        ),
        jam=JamIdentity(
            manual_version=MANUAL_VERSION,
            conformance_version=CONFORMANCE_VERSION,
        ),
        scaffold=ScaffoldIdentity(
            template=scaffold_template,
            version=SCAFFOLD_VERSION,
        ),
        python=python_identity,
    )

    manifest_text: str = yaml.safe_dump(
        manifest.model_dump(mode="json"),
        sort_keys=False,
        allow_unicode=True,
    )

    actions.append(
        _create_text_file(
            root / "jam.yaml",
            manifest_text,
            root=root,
            dry_run=dry_run,
        )
    )

    actions.append(
        _ensure_readme(
            root / "README.md",
            project_name=project_name,
            platform_role=platform_role,
            root=root,
            dry_run=dry_run,
        )
    )

    adr_source = (
        template_root / scaffold_template / "docs/adr/ADR-0001-repository-role.md"
    )
    adr_destination = root / "docs/adr/ADR-0001-repository-role.md"

    actions.append(
        _create_rendered_file(
            source=adr_source,
            destination=adr_destination,
            root=root,
            replacements={
                "{{PROJECT_NAME}}": project_name,
                "{{PACKAGE_NAME}}": package_name or project_name,
                "{{PLATFORM_ROLE}}": platform_role,
            },
            dry_run=dry_run,
        )
    )

    if include_baseline:
        for relative_path in BASELINE_FILES:
            actions.append(
                _copy_template_file(
                    source=template_root / scaffold_template / relative_path,
                    destination=root / relative_path,
                    root=root,
                    dry_run=dry_run,
                )
            )

    validation = validate_repository(root)

    return InitReport(
        repository=str(root),
        dry_run=dry_run,
        actions=tuple(actions),
        validation=validation,
    )


def format_init_report(report: InitReport) -> str:
    """Render a human-readable initialization report."""

    lines = [
        f"JAM init: {report.repository}",
        "",
    ]

    for action in report.actions:
        if action.applied:
            marker = "✓"
        elif action.operation == "preserve":
            marker = "•"
        else:
            marker = "→"

        lines.append(f"{marker} {action.path}: {action.message}")

    lines.extend(
        [
            "",
            "DRY RUN" if report.dry_run else "APPLIED",
            "PASS" if report.passed else "FAIL",
        ]
    )

    return "\n".join(lines)


def _validate_inputs(
    *,
    root: Path,
    project_name: str,
    platform_role: str,
    scaffold_template: str,
    python_identity: PythonIdentity,
) -> None:
    if not root.is_dir():
        raise InitError(f"Repository directory does not exist: {root}")

    if not project_name.strip():
        raise InitError("project_name cannot be empty")

    if not platform_role.strip():
        raise InitError("platform_role cannot be empty")

    if not scaffold_template.strip():
        raise InitError("scaffold_template cannot be empty")

    if python_identity.layout == "single-package":
        package_name = python_identity.package

        if package_name is None:
            raise InitError("single-package layout requires --package")

        if not package_name.isidentifier():
            raise InitError("package_name must be a valid Python identifier")

        if package_name != package_name.lower():
            raise InitError("package_name must be lowercase")

        return

    missing_manifests = [
        f"{package_path}/pyproject.toml"
        for package_path in python_identity.packages
        if not (root / package_path / "pyproject.toml").is_file()
    ]

    if missing_manifests:
        raise InitError("missing package manifests: " + ", ".join(missing_manifests))


def _create_text_file(
    destination: Path,
    content: str,
    *,
    root: Path,
    dry_run: bool,
) -> InitAction:
    relative_path = str(destination.relative_to(root))

    if destination.exists():
        return InitAction(
            path=relative_path,
            operation="preserve",
            applied=False,
            message="preserved existing file",
        )

    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content, encoding="utf-8")

    return InitAction(
        path=relative_path,
        operation="create",
        applied=not dry_run,
        message="would create" if dry_run else "created",
    )


def _ensure_readme(
    destination: Path,
    *,
    project_name: str,
    platform_role: str,
    root: Path,
    dry_run: bool,
) -> InitAction:
    if not destination.exists():
        content = (
            f"# {project_name}\n\n"
            f"{JAM_DECLARATION}\n\n"
            f"**Platform role:** {platform_role}\n"
        )
        return _create_text_file(
            destination,
            content,
            root=root,
            dry_run=dry_run,
        )

    text = destination.read_text(encoding="utf-8")
    additions: list[str] = []

    if "Built with JAM" not in text:
        additions.append(JAM_DECLARATION)

    if "**Platform role:**" not in text:
        additions.append(f"**Platform role:** {platform_role}")

    relative_path = str(destination.relative_to(root))

    if not additions:
        return InitAction(
            path=relative_path,
            operation="preserve",
            applied=False,
            message="JAM declaration and platform role already present",
        )

    addition = "\n\n## JAM\n\n" + "\n\n".join(additions) + "\n"

    if not dry_run:
        destination.write_text(
            text.rstrip() + addition,
            encoding="utf-8",
        )

    return InitAction(
        path=relative_path,
        operation="append",
        applied=not dry_run,
        message=(
            "would append JAM declaration" if dry_run else "appended JAM declaration"
        ),
    )


def _create_rendered_file(
    *,
    source: Path,
    destination: Path,
    root: Path,
    replacements: dict[str, str],
    dry_run: bool,
) -> InitAction:
    if not source.is_file():
        raise InitError(f"Template file is missing: {source}")

    text = source.read_text(encoding="utf-8")

    for token, value in replacements.items():
        text = text.replace(token, value)

    return _create_text_file(
        destination,
        text,
        root=root,
        dry_run=dry_run,
    )


def _copy_template_file(
    *,
    source: Path,
    destination: Path,
    root: Path,
    dry_run: bool,
) -> InitAction:
    relative_path = str(destination.relative_to(root))

    if destination.exists():
        return InitAction(
            path=relative_path,
            operation="preserve",
            applied=False,
            message="preserved existing file",
        )

    if not source.is_file():
        raise InitError(f"Template file is missing: {source}")

    if not dry_run:
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy2(source, destination)

    return InitAction(
        path=relative_path,
        operation="create",
        applied=not dry_run,
        message=("would copy from scaffold" if dry_run else "copied from scaffold"),
    )
