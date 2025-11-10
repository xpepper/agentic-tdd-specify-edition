"""Abstract base class for TDD agents."""

from abc import ABC, abstractmethod
from pathlib import Path

from langchain.schema import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..models.agent import AgentContext, AgentResult, AgentRole


class Agent(ABC):
    """Base class for all TDD agents."""

    def __init__(self, llm: ChatOpenAI, work_dir: Path):
        """Initialize agent.

        Args:
            llm: Configured LangChain LLM instance
            work_dir: Working directory for kata implementation
        """
        self.llm = llm
        self.work_dir = work_dir

    @property
    @abstractmethod
    def role(self) -> AgentRole:
        """Return agent's role identifier."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return role-specific system prompt for LLM.

        Returns:
            System prompt string with role instructions
        """
        pass

    @abstractmethod
    def execute(self, context: AgentContext) -> AgentResult:
        """Execute agent's primary task.

        Args:
            context: Agent execution context (codebase, git history, kata description)

        Returns:
            AgentResult with success status, modified files, commits, etc.

        Raises:
            AgentExecutionError: If agent encounters unrecoverable error
        """
        pass

    @abstractmethod
    def _build_user_prompt(self, context: AgentContext) -> str:
        """Build user prompt from context.

        Args:
            context: Agent execution context

        Returns:
            Formatted prompt string with context details
        """
        pass

    def _run_llm(self, context: AgentContext) -> str:
        """Internal: Run LLM with system prompt and context.

        Args:
            context: Agent execution context

        Returns:
            LLM response text
        """
        system_prompt = self.get_system_prompt()
        user_prompt = self._build_user_prompt(context)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = self.llm.invoke(messages)
        # Ensure content is always a string
        content = response.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # If content is a list, join the elements
            return " ".join(str(item) for item in content)
        else:
            return str(content)


class AgentError(Exception):
    """Base exception for agent errors."""

    pass


class AgentExecutionError(AgentError):
    """Agent execution failed unrecoverably."""

    pass


class AgentTimeoutError(AgentError):
    """Agent execution exceeded timeout."""

    pass


class QualityGateError(AgentError):
    """Quality gate check failed."""

    pass
