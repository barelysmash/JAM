"""Validate repositories against baseline JAM conformance rules."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Final

from jam_sdk.manifest import ManifestError, load_manifest

JAM_DECLARATION: Final[str] = "Built with JAM"
TOKEN_PATTERN: Final[re.Pattern[str]] = re.compile(r"\{\{[A-Z0-9_]+\}\}")

REQUIRED_FILES: Final[tuple[str, ...]] = (
    "jam.yaml",
    "README.md",
    "pyproject.toml",
    "docs/adr/ADR-0001-repository-role.md",
)

TEXT_SUFFIXES: Final[frozenset[str]] = frozenset(
    {
        ".md",
        ".py",
        ".toml",
        ".yaml",
        ".yml",
        ".json",
        ".txt",
    }
)


@dataclass(frozen=True, slots=True)
class ValidationCheck:
    """One JAM conformance check."""

    name: str
    passed: bool
    message: str


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Complete JAM conformance report for a repository."""

    repository: str
    passed: bool
    checks: tuple[ValidationCheck, ...]

    def to_json(self) -> str:
        """Serialize the report as deterministic JSON."""

        return json.dumps(
            asdict(self),
            indent=2,
            sort_keys=True,
        )


def validate_repository(repository: Path) -> ValidationReport:
    """Validate a repository against baseline JAM requirements."""

    root = repository.resolve()
    checks: list[ValidationCheck] = []

    if not root.is_dir():
        checks.append(
            ValidationCheck(
                name="repository",
                passed=False,
                message=f"Repository directory does not exist: {root}",
            )
        )
        return _build_report(root, checks)

    checks.extend(_check_required_files(root))
    checks.append(_check_manifest(root))
    checks.append(_check_readme_declaration(root))
    checks.append(_check_platform_role(root))
    checks.append(_check_python_configuration(root))
    checks.append(check_ci_workflows(root))
    checks.append(_check_repository_role_adr(root))
    checks.append(_check_unresolved_tokens(root))

    return _build_report(root, checks)


def format_validation_report(report: ValidationReport) -> str:
    """Render a human-readable validation report."""

    lines = [
        f"JAM validation: {report.repository}",
        "",
    ]

    for check in report.checks:
        marker = "✓" if check.passed else "✗"
        lines.append(f"{marker} {check.name}: {check.message}")

    lines.extend(
        [
            "",
            "PASS" if report.passed else "FAIL",
        ]
    )

    return "\n".join(lines)


def _build_report(
    root: Path,
    checks: list[ValidationCheck],
) -> ValidationReport:
    return ValidationReport(
        repository=str(root),
        passed=all(check.passed for check in checks),
        checks=tuple(checks),
    )


def _check_manifest(root: Path) -> ValidationCheck:
    try:
        manifest = load_manifest(root)
    except ManifestError as exc:
        return ValidationCheck(
            name="jam-manifest",
            passed=False,
            message=str(exc),
        )

    readme = root / "README.md"

    if readme.is_file():
        readme_text = readme.read_text(encoding="utf-8")

        if manifest.repository.role not in readme_text:
            return ValidationCheck(
                name="jam-manifest",
                passed=False,
                message=("manifest platform role does not match README"),
            )

    return ValidationCheck(
        name="jam-manifest",
        passed=True,
        message=(
            "manifest is valid: "
            f"{manifest.repository.name} / "
            f"{manifest.repository.role}"
        ),
    )


def _check_required_files(root: Path) -> list[ValidationCheck]:
    checks: list[ValidationCheck] = []

    for relative_path in REQUIRED_FILES:
        path = root / relative_path
        checks.append(
            ValidationCheck(
                name=f"required-file:{relative_path}",
                passed=path.is_file(),
                message=("present" if path.is_file() else f"missing {relative_path}"),
            )
        )

    return checks


def _check_readme_declaration(root: Path) -> ValidationCheck:
    path = root / "README.md"

    if not path.is_file():
        return ValidationCheck(
            name="jam-declaration",
            passed=False,
            message="README.md is missing",
        )

    text = path.read_text(encoding="utf-8")
    passed = JAM_DECLARATION in text

    return ValidationCheck(
        name="jam-declaration",
        passed=passed,
        message=(
            "README declares JAM conformance"
            if passed
            else f'README must contain "{JAM_DECLARATION}"'
        ),
    )


def _check_platform_role(root: Path) -> ValidationCheck:
    path = root / "README.md"

    if not path.is_file():
        return ValidationCheck(
            name="platform-role",
            passed=False,
            message="README.md is missing",
        )

    text = path.read_text(encoding="utf-8")
    passed = bool(
        re.search(
            r"^\*\*Platform role:\*\*\s+\S.+$",
            text,
            flags=re.MULTILINE,
        )
    )

    return ValidationCheck(
        name="platform-role",
        passed=passed,
        message=(
            "platform role is declared"
            if passed
            else "README must declare **Platform role:**"
        ),
    )


