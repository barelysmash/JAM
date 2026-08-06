from pathlib import Path

from jam_sdk.doctor import (
    doctor_repository,
    format_doctor_report,
)
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


def test_doctor_reports_no_repairs_for_valid_repository(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)

    report = doctor_repository(
        repository,
        template_root=Path("templates"),
    )

    assert report.passed is True
    assert report.actions == ()


def test_doctor_identifies_repairable_missing_file(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)
    workflow = repository / ".github/workflows/ci.yml"
    workflow.unlink()

    report = doctor_repository(
        repository,
        template_root=Path("templates"),
    )

    assert report.passed is False
    assert any(
        action.path == ".github/workflows/ci.yml"
        and action.repairable
        and not action.applied
        for action in report.actions
    )


def test_doctor_fixes_missing_file(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)
    workflow = repository / ".github/workflows/ci.yml"
    workflow.unlink()

    report = doctor_repository(
        repository,
        template_root=Path("templates"),
        fix=True,
    )

    assert workflow.is_file()
    assert report.passed is True
    assert any(action.applied for action in report.actions)


def test_doctor_never_overwrites_existing_file(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)
    gitignore = repository / ".gitignore"
    gitignore.write_text("custom\n", encoding="utf-8")

    report = doctor_repository(
        repository,
        template_root=Path("templates"),
        fix=True,
    )

    assert gitignore.read_text(encoding="utf-8") == "custom\n"
    assert report.actions == ()


def test_doctor_requires_manifest_for_repairs(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)
    (repository / "jam.yaml").unlink()
    (repository / ".gitignore").unlink()

    report = doctor_repository(
        repository,
        template_root=Path("templates"),
        fix=True,
    )

    assert report.passed is False
    assert any(
        action.path == ".gitignore" and not action.repairable
        for action in report.actions
    )


def test_doctor_report_is_human_readable(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)

    output = format_doctor_report(
        doctor_repository(
            repository,
            template_root=Path("templates"),
        )
    )

    assert "JAM doctor:" in output
    assert "PASS" in output


def test_doctor_preserves_conformant_split_workflows(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)
    workflow_directory = repository / ".github/workflows"
    (workflow_directory / "ci.yml").unlink()

    (workflow_directory / "lint.yml").write_text(
        """
name: Lint
jobs:
  lint:
    steps:
      - run: python -m ruff check .
      - run: python -m mypy
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (workflow_directory / "tests.yaml").write_text(
        """
name: Tests
jobs:
  tests:
    steps:
      - run: python -m pytest
""".strip()
        + "\n",
        encoding="utf-8",
    )

    report = doctor_repository(
        repository,
        template_root=Path("templates"),
        fix=True,
    )

    assert report.passed is True
    assert report.actions == ()
    assert not (workflow_directory / "ci.yml").exists()
