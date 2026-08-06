"""Read and validate JAM repository manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    model_validator,
)


class RepositoryIdentity(BaseModel):
    """Repository identity declared by JAM."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    type: Literal["engine", "application", "foundation", "orchestrator"]
    role: str = Field(min_length=1)


class JamIdentity(BaseModel):
    """JAM versions used by the repository."""

    model_config = ConfigDict(extra="forbid")

    manual_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    conformance_version: str = Field(pattern=r"^\d+\.\d+$")


class ScaffoldIdentity(BaseModel):
    """Scaffold origin for the repository."""

    model_config = ConfigDict(extra="forbid")

    template: str = Field(min_length=1)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")


class PythonIdentity(BaseModel):
    """Python layout and package identity."""

    model_config = ConfigDict(extra="forbid")

    layout: Literal["single-package", "monorepo"] = "single-package"
    package: str | None = None
    packages: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_layout(self) -> Self:
        """Validate fields appropriate to the declared layout."""

        if self.layout == "single-package":
            if self.package is None or not self.package.strip():
                raise ValueError("single-package layout requires python.package")

            if self.packages:
                raise ValueError("single-package layout cannot declare python.packages")

            return self

        if self.package is not None:
            raise ValueError("monorepo layout cannot declare python.package")

        if not self.packages:
            raise ValueError("monorepo layout requires python.packages")

        if len(set(self.packages)) != len(self.packages):
            raise ValueError("monorepo package paths must be unique")

        for package_path in self.packages:
            parts = package_path.split("/")

            if (
                not package_path
                or "\\" in package_path
                or package_path.startswith("/")
                or any(part in {"", ".", ".."} for part in parts)
            ):
                raise ValueError(
                    "monorepo package paths must be safe "
                    f"repository-relative paths: {package_path!r}"
                )

        return self


class JamManifest(BaseModel):
    """Canonical repository manifest."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    repository: RepositoryIdentity
    jam: JamIdentity
    scaffold: ScaffoldIdentity
    python: PythonIdentity


class ManifestError(ValueError):
    """Raised when a JAM manifest cannot be read or validated."""


def load_manifest(repository: Path) -> JamManifest:
    """Load and validate jam.yaml from a repository."""

    path = repository.resolve() / "jam.yaml"

    if not path.is_file():
        raise ManifestError(f"JAM manifest is missing: {path}")

    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ManifestError(f"Invalid JAM manifest YAML: {exc}") from exc

    try:
        return JamManifest.model_validate(payload)
    except ValidationError as exc:
        raise ManifestError(f"Invalid JAM manifest:\n{exc}") from exc
