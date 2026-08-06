from pathlib import Path

import pytest
from jam_sdk.manifest import ManifestError, load_manifest
from jam_sdk.scaffold import (
    ScaffoldRequest,
    scaffold_python_engine,
)


def _create_repository(tmp_path: Path) -> Path:
    destination = tmp_path / "muse-demo"

    scaffold_python_engine(
        ScaffoldRequest(
            project_name="Muse Demo",
            package_name="muse_demo",
            platform_role="Creative Intelligence Engine",
            destination=destination,
        ),
        template_root=Path("templates"),
    )

    return destination


def test_load_manifest_from_generated_repository(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)

    manifest = load_manifest(repository)

    assert manifest.schema_version == "1.0"
    assert manifest.repository.name == "Muse Demo"
    assert manifest.repository.type == "engine"
    assert manifest.repository.role == "Creative Intelligence Engine"
    assert manifest.jam.manual_version == "1.3.0"
    assert manifest.scaffold.template == "python-engine"
    assert manifest.python.layout == "single-package"
    assert manifest.python.package == "muse_demo"
    assert manifest.python.packages == ()


def test_load_manifest_rejects_missing_file(
    tmp_path: Path,
) -> None:
    with pytest.raises(ManifestError, match="manifest is missing"):
        load_manifest(tmp_path)


def test_load_manifest_rejects_invalid_manifest(
    tmp_path: Path,
) -> None:
    path = tmp_path / "jam.yaml"
    path.write_text(
        "schema_version: invalid",
        encoding="utf-8",
    )

    with pytest.raises(ManifestError, match="Invalid JAM manifest"):
        load_manifest(tmp_path)


def test_load_manifest_accepts_monorepo_layout(
    tmp_path: Path,
) -> None:
    (tmp_path / "jam.yaml").write_text(
        """
schema_version: "1.0"

repository:
  name: "Atlas"
  type: "engine"
  role: "Operational Intelligence Engine"

jam:
  manual_version: "1.3.0"
  conformance_version: "1.0"

scaffold:
  template: "python-engine"
  version: "1.0.0"

python:
  layout: "monorepo"
  packages:
    - "packages/atlas-core"
    - "packages/atlas-events"
    - "apps/restaurantos"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    manifest = load_manifest(tmp_path)

    assert manifest.python.layout == "monorepo"
    assert manifest.python.package is None
    assert manifest.python.packages == (
        "packages/atlas-core",
        "packages/atlas-events",
        "apps/restaurantos",
    )


def test_load_manifest_rejects_duplicate_monorepo_paths(
    tmp_path: Path,
) -> None:
    (tmp_path / "jam.yaml").write_text(
        """
schema_version: "1.0"

repository:
  name: "Atlas"
  type: "engine"
  role: "Operational Intelligence Engine"

jam:
  manual_version: "1.3.0"
  conformance_version: "1.0"

scaffold:
  template: "python-engine"
  version: "1.0.0"

python:
  layout: "monorepo"
  packages:
    - "packages/atlas-core"
    - "packages/atlas-core"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ManifestError,
        match="package paths must be unique",
    ):
        load_manifest(tmp_path)


def test_load_manifest_rejects_unsafe_monorepo_path(
    tmp_path: Path,
) -> None:
    (tmp_path / "jam.yaml").write_text(
        """
schema_version: "1.0"

repository:
  name: "Atlas"
  type: "engine"
  role: "Operational Intelligence Engine"

jam:
  manual_version: "1.3.0"
  conformance_version: "1.0"

scaffold:
  template: "python-engine"
  version: "1.0.0"

python:
  layout: "monorepo"
  packages:
    - "../outside"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ManifestError,
        match="safe repository-relative paths",
    ):
        load_manifest(tmp_path)
