"""Implementer agent implementation."""

import re
import time
from pathlib import Path

from langchain_openai import ChatOpenAI

from ..llm.prompts import get_system_prompt
from ..models.agent import AgentContext, AgentResult, AgentRole
from ..models.runner import TestResult
from ..runners import LanguageRunner
from ..utils.git import GitOperations
from .base import Agent, AgentExecutionError, QualityGateError


class ImplementerAgent(Agent):
    """Agent responsible for implementing code to pass tests."""

    def __init__(self, llm: ChatOpenAI, work_dir: Path, runner: LanguageRunner):
        """Initialize ImplementerAgent.

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
        """Return IMPLEMENTER role."""
        return AgentRole.IMPLEMENTER

    def get_system_prompt(self) -> str:
        """Return implementer system prompt."""
        return get_system_prompt(AgentRole.IMPLEMENTER)

    def execute(self, context: AgentContext) -> AgentResult:
        """Implement code to pass test and commit.

        Args:
            context: Agent execution context

        Returns:
            AgentResult with implementation results

        Raises:
            AgentExecutionError: If implementation fails unrecoverably
        """
        start_time = time.time()

        try:
            # Get implementation code from LLM
            llm_response = self._run_llm(context)

            # Parse response to extract code changes
            file_changes = self._parse_implementation_response(llm_response)

            # Apply code changes
            modified_files = []
            for file_path, code_content in file_changes.items():
                full_path = self.work_dir / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(code_content)
                modified_files.append(Path(file_path))

            # Run tests to verify GREEN state
            test_result = self.runner.run_tests(self.work_dir)

            if not test_result.passed:
                duration = time.time() - start_time
                return AgentResult(
                    role=self.role,
                    success=False,
                    message="Tests still failing after implementation",
                    files_modified=modified_files,
                    tests_passed=False,
                    test_output=test_result.output,
                    error_details="Implementation did not make tests pass",
                    duration_seconds=duration,
                )

            # Run quality gates
            self._run_quality_gates()

            # Stage all changes (test + implementation)
            self.git.add([self.work_dir / f for f in modified_files])

            # Get staged files for commit message
            status = self.git.get_status()
            staged_files = status.get("staged", [])

            # Commit changes
            commit_message = self._generate_commit_message(staged_files, test_result)
            commit_sha = self.git.commit(commit_message)

            duration = time.time() - start_time

            return AgentResult(
                role=self.role,
                success=True,
                message=f"Implementation complete: {commit_message}",
                files_modified=modified_files,
                tests_passed=True,
                test_output=test_result.output,
                commits_made=[commit_sha],
                duration_seconds=duration,
            )

        except QualityGateError as e:
            duration = time.time() - start_time
            return AgentResult(
                role=self.role,
                success=False,
                message=f"Quality gate failed: {str(e)}",
                error_details=str(e),
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            return AgentResult(
                role=self.role,
                success=False,
                message=f"Implementation failed: {str(e)}",
                error_details=str(e),
                duration_seconds=duration,
            )

    def _build_user_prompt(self, context: AgentContext) -> str:
        """Build user prompt for implementation.

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

        if context.last_test_output:
            prompt_parts.extend(
                [
                    "# Test Failure Output",
                    "```",
                    context.last_test_output,
                    "```",
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
                "Write MINIMAL code to make the failing test pass.",
                "Do not add features not required by the test.",
                "",
                "Respond with file changes in this format:",
                "FILE: path/to/file.ext",
                "```",
                "... complete file content ...",
                "```",
                "",
                "FILE: path/to/another_file.ext",
                "```",
                "... complete file content ...",
                "```",
            ]
        )

        return "\n".join(prompt_parts)

    def _parse_implementation_response(self, response: str) -> dict[str, str]:
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

    def _generate_commit_message(self, staged_files: list[str], test_result: TestResult) -> str:
        """Generate commit message for test + implementation.

        Args:
            staged_files: List of staged file paths
            test_result: Test result with pass/fail info

        Returns:
            Commit message string
        """
        files_str = ", ".join(staged_files[:3])
        if len(staged_files) > 3:
            files_str += f" and {len(staged_files) - 3} more"

        tests_info = f"{test_result.passed_count} tests passing"

        return f"feat: Implement behavior with passing tests\n\n{files_str}\n{tests_info}"