def _check_python_configuration(
    root: Path,
) -> ValidationCheck:
    path = root / "pyproject.toml"

    if not path.is_file():
        return ValidationCheck(
            name="python-configuration",
            passed=False,
            message="pyproject.toml is missing",
        )

    try:
        manifest = load_manifest(root)
    except ManifestError as exc:
        return ValidationCheck(
            name="python-configuration",
            passed=False,
            message=(f"cannot determine Python layout: {exc}"),
        )

    root_text = path.read_text(encoding="utf-8")

    if manifest.python.layout == "monorepo":
        return _check_monorepo_python_configuration(
            root,
            root_text,
            manifest.python.packages,
        )

    return _check_single_package_python_configuration(
        root_text,
    )


def _check_single_package_python_configuration(
    root_text: str,
) -> ValidationCheck:
    required_markers = (
        "[project]",
        "[tool.ruff]",
        "[tool.mypy]",
        "[tool.pytest.ini_options]",
    )
    missing = [marker for marker in required_markers if marker not in root_text]

    return ValidationCheck(
        name="python-configuration",
        passed=not missing,
        message=(
            "single-package Python tooling is configured"
            if not missing
            else f"missing sections: {', '.join(missing)}"
        ),
    )


def _check_monorepo_python_configuration(
    root: Path,
    root_text: str,
    package_paths: tuple[str, ...],
) -> ValidationCheck:
    missing_root_markers = [
        marker
        for marker in (
            "[tool.ruff]",
            "[tool.mypy]",
        )
        if marker not in root_text
    ]

    missing_package_files = [
        f"{package_path}/pyproject.toml"
        for package_path in package_paths
        if not (root / package_path / "pyproject.toml").is_file()
    ]

    problems: list[str] = []

    if missing_root_markers:
        problems.append("missing root sections: " + ", ".join(missing_root_markers))

    if missing_package_files:
        problems.append(
            "missing package manifests: " + ", ".join(missing_package_files)
        )

    return ValidationCheck(
        name="python-configuration",
        passed=not problems,
        message=(
            f"monorepo Python tooling is configured for {len(package_paths)} package(s)"
            if not problems
            else "; ".join(problems)
        ),
    )


def discover_workflow_files(root: Path) -> tuple[Path, ...]:
    """Discover GitHub Actions workflow files."""

    directory = root / ".github/workflows"

    if not directory.is_dir():
        return ()

    workflows = {
        path
        for pattern in ("*.yml", "*.yaml")
        for path in directory.glob(pattern)
        if path.is_file()
    }

    return tuple(
        sorted(
            workflows,
            key=lambda path: path.as_posix(),
        )
    )


def check_ci_workflows(root: Path) -> ValidationCheck:
    """Check required commands across all workflow files."""

    workflows = discover_workflow_files(root)

    if not workflows:
        return ValidationCheck(
            name="ci-workflow",
            passed=False,
            message="CI workflows are missing",
        )

    text = "\n".join(path.read_text(encoding="utf-8") for path in workflows)
    required_commands = (
        "ruff check",
        "mypy",
        "pytest",
    )
    missing = [command for command in required_commands if command not in text]

    return ValidationCheck(
        name="ci-workflow",
        passed=not missing,
        message=(
            f"CI runs Ruff, mypy, and pytest across {len(workflows)} workflow file(s)"
            if not missing
            else f"CI workflows are missing: {', '.join(missing)}"
        ),
    )


def _check_repository_role_adr(root: Path) -> ValidationCheck:
    path = root / "docs/adr/ADR-0001-repository-role.md"

    if not path.is_file():
        return ValidationCheck(
            name="repository-role-adr",
            passed=False,
            message="repository-role ADR is missing",
        )

    text = path.read_text(encoding="utf-8")
    passed = "# ADR-0001: Repository Role" in text and "Status: Accepted" in text

    return ValidationCheck(
        name="repository-role-adr",
        passed=passed,
        message=(
            "repository role ADR is accepted"
            if passed
            else "repository role ADR is incomplete"
        ),
    )


def _check_unresolved_tokens(root: Path) -> ValidationCheck:
    unresolved: list[str] = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(part in _ignored_directories() for part in path.parts):
            continue

        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if TOKEN_PATTERN.search(text):
            unresolved.append(str(path.relative_to(root)))

    return ValidationCheck(
        name="template-tokens",
        passed=not unresolved,
        message=(
            "no unresolved template tokens"
            if not unresolved
            else "unresolved tokens in: " + ", ".join(sorted(unresolved))
        ),
    )


def _ignored_directories() -> frozenset[str]:
    return frozenset(
        {
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            "build",
            "dist",
        }
    )
