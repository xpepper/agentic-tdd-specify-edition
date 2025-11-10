"""Tester agent implementation."""

import re
import time
from pathlib import Path

from langchain_openai import ChatOpenAI

from ..llm.prompts import get_system_prompt
from ..models.agent import AgentContext, AgentResult, AgentRole
from ..runners import LanguageRunner
from ..utils.git import GitOperations
from .base import Agent, AgentExecutionError


class TesterAgent(Agent):
    """Agent responsible for writing failing tests."""

    def __init__(self, llm: ChatOpenAI, work_dir: Path, runner: LanguageRunner):
        """Initialize TesterAgent.

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
        """Return TESTER role."""
        return AgentRole.TESTER

    def get_system_prompt(self) -> str:
        """Return tester system prompt."""
        return get_system_prompt(AgentRole.TESTER)

    def execute(self, context: AgentContext) -> AgentResult:
        """Write and stage a failing test.

        Args:
            context: Agent execution context

        Returns:
            AgentResult with test creation results

        Raises:
            AgentExecutionError: If test creation fails unrecoverably
        """
        start_time = time.time()

        try:
            # Get test code from LLM
            llm_response = self._run_llm(context)

            # Parse the response to extract test code and file path
            test_code, test_file_path = self._parse_test_response(llm_response)

            # Write test file
            full_path = self.work_dir / test_file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(test_code)

            # Run tests to verify RED state
            test_result = self.runner.run_tests(self.work_dir)

            # Check for overshoot (test passes unexpectedly)
            overshoot_detected = test_result.passed

            # Stage the test file
            if not overshoot_detected:
                self.git.add([full_path])

            duration = time.time() - start_time

            return AgentResult(
                role=self.role,
                success=not overshoot_detected,
                message=f"Test written: {test_file_path}"
                if not overshoot_detected
                else "Overshoot detected: Test passed unexpectedly",
                files_modified=[Path(test_file_path)],
                tests_passed=test_result.passed,
                test_output=test_result.output,
                overshoot_detected=overshoot_detected,
                duration_seconds=duration,
            )

        except Exception as e:
            duration = time.time() - start_time
            return AgentResult(
                role=self.role,
                success=False,
                message=f"Test creation failed: {str(e)}",
                error_details=str(e),
                duration_seconds=duration,
            )

    def _build_user_prompt(self, context: AgentContext) -> str:
        """Build user prompt for test generation.

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

        if context.last_test_output:
            prompt_parts.extend(
                [
                    "# Last Test Output",
                    "```",
                    context.last_test_output,
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
                "Write ONE small, focused test for the next untested behavior.",
                "The test should be minimal and fail when run (RED state).",
                "",
                "**CRITICAL**: You MUST include ALL existing tests and code in your response.",
                "Do NOT remove or replace any existing tests or functions.",
                "Only ADD the new test to the existing file content.",
                "",
                "Respond with the COMPLETE file content including:",
                "FILE_PATH: path/to/test_file.ext",
                "TEST_CODE:",
                "```",
                "... COMPLETE file with all existing tests/code + your new test ...",
                "```",
            ]
        )

        return "\n".join(prompt_parts)

    def _parse_test_response(self, response: str) -> tuple[str, str]:
        """Parse LLM response to extract test code and file path.

        Args:
            response: LLM response text

        Returns:
            Tuple of (test_code, file_path)

        Raises:
            AgentExecutionError: If response cannot be parsed
        """
        # Extract file path
        file_path_match = re.search(r"FILE_PATH:\s*(.+)", response)
        if not file_path_match:
            raise AgentExecutionError("Could not find FILE_PATH in response")

        file_path = file_path_match.group(1).strip()

        # Extract code block
        code_match = re.search(r"```(?:\w+)?\n(.*?)\n```", response, re.DOTALL)
        if not code_match:
            raise AgentExecutionError("Could not find code block in response")

        test_code = code_match.group(1)

        return test_code, file_path
