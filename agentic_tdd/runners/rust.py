"""Rust language runner implementation."""

import re
from pathlib import Path

from ..models.runner import CommandResult, QualityGateResult, TestResult
from ..utils.shell import run_command
from .base import LanguageRunner


class RustRunner(LanguageRunner):
    """Concrete implementation for Rust language support."""

    @property
    def language_name(self) -> str:
        """Return 'Rust'."""
        return "Rust"

    @property
    def file_extensions(self) -> list[str]:
        """Return Rust file extensions."""
        return [".rs", ".toml"]

    def initialize_project(self, path: Path, project_name: str) -> CommandResult:
        """Initialize a new Rust project using cargo.

        Args:
            path: Directory where project should be initialized
            project_name: Name for the Cargo package

        Returns:
            CommandResult with cargo init output
        """
        # Ensure path exists
        path.mkdir(parents=True, exist_ok=True)

        # Run cargo init
        command = ["cargo", "init", "--name", project_name]
        result = run_command(command, cwd=path)

        return result

    def run_tests(self, path: Path) -> TestResult:
        """Execute cargo test and parse results.

        Args:
            path: Project root directory

        Returns:
            TestResult with test execution details

        Parses output like:
            test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
        """
        command = ["cargo", "test", "--color=always"]
        cmd_result = run_command(command, cwd=path, timeout=60)

        # Parse test results from cargo output
        passed_count = 0
        failed_count = 0
        passed = False

        if cmd_result.success:
            # Look for "test result: ok. X passed; Y failed"
            pattern = r"(\d+) passed; (\d+) failed"
            match = re.search(pattern, cmd_result.output)
            if match:
                passed_count = int(match.group(1))
                failed_count = int(match.group(2))
                passed = failed_count == 0
        else:
            # If command failed, still try to extract counts
            pattern = r"(\d+) passed; (\d+) failed"
            match = re.search(pattern, cmd_result.output)
            if match:
                passed_count = int(match.group(1))
                failed_count = int(match.group(2))

        return TestResult(
            passed=passed,
            test_count=passed_count + failed_count,
            failed_count=failed_count,
            passed_count=passed_count,
            output=cmd_result.output,
            duration_seconds=cmd_result.duration_seconds,
        )

    def format_code(self, path: Path) -> QualityGateResult:
        """Format Rust code using cargo fmt.

        Args:
            path: Project root directory

        Returns:
            QualityGateResult indicating if formatting was applied
        """
        # Check if formatting needed
        check_command = ["cargo", "fmt", "--", "--check"]
        check_result = run_command(check_command, cwd=path)

        auto_fixed = False
        if not check_result.success:
            # Formatting needed, apply it
            format_command = ["cargo", "fmt"]
            format_result = run_command(format_command, cwd=path)
            auto_fixed = format_result.success

            return QualityGateResult(
                gate_name="format",
                passed=format_result.success,
                command_result=format_result,
                issues_found=[] if format_result.success else ["Formatting failed"],
                auto_fixed=auto_fixed,
            )

        return QualityGateResult(
            gate_name="format",
            passed=True,
            command_result=check_result,
            issues_found=[],
            auto_fixed=False,
        )

    def lint_code(self, path: Path) -> QualityGateResult:
        """Run cargo clippy with warnings as errors.

        Args:
            path: Project root directory

        Returns:
            QualityGateResult with any lint issues found
        """
        command = ["cargo", "clippy", "--", "-D", "warnings"]
        result = run_command(command, cwd=path, timeout=60)

        issues = []
        if not result.success:
            # Parse clippy output for issues
            # Each issue typically starts with "warning:" or "error:"
            for line in result.output.split("\n"):
                if line.strip().startswith(("warning:", "error:")):
                    issues.append(line.strip())

        return QualityGateResult(
            gate_name="lint",
            passed=result.success,
            command_result=result,
            issues_found=issues,
            auto_fixed=False,
        )

    def build(self, path: Path) -> CommandResult:
        """Build the Rust project using cargo build.

        Args:
            path: Project root directory

        Returns:
            CommandResult with compilation output
        """
        command = ["cargo", "build"]
        return run_command(command, cwd=path, timeout=120)

    def get_test_file_pattern(self) -> str:
        """Return glob pattern for Rust test files.

        Returns:
            Glob pattern string
        """
        return "tests/**/*.rs"

    def get_source_file_pattern(self) -> str:
        """Return glob pattern for Rust source files.

        Returns:
            Glob pattern string
        """
        return "src/**/*.rs"
