"""Render repositories from JAM templates."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shutil import copytree, ignore_patterns
from typing import Final

PROJECT_NAME_TOKEN: Final[str] = "{{PROJECT_NAME}}"
PACKAGE_NAME_TOKEN: Final[str] = "{{PACKAGE_NAME}}"
PLATFORM_ROLE_TOKEN: Final[str] = "{{PLATFORM_ROLE}}"


class ScaffoldError(ValueError):
    """Raised when a repository cannot be scaffolded safely."""


@dataclass(frozen=True, slots=True)
class ScaffoldRequest:
    """Inputs required to render a JAM repository template."""

    project_name: str
    package_name: str
    platform_role: str
    destination: Path


def scaffold_python_engine(
    request: ScaffoldRequest,
    *,
    template_root: Path,
) -> Path:
    """Render the Python engine template into a new directory."""

    _validate_request(request)

    template = template_root / "python-engine"

    if not template.is_dir():
        raise ScaffoldError(f"Template does not exist: {template}")

    destination = request.destination.resolve()

    if destination.exists() and any(destination.iterdir()):
        raise ScaffoldError(f"Destination is not empty: {destination}")

    destination.mkdir(parents=True, exist_ok=True)
    copytree(
        template,
        destination,
        dirs_exist_ok=True,
        ignore=ignore_patterns(
            "__pycache__",
            "*.pyc",
            "*.pyo",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
        ),
    )

    package_placeholder = destination / "src/package_name"
    package_destination = destination / "src" / request.package_name

    if not package_placeholder.is_dir():
        raise ScaffoldError(f"Package placeholder is missing: {package_placeholder}")

    package_placeholder.rename(package_destination)

    replacements = {
        PROJECT_NAME_TOKEN: request.project_name,
        PACKAGE_NAME_TOKEN: request.package_name,
        PLATFORM_ROLE_TOKEN: request.platform_role,
    }

    for path in destination.rglob("*"):
        if path.is_file():
            _replace_tokens(path, replacements)

    return destination


def _validate_request(request: ScaffoldRequest) -> None:
    if not request.project_name.strip():
        raise ScaffoldError("project_name cannot be empty")

    if not request.platform_role.strip():
        raise ScaffoldError("platform_role cannot be empty")

    if not request.package_name.isidentifier():
        raise ScaffoldError("package_name must be a valid Python identifier")

    if request.package_name != request.package_name.lower():
        raise ScaffoldError("package_name must be lowercase")


def _replace_tokens(
    path: Path,
    replacements: dict[str, str],
) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return

    for token, value in replacements.items():
        text = text.replace(token, value)

    path.write_text(text, encoding="utf-8")
