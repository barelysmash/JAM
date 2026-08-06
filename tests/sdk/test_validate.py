from pathlib import Path

from jam_sdk.scaffold import (
    ScaffoldRequest,
    scaffold_python_engine,
)
from jam_sdk.validate import (
    format_validation_report,
    validate_repository,
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


def test_validate_generated_repository_passes(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)

    report = validate_repository(repository)

    assert report.passed is True
    assert all(check.passed for check in report.checks)


def test_validate_missing_repository_fails(
    tmp_path: Path,
) -> None:
    report = validate_repository(tmp_path / "missing")

    assert report.passed is False
    assert report.checks[0].name == "repository"


def test_validate_detects_missing_required_file(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)
    (repository / ".github/workflows/ci.yml").unlink()

    report = validate_repository(repository)

    assert report.passed is False
    assert any(
        check.name == "required-file:.github/workflows/ci.yml" and not check.passed
        for check in report.checks
    )


def test_validate_detects_missing_jam_declaration(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)
    readme = repository / "README.md"
    text = readme.read_text(encoding="utf-8")
    readme.write_text(
        text.replace("Built with JAM", "Built independently"),
        encoding="utf-8",
    )

    report = validate_repository(repository)

    assert report.passed is False
    assert any(
        check.name == "jam-declaration" and not check.passed for check in report.checks
    )


def test_validate_detects_unresolved_tokens(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)
    path = repository / "docs/unresolved.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Project: {{PROJECT_NAME}}",
        encoding="utf-8",
    )

    report = validate_repository(repository)

    assert report.passed is False
    assert any(
        check.name == "template-tokens" and not check.passed for check in report.checks
    )


def test_human_report_contains_status(
    tmp_path: Path,
) -> None:
    repository = _create_repository(tmp_path)

    output = format_validation_report(validate_repository(repository))

    assert "JAM validation:" in output
    assert "PASS" in output
    assert "✓ jam-declaration" in output


def test_json_report_is_machine_readable(
    tmp_path: Path,
) -> None:
    import json

    repository = _create_repository(tmp_path)
    payload = json.loads(validate_repository(repository).to_json())

    assert payload["passed"] is True
    assert payload["repository"] == str(repository.resolve())
