from pathlib import Path

import pytest
from _pytest.capture import CaptureFixture
from jam_sdk.cli import main
from jam_sdk.init import InitError, initialize_repository
from jam_sdk.manifest import load_manifest


def _create_existing_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "existing"
    repository.mkdir()

    (repository / "pyproject.toml").write_text(
        """
[project]
name = "existing"
version = "0.1.0"

[tool.ruff]

[tool.mypy]

[tool.pytest.ini_options]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    return repository


def test_init_adopts_existing_repository(
    tmp_path: Path,
) -> None:
    repository = _create_existing_repository(tmp_path)

    report = initialize_repository(
        repository,
        project_name="Muse",
        package_name="muse",
        platform_role="Creative Intelligence Engine",
        repository_type="engine",
        scaffold_template="python-engine",
        template_root=Path("templates"),
        include_baseline=True,
    )

    assert report.passed is True
    assert (repository / "jam.yaml").is_file()
    assert (repository / "README.md").is_file()
    assert (repository / "docs/adr/ADR-0001-repository-role.md").is_file()
    assert (repository / ".github/workflows/ci.yml").is_file()


def test_init_dry_run_does_not_write_files(
    tmp_path: Path,
) -> None:
    repository = _create_existing_repository(tmp_path)

    report = initialize_repository(
        repository,
        project_name="Muse",
        package_name="muse",
        platform_role="Creative Intelligence Engine",
        repository_type="engine",
        scaffold_template="python-engine",
        template_root=Path("templates"),
        include_baseline=True,
        dry_run=True,
    )

    assert report.dry_run is True
    assert not (repository / "jam.yaml").exists()
    assert not (repository / "README.md").exists()
    assert any(
        action.operation == "create" and not action.applied for action in report.actions
    )


def test_init_appends_to_existing_readme(
    tmp_path: Path,
) -> None:
    repository = _create_existing_repository(tmp_path)
    readme = repository / "README.md"
    readme.write_text(
        "# Existing Project\n\nCustom documentation.\n",
        encoding="utf-8",
    )

    initialize_repository(
        repository,
        project_name="Existing Project",
        package_name="existing",
        platform_role="Creative Intelligence Engine",
        repository_type="engine",
        scaffold_template="python-engine",
        template_root=Path("templates"),
        include_baseline=True,
    )

    text = readme.read_text(encoding="utf-8")

    assert "Custom documentation." in text
    assert "Built with JAM" in text
    assert "**Platform role:** Creative Intelligence Engine" in text


def test_init_preserves_existing_gitignore(
    tmp_path: Path,
) -> None:
    repository = _create_existing_repository(tmp_path)
    gitignore = repository / ".gitignore"
    gitignore.write_text("custom-entry\n", encoding="utf-8")

    initialize_repository(
        repository,
        project_name="Muse",
        package_name="muse",
        platform_role="Creative Intelligence Engine",
        repository_type="engine",
        scaffold_template="python-engine",
        template_root=Path("templates"),
        include_baseline=True,
    )

    assert gitignore.read_text(encoding="utf-8") == "custom-entry\n"


def test_init_cli_adopts_repository(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    repository = _create_existing_repository(tmp_path)

    exit_code = main(
        [
            "init",
            str(repository),
            "--name",
            "Muse",
            "--package",
            "muse",
            "--role",
            "Creative Intelligence Engine",
            "--type",
            "engine",
            "--baseline",
            "--template-root",
            "templates",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "JAM init:" in captured.out
    assert "PASS" in captured.out


def test_init_cli_dry_run_returns_success(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    repository = _create_existing_repository(tmp_path)

    exit_code = main(
        [
            "init",
            str(repository),
            "--name",
            "Muse",
            "--package",
            "muse",
            "--role",
            "Creative Intelligence Engine",
            "--dry-run",
            "--template-root",
            "templates",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "DRY RUN" in captured.out
    assert not (repository / "jam.yaml").exists()


def _create_existing_monorepo(
    tmp_path: Path,
) -> Path:
    repository = _create_existing_repository(tmp_path)

    for package_path in (
        "packages/atlas-core",
        "packages/atlas-events",
        "apps/restaurantos",
    ):
        package_directory = repository / package_path
        package_directory.mkdir(
            parents=True,
            exist_ok=True,
        )
        (package_directory / "pyproject.toml").write_text(
            """
[project]
name = "atlas-package"
version = "0.1.0"
""".strip()
            + "\n",
            encoding="utf-8",
        )

    return repository


def test_init_adopts_existing_monorepo(
    tmp_path: Path,
) -> None:
    repository = _create_existing_monorepo(tmp_path)

    report = initialize_repository(
        repository,
        project_name="Atlas",
        package_name=None,
        platform_role="Operational Intelligence Engine",
        repository_type="engine",
        scaffold_template="python-engine",
        template_root=Path("templates"),
        python_layout="monorepo",
        package_paths=(
            "packages/atlas-core",
            "packages/atlas-events",
            "apps/restaurantos",
        ),
        include_baseline=True,
    )

    manifest = load_manifest(repository)

    assert report.passed is True
    assert manifest.python.layout == "monorepo"
    assert manifest.python.package is None
    assert manifest.python.packages == (
        "packages/atlas-core",
        "packages/atlas-events",
        "apps/restaurantos",
    )


def test_init_rejects_missing_monorepo_package(
    tmp_path: Path,
) -> None:
    repository = _create_existing_repository(tmp_path)

    with pytest.raises(
        InitError,
        match="missing package manifests",
    ):
        initialize_repository(
            repository,
            project_name="Atlas",
            package_name=None,
            platform_role="Operational Intelligence Engine",
            repository_type="engine",
            scaffold_template="python-engine",
            template_root=Path("templates"),
            python_layout="monorepo",
            package_paths=("packages/missing",),
        )

    assert not (repository / "jam.yaml").exists()


def test_init_cli_adopts_monorepo(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    repository = _create_existing_monorepo(tmp_path)

    exit_code = main(
        [
            "init",
            str(repository),
            "--name",
            "Atlas",
            "--role",
            "Operational Intelligence Engine",
            "--type",
            "engine",
            "--layout",
            "monorepo",
            "--package-path",
            "packages/atlas-core",
            "--package-path",
            "packages/atlas-events",
            "--package-path",
            "apps/restaurantos",
            "--baseline",
            "--template-root",
            "templates",
        ]
    )
    captured = capsys.readouterr()

    manifest = load_manifest(repository)

    assert exit_code == 0
    assert "PASS" in captured.out
    assert manifest.python.layout == "monorepo"
    assert len(manifest.python.packages) == 3
