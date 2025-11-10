"""Refactorer agent implementation."""

import re
import time
from pathlib import Path

from langchain_openai import ChatOpenAI

from ..llm.prompts import get_system_prompt
from ..models.agent import AgentContext, AgentResult, AgentRole
from ..runners import LanguageRunner
from ..utils.git import GitOperations
from .base import Agent, AgentExecutionError, QualityGateError


class RefactorerAgent(Agent):
    """Agent responsible for refactoring code while maintaining tests."""

    def __init__(self, llm: ChatOpenAI, work_dir: Path, runner: LanguageRunner):
        """Initialize RefactorerAgent.

        Args:
            llm: Configured LangChain LLM instance
            work_dir: Working directory for kata implementation
            runner: Language runner for executing tests
        """
        super().__init__(llm, work_dir)
        self.runner = runner
        self.git = GitOperations(work_dir)

    @property
    def role(self) -> AgentRole:
        """Return REFACTORER role."""
        return AgentRole.REFACTORER

    def get_system_prompt(self) -> str:
        """Return refactorer system prompt."""
        return get_system_prompt(AgentRole.REFACTORER)

    def execute(self, context: AgentContext) -> AgentResult:
        """Refactor code while maintaining GREEN state.

        Args:
            context: Agent execution context

        Returns:
            AgentResult with refactoring results

        Raises:
            AgentExecutionError: If refactoring fails unrecoverably
        """
        start_time = time.time()

        try:
            # Get last commit SHA before refactoring (for revert if needed)
            last_commit = self.git.get_last_commit_sha()

            # Get refactoring from LLM
            llm_response = self._run_llm(context)

            # Check if LLM indicates no refactoring needed
            if self._is_no_changes_response(llm_response):
                duration = time.time() - start_time
                return AgentResult(
                    role=self.role,
                    success=True,
                    message="No refactoring needed",
                    tests_passed=True,
                    duration_seconds=duration,
                )

            # Parse response to extract code changes
            file_changes = self._parse_refactoring_response(llm_response)

            # Apply code changes
            modified_files = []
            for file_path, code_content in file_changes.items():
                full_path = self.work_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(code_content)
                modified_files.append(Path(file_path))

            # Run tests to verify still GREEN
            test_result = self.runner.run_tests(self.work_dir)

            if not test_result.passed:
                # Revert changes
                if last_commit:
                    self.git.revert_to_commit(last_commit)

                duration = time.time() - start_time
                return AgentResult(
                    role=self.role,
                    success=False,
                    message="Refactoring broke tests, reverted",
                    files_modified=modified_files,
                    tests_passed=False,
                    test_output=test_result.output,
                    error_details="Tests failed after refactoring",
                    duration_seconds=duration,
                )

            # Run quality gates
            try:
                self._run_quality_gates()
            except QualityGateError as e:
                # Revert changes
                if last_commit:
                    self.git.revert_to_commit(last_commit)

                duration = time.time() - start_time
                return AgentResult(
                    role=self.role,
                    success=False,
                    message=f"Quality gate failed after refactoring: {str(e)}",
                    error_details=str(e),
                    duration_seconds=duration,
                )

            # Stage changes
            self.git.add([self.work_dir / f for f in modified_files])

            # Commit refactoring
            commit_message = self._generate_commit_message(file_changes)
            commit_sha = self.git.commit(commit_message)

            duration = time.time() - start_time

            return AgentResult(
                role=self.role,
                success=True,
                message=f"Refactoring complete: {commit_message}",
                files_modified=modified_files,
                tests_passed=True,
                test_output=test_result.output,
                commits_made=[commit_sha],
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            return AgentResult(
                role=self.role,
                success=False,
                message=f"Refactoring failed: {str(e)}",
                error_details=str(e),
                duration_seconds=duration,
            )

    def _build_user_prompt(self, context: AgentContext) -> str:
        """Build user prompt for refactoring.

        Args:
            context: Agent execution context

        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            "# Kata Description",
            context.kata_description,
            "",
        ]

        if context.kata_constraints:
            prompt_parts.extend(
                [
                    "# Kata Constraints",
                    "\n".join(f"- {c}" for c in context.kata_constraints),
                    "",
                ]
            )

        prompt_parts.extend(
            [
                "# Current Cycle",
                f"Cycle {context.cycle_number}",
                "",
            ]
        )

        if context.recent_commits:
            prompt_parts.extend(
                [
                    "# Recent Commits",
                    "\n".join(
                        f"- {commit.sha[:7]}: {commit.message}" for commit in context.recent_commits
                    ),
                    "",
                ]
            )

        if context.codebase_files:
            prompt_parts.extend(["# Current Codebase", ""])
            for file in context.codebase_files:
                prompt_parts.extend(
                    [
                        f"## {file.path}",
                        "```",
                        file.content,
                        "```",
                        "",
                    ]
                )

        if context.last_error:
            prompt_parts.extend(
                [
                    "# Previous Error (Retry)",
                    context.last_error,
                    "",
                ]
            )

        prompt_parts.extend(
            [
                "# Your Task",
                "Identify ONE quality improvement opportunity and refactor the code.",
                "Maintain all tests passing (GREEN state).",
                "",
                "**CRITICAL**: You MUST preserve ALL existing tests and code functionality.",
                "Do NOT remove, modify test behavior, or replace any existing tests.",
                "Only improve code quality (naming, structure, duplication) without changing behavior.",
                "",
                "If no improvements are needed, respond with: NO_CHANGES_NEEDED",
                "",
                "Otherwise, respond with file changes in this format:",
                "FILE: path/to/file.ext",
                "```",
                "... COMPLETE file content with ALL existing code + your improvements ...",
                "```",
                "",
                "FILE: path/to/another_file.ext",
                "```",
                "... COMPLETE file content with ALL existing code + your improvements ...",
                "```",
            ]
        )

        return "\n".join(prompt_parts)

    def _parse_refactoring_response(self, response: str) -> dict[str, str]:
        """Parse LLM response to extract file changes.

        Args:
            response: LLM response text

        Returns:
            Dictionary mapping file paths to code content

        Raises:
            AgentExecutionError: If response cannot be parsed
        """
        file_changes: dict[str, str] = {}

        # Find all FILE: markers followed by code blocks
        pattern = r"FILE:\s*(.+?)\n```(?:\w+)?\n(.*?)\n```"
        matches = re.finditer(pattern, response, re.DOTALL)

        for match in matches:
            file_path = match.group(1).strip()
            code_content = match.group(2)
            file_changes[file_path] = code_content

        if not file_changes:
            raise AgentExecutionError("Could not find any file changes in response")

        return file_changes

    def _is_no_changes_response(self, response: str) -> bool:
        """Check if LLM indicated no changes needed.

        Args:
            response: LLM response text

        Returns:
            True if no changes needed
        """
        return "NO_CHANGES_NEEDED" in response.upper()

    def _run_quality_gates(self) -> None:
        """Run quality gates (format, lint, build).

        Raises:
            QualityGateError: If any quality gate fails
        """
        # Format code
        format_result = self.runner.format_code(self.work_dir)
        if not format_result.passed:
            raise QualityGateError(f"Format failed: {format_result.command_result.output}")

        # Re-run tests if formatting made changes
        if format_result.auto_fixed:
            test_result = self.runner.run_tests(self.work_dir)
            if not test_result.passed:
                raise QualityGateError("Tests failed after formatting")

        # Lint code
        lint_result = self.runner.lint_code(self.work_dir)
        if not lint_result.passed:
            issues = "\n".join(lint_result.issues_found)
            raise QualityGateError(f"Lint failed:\n{issues}")

        # Build
        build_result = self.runner.build(self.work_dir)
        if not build_result.success:
            raise QualityGateError(f"Build failed: {build_result.output}")

    def _generate_commit_message(self, file_changes: dict[str, str]) -> str:
        """Generate commit message for refactoring.

        Args:
            file_changes: Dictionary of file paths to content

        Returns:
            Commit message string
        """
        files = list(file_changes.keys())
        files_str = ", ".join(files[:2])
        if len(files) > 2:
            files_str += f" and {len(files) - 2} more"

        return f"refactor: Improve code quality\n\nRefactored: {files_str}"
