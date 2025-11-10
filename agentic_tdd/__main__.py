"""Python entry point for agentic-tdd package.

This allows the tool to be invoked as:
    python -m agentic_tdd
"""

import sys


def main() -> None:
    """Main entry point for CLI."""
    # Import here to avoid circular imports and ensure clean startup
    from .cli import app

    # Call with explicit prog_name to ensure consistent behavior
    app(prog_name="agentic-tdd")


if __name__ == "__main__":
    main()
