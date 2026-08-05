from pathlib import Path

import pytest
from jam_sdk.scaffold import (
    ScaffoldError,
    ScaffoldRequest,
    scaffold_python_engine,
)


def test_scaffold_renders_python_engine(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "muse-demo"

    result = scaffold_python_engine(
        ScaffoldRequest(
            project_name="Muse Demo",
            package_name="muse_demo",
            platform_role="Creative Intelligence Engine",
            destination=destination,
        ),
        template_root=Path("templates"),
    )

    assert result == destination.resolve()
    assert (destination / "src/muse_demo/__init__.py").is_file()

    readme = (destination / "README.md").read_text(encoding="utf-8")
    package = (destination / "src/muse_demo/__init__.py").read_text(encoding="utf-8")

    assert "Muse Demo" in readme
    assert "Creative Intelligence Engine" in readme
    assert "`muse_demo`" in readme
    assert "Muse Demo package" in package
    assert "{{" not in readme
    assert "{{" not in package


def test_scaffold_rejects_invalid_package_name(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ScaffoldError,
        match="valid Python identifier",
    ):
        scaffold_python_engine(
            ScaffoldRequest(
                project_name="Invalid",
                package_name="not-valid",
                platform_role="Test Engine",
                destination=tmp_path / "invalid",
            ),
            template_root=Path("templates"),
        )


def test_scaffold_rejects_uppercase_package_name(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ScaffoldError,
        match="must be lowercase",
    ):
        scaffold_python_engine(
            ScaffoldRequest(
                project_name="Invalid",
                package_name="InvalidPackage",
                platform_role="Test Engine",
                destination=tmp_path / "invalid",
            ),
            template_root=Path("templates"),
        )


def test_scaffold_rejects_nonempty_destination(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "existing"
    destination.mkdir()
    (destination / "existing.txt").write_text(
        "existing",
        encoding="utf-8",
    )

    with pytest.raises(
        ScaffoldError,
        match="Destination is not empty",
    ):
        scaffold_python_engine(
            ScaffoldRequest(
                project_name="Example",
                package_name="example",
                platform_role="Example Engine",
                destination=destination,
            ),
            template_root=Path("templates"),
        )


def test_scaffold_rejects_missing_template(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ScaffoldError,
        match="Template does not exist",
    ):
        scaffold_python_engine(
            ScaffoldRequest(
                project_name="Example",
                package_name="example",
                platform_role="Example Engine",
                destination=tmp_path / "example",
            ),
            template_root=tmp_path / "missing",
        )


def test_scaffold_creates_complete_python_project(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "atlas-demo"

    scaffold_python_engine(
        ScaffoldRequest(
            project_name="Atlas Demo",
            package_name="atlas_demo",
            platform_role="Operational Intelligence Engine",
            destination=destination,
        ),
        template_root=Path("templates"),
    )

    expected_files = [
        ".github/workflows/ci.yml",
        ".gitignore",
        "README.md",
        "pyproject.toml",
        "docs/adr/ADR-0001-repository-role.md",
        "src/atlas_demo/__init__.py",
        "tests/test_package.py",
    ]

    for relative_path in expected_files:
        assert (destination / relative_path).is_file()

    for rendered_file in destination.rglob("*"):
        if not rendered_file.is_file():
            continue

        try:
            text = rendered_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        assert "{{PROJECT_NAME}}" not in text
        assert "{{PACKAGE_NAME}}" not in text
        assert "{{PLATFORM_ROLE}}" not in text
