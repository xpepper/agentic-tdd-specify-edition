"""Supervisor agent implementation."""

import logging
import re
from pathlib import Path

from ..models.agent import AgentContext, AgentResult, CodebaseFile
from ..models.config import ToolConfig
from ..models.cycle import CycleState, SessionState, TDDPhase
from ..models.kata import KataDescription
from ..runners import LanguageRunner
from ..utils.git import GitOperations
from .implementer import ImplementerAgent
from .refactorer import RefactorerAgent
from .tester import TesterAgent

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """Orchestrates TDD cycles and handles failures."""

    def __init__(
        self,
        tester: TesterAgent,
        implementer: ImplementerAgent,
        refactorer: RefactorerAgent,
        runner: LanguageRunner,
        config: ToolConfig,
        kata: KataDescription,
    ):
        """Initialize SupervisorAgent.

        Args:
            tester: Tester agent instance
            implementer: Implementer agent instance
            refactorer: Refactorer agent instance
            runner: Language runner for executing commands
            config: Tool configuration
            kata: Kata description
        """
        self.tester = tester
        self.implementer = implementer
        self.refactorer = refactorer
        self.runner = runner
        self.config = config
        self.kata = kata
        self.git = GitOperations(config.work_dir)
        self.session_state = SessionState(kata=kata, work_dir=config.work_dir)

    def run_session(self) -> SessionState:
        """Execute complete TDD session.

        Returns:
            SessionState with complete cycle history
        """
        logger.info(f"Starting TDD session for kata: {self.kata.title}")
        logger.info(f"Working directory: {self.config.work_dir}")
        logger.info(f"Max cycles: {self.config.max_cycles}")

        # Initialize project and git repository
        self._initialize_session()

        # Run TDD cycles until completion or max cycles reached
        while self.session_state.current_cycle <= self.config.max_cycles:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Starting Cycle {self.session_state.current_cycle}")
            logger.info(f"{'=' * 60}")

            cycle_state = self.run_cycle()

            if cycle_state.phase == TDDPhase.FAILED:
                logger.error(f"Cycle {cycle_state.cycle_num} failed: {cycle_state.errors}")
                logger.info("Aborting session due to cycle failure")
                break

            if cycle_state.phase == TDDPhase.COMPLETE:
                logger.info(f"Cycle {cycle_state.cycle_num} completed successfully")
                self.session_state.advance_cycle()

        # Finalize session
        from datetime import UTC, datetime

        self.session_state.completed_at = datetime.now(UTC)
        logger.info("\n" + "=" * 60)
        logger.info("TDD Session Complete")
        logger.info(f"Total cycles: {len(self.session_state.cycles)}")
        logger.info(f"Total commits: {self.session_state.total_commits}")
        logger.info("=" * 60)

        return self.session_state

    def run_cycle(self) -> CycleState:
        """Execute single TDD cycle.

        Returns:
            CycleState with cycle results
        """
        cycle_state = self.session_state.get_current_cycle_state()

        try:
            # Phase 1: Tester - Write failing test
            cycle_state.phase = TDDPhase.TESTING
            logger.info("Phase 1: Tester - Writing failing test...")
            tester_result = self._execute_tester(cycle_state)

            if tester_result.overshoot_detected:
                logger.warning("Overshoot detected!")
                return self._handle_tester_overshoot(cycle_state, tester_result)

            if not tester_result.success:
                error_msg = f"Tester failed: {tester_result.message}"
                logger.error(error_msg)
                cycle_state.mark_failed(error_msg)
                return cycle_state

            # Update cycle state with test file
            if tester_result.files_modified:
                cycle_state.test_file_path = tester_result.files_modified[0]

            # Phase 2: Implementer - Make test pass
            cycle_state.phase = TDDPhase.IMPLEMENTING
            logger.info("Phase 2: Implementer - Making test pass...")
            impl_result = self._execute_with_retry(
                self.implementer, cycle_state, max_attempts=self.config.max_retries
            )

            if not impl_result.success:
                return self._handle_implementer_failure(cycle_state, impl_result)

            # Update cycle state with implementation files and commits
            cycle_state.implementation_files.extend(impl_result.files_modified)
            cycle_state.commits.extend(impl_result.commits_made)
            self.session_state.total_commits += len(impl_result.commits_made)

            # Phase 3: Refactorer - Improve code quality
            cycle_state.phase = TDDPhase.REFACTORING
            logger.info("Phase 3: Refactorer - Improving code quality...")
            refactor_result = self._execute_with_retry(
                self.refactorer, cycle_state, max_attempts=self.config.max_retries
            )

            # Refactorer failure is non-fatal (revert and proceed)
            if not refactor_result.success:
                logger.warning(
                    f"Refactorer failed after {self.config.max_retries} attempts, "
                    "skipping refactoring"
                )
                # Revert handled by refactorer itself
            else:
                # Update cycle state with refactoring commits
                cycle_state.commits.extend(refactor_result.commits_made)
                self.session_state.total_commits += len(refactor_result.commits_made)

            # Mark cycle complete
            cycle_state.mark_complete()
            logger.info(f"✓ Cycle {cycle_state.cycle_num} completed successfully")

            return cycle_state

        except Exception as e:
            error_msg = f"Unexpected error in cycle: {str(e)}"
            logger.error(error_msg)
            cycle_state.mark_failed(error_msg)
            return cycle_state

    def _initialize_session(self) -> None:
        """Initialize project structure and git repository."""
        logger.info("Initializing session...")

        # Initialize git repository if not exists
        if not (self.config.work_dir / ".git").exists():
            logger.info("Initializing git repository...")
            self.git.init()

        # Initialize project structure using language runner
        logger.info(f"Initializing {self.config.language} project...")
        # Use kata title as project name, normalized for file system
        # Remove markdown syntax and special characters
        project_name = re.sub(
            r"\[([^\]]+)\]\([^)]+\)", r"\1", self.kata.title
        )  # Remove markdown links
        project_name = re.sub(
            r"[^a-zA-Z0-9_-]+", "_", project_name.lower()
        )  # Keep only alphanumeric, underscore, hyphen
        project_name = project_name.strip("_")  # Remove leading/trailing underscores
        init_result = self.runner.initialize_project(self.config.work_dir, project_name)
        if not init_result.success:
            raise RuntimeError(f"Failed to initialize project: {init_result.output}")

        logger.info("Session initialized successfully")

    def _execute_tester(self, cycle_state: CycleState) -> AgentResult:
        """Execute tester agent.

        Args:
            cycle_state: Current cycle state

        Returns:
            AgentResult from tester execution
        """
        context = self._build_context(cycle_state)
        return self.tester.execute(context)

    def _execute_with_retry(
        self,
        agent: TesterAgent | ImplementerAgent | RefactorerAgent,
        cycle_state: CycleState,
        max_attempts: int,
    ) -> AgentResult:
        """Execute agent with retry logic.

        Args:
            agent: Agent to execute
            cycle_state: Current cycle state
            max_attempts: Maximum retry attempts

        Returns:
            AgentResult from successful execution or final attempt
        """
        result: AgentResult | None = None
        for attempt in range(max_attempts):
            context = self._build_context(cycle_state, retry_attempt=attempt)

            logger.info(f"Attempt {attempt + 1}/{max_attempts}")
            result = agent.execute(context)

            if result.success:
                return result

            logger.warning(f"Attempt {attempt + 1} failed: {result.message}")
            if attempt < max_attempts - 1:
                logger.info("Retrying...")

        # Result must be set after loop
        assert result is not None
        return result

    def _build_context(
        self, cycle_state: CycleState, retry_attempt: int = 0, last_error: str | None = None
    ) -> AgentContext:
        """Build agent execution context.

        Args:
            cycle_state: Current cycle state
            retry_attempt: Current retry attempt number
            last_error: Last error message if retrying

        Returns:
            AgentContext for agent execution
        """
        # Read codebase files
        codebase_files: list[CodebaseFile] = []
        for file_path in self.config.work_dir.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                try:
                    content = file_path.read_text()
                    relative_path = file_path.relative_to(self.config.work_dir)
                    codebase_files.append(
                        CodebaseFile(
                            path=relative_path, content=content, language=self.config.language
                        )
                    )
                except Exception as e:
                    logger.warning(f"Could not read file {file_path}: {e}")

        # Get recent commits
        recent_commits = self.git.get_recent_commits(limit=5)

        # Get last test output if available
        last_test_output: str | None = None
        if self.git.get_last_commit_sha():
            test_result = self.runner.run_tests(self.config.work_dir)
            last_test_output = test_result.output

        # Build kata constraints list
        kata_constraints = [c.description for c in self.kata.constraints]

        return AgentContext(
            kata_description=self.kata.description,
            kata_constraints=kata_constraints,
            cycle_number=cycle_state.cycle_num,
            codebase_files=codebase_files,
            recent_commits=recent_commits,
            last_test_output=last_test_output,
            last_error=last_error,
            retry_attempt=retry_attempt,
        )

    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored from codebase context.

        Args:
            file_path: File path to check

        Returns:
            True if file should be ignored
        """
        # Ignore git directory, build artifacts, etc.
        ignore_patterns = [
            ".git",
            "target",  # Rust build directory
            "__pycache__",  # Python cache
            ".pytest_cache",
            "node_modules",
            ".DS_Store",
        ]

        parts = file_path.relative_to(self.config.work_dir).parts
        return any(pattern in parts for pattern in ignore_patterns)

    def _handle_tester_overshoot(self, cycle_state: CycleState, result: AgentResult) -> CycleState:
        """Handle test passing immediately (overshoot).

        Args:
            cycle_state: Current cycle state
            result: Tester result with overshoot

        Returns:
            Updated cycle state
        """
        logger.warning("Test passed immediately - overshoot detected")
        logger.info("This suggests the implementation already covers this behavior")

        # Mark as failed - supervisor should request different test or consider kata complete
        error_msg = f"Overshoot: {result.message}"
        cycle_state.mark_failed(error_msg)

        return cycle_state

    def _handle_implementer_failure(
        self, cycle_state: CycleState, result: AgentResult
    ) -> CycleState:
        """Handle implementer unable to pass test.

        Args:
            cycle_state: Current cycle state
            result: Implementer result

        Returns:
            Updated cycle state
        """
        error_msg = f"Implementer failed after {self.config.max_retries} attempts: {result.message}"
        logger.error(error_msg)

        # This is a critical failure - cannot proceed with cycle
        cycle_state.mark_failed(error_msg)

        return cycle_state
