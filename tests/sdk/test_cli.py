from pathlib import Path

from _pytest.capture import CaptureFixture
from jam_sdk.cli import build_parser, main


def test_parser_accepts_new_command(tmp_path: Path) -> None:
    args = build_parser().parse_args(
        [
            "new",
            "Muse Demo",
            "--package",
            "muse_demo",
            "--role",
            "Creative Intelligence Engine",
            "--destination",
            str(tmp_path / "muse-demo"),
        ]
    )

    assert args.command == "new"
    assert args.project_name == "Muse Demo"
    assert args.package_name == "muse_demo"
    assert args.platform_role == "Creative Intelligence Engine"


def test_main_creates_repository(tmp_path: Path) -> None:
    destination = tmp_path / "muse-demo"

    exit_code = main(
        [
            "new",
            "Muse Demo",
            "--package",
            "muse_demo",
            "--role",
            "Creative Intelligence Engine",
            "--destination",
            str(destination),
            "--template-root",
            "templates",
        ]
    )

    assert exit_code == 0
    assert (destination / "README.md").is_file()
    assert (destination / "src/muse_demo/__init__.py").is_file()


def test_main_returns_error_for_invalid_package(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    exit_code = main(
        [
            "new",
            "Invalid Demo",
            "--package",
            "not-valid",
            "--role",
            "Test Engine",
            "--destination",
            str(tmp_path / "invalid"),
            "--template-root",
            "templates",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "valid Python identifier" in captured.out


def test_main_returns_error_for_nonempty_destination(
    tmp_path: Path,
    capsys: CaptureFixture[str],
) -> None:
    destination = tmp_path / "existing"
    destination.mkdir()
    (destination / "existing.txt").write_text(
        "existing",
        encoding="utf-8",
    )

    exit_code = main(
        [
            "new",
            "Existing Demo",
            "--package",
            "existing_demo",
            "--role",
            "Test Engine",
            "--destination",
            str(destination),
            "--template-root",
            "templates",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Destination is not empty" in captured.out
