"""Command-line interface for the JAM SDK."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Final

from jam_sdk.scaffold import (
    ScaffoldError,
    ScaffoldRequest,
    scaffold_python_engine,
)
from jam_sdk.validate import (
    format_validation_report,
    validate_repository,
)

DEFAULT_TEMPLATE_ROOT: Final[Path] = Path(__file__).resolve().parents[3] / "templates"


def build_parser() -> argparse.ArgumentParser:
    """Build the JAM command-line parser."""

    parser = argparse.ArgumentParser(
        prog="jam",
        description="Create JAM-conformant BarelySmash repositories.",
    )

    subcommands = parser.add_subparsers(
        dest="command",
        required=True,
    )

    new_parser = subcommands.add_parser(
        "new",
        help="Create a repository from a JAM template.",
    )
    new_parser.add_argument(
        "project_name",
        help="Human-readable project name.",
    )
    new_parser.add_argument(
        "--package",
        required=True,
        dest="package_name",
        help="Lowercase Python package name.",
    )
    new_parser.add_argument(
        "--role",
        required=True,
        dest="platform_role",
        help="Platform role, such as Creative Intelligence Engine.",
    )
    new_parser.add_argument(
        "--destination",
        required=True,
        type=Path,
        help="Directory where the repository will be created.",
    )
    new_parser.add_argument(
        "--template-root",
        type=Path,
        default=DEFAULT_TEMPLATE_ROOT,
        help=argparse.SUPPRESS,
    )

    validate_parser = subcommands.add_parser(
        "validate",
        help="Validate a repository against JAM requirements.",
    )
    validate_parser.add_argument(
        "repository",
        nargs="?",
        type=Path,
        default=Path.cwd(),
        help="Repository to validate. Defaults to the current directory.",
    )
    validate_parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Emit machine-readable JSON.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the JAM command-line interface."""

    args = build_parser().parse_args(argv)

    if args.command == "validate":
        report = validate_repository(args.repository)
        output = (
            report.to_json() if args.json_output else format_validation_report(report)
        )
        print(output)
        return 0 if report.passed else 1

    if args.command != "new":
        return 2

    try:
        destination = scaffold_python_engine(
            ScaffoldRequest(
                project_name=args.project_name,
                package_name=args.package_name,
                platform_role=args.platform_role,
                destination=args.destination,
            ),
            template_root=args.template_root,
        )
    except ScaffoldError as exc:
        print(f"error: {exc}")
        return 1

    print(f"Created JAM repository at {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
