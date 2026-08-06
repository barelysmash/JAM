"""Read and validate JAM repository manifests."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError


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
    """Python package identity."""

    model_config = ConfigDict(extra="forbid")

    package: str = Field(min_length=1)


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
