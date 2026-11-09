"""Print a greeting, optionally addressed to a name."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

DEFAULT_NAME = "ai-devkit-pilot2"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse the command-line arguments for the greeting script."""
    parser = argparse.ArgumentParser(
        description="Print a greeting.",
        allow_abbrev=False,
    )
    parser.add_argument(
        "--name",
        metavar="NAME",
        default=DEFAULT_NAME,
        help=f"name to greet (default: {DEFAULT_NAME})",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    """Print the greeting selected by the command line."""
    args = parse_args(argv)
    print(f"Hello from {args.name}!")


if __name__ == "__main__":
    main()
