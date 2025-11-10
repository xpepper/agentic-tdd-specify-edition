"""Abstract base class for language runners."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..models.runner import CommandResult, QualityGateResult, TestResult


class LanguageRunner(ABC):
    """Abstract interface for language-specific operations."""

    @property
    @abstractmethod
    def language_name(self) -> str:
        """Human-readable language name (e.g., 'Rust', 'Python')."""
        pass

    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """File extensions for this language (e.g., ['.rs', '.toml'])."""
        pass

    @abstractmethod
    def initialize_project(self, path: Path, project_name: str) -> CommandResult:
        """Initialize a new project in the given directory.

        Args:
            path: Directory where project should be initialized
            project_name: Name for the project/package

        Returns:
            CommandResult with initialization command output

        Example (Rust):
            cargo init --name kata_name

        Example (Python):
            poetry init --name kata_name --no-interaction
            Create src/ and tests/ directories
        """
        pass

    @abstractmethod
    def run_tests(self, path: Path) -> TestResult:
        """Execute test suite and parse results.

        Args:
            path: Project root directory

        Returns:
            TestResult with pass/fail status and test counts

        Example (Rust):
            cargo test --color=always
            Parse output for "test result: ok. 3 passed; 0 failed"

        Example (Python):
            pytest --verbose --tb=short
            Parse output for test counts
        """
        pass

    @abstractmethod
    def format_code(self, path: Path) -> QualityGateResult:
        """Format code according to language conventions.

        Args:
            path: Project root directory

        Returns:
            QualityGateResult with auto_fixed=True if formatting applied

        Example (Rust):
            cargo fmt

        Example (Python):
            black .
            isort .
        """
        pass

    @abstractmethod
    def lint_code(self, path: Path) -> QualityGateResult:
        """Run linter and report issues.

        Args:
            path: Project root directory

        Returns:
            QualityGateResult with issues_found list

        Example (Rust):
            cargo clippy -- -D warnings

        Example (Python):
            ruff check .
        """
        pass

    @abstractmethod
    def build(self, path: Path) -> CommandResult:
        """Build/compile the project.

        Args:
            path: Project root directory

        Returns:
            CommandResult with compilation output

        Example (Rust):
            cargo build

        Example (Python):
            python -m py_compile src/**/*.py  # Optional for Python
        """
        pass

    @abstractmethod
    def get_test_file_pattern(self) -> str:
        """Return glob pattern for test files.

        Returns:
            Glob pattern string

        Example (Rust): "tests/**/*.rs"
        Example (Python): "tests/**/test_*.py"
        """
        pass

    @abstractmethod
    def get_source_file_pattern(self) -> str:
        """Return glob pattern for source files.

        Returns:
            Glob pattern string

        Example (Rust): "src/**/*.rs"
        Example (Python): "src/**/*.py"
        """
        pass
