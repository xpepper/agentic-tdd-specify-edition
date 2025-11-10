"""Python entry point for agentic-tdd package.

This allows the tool to be invoked as:
    python -m agentic_tdd
"""

from .cli import app


def main() -> None:
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
