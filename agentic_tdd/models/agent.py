"""Agent execution models."""

from datetime import datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    """Agent role identifier."""

    TESTER = "tester"
    IMPLEMENTER = "implementer"
    REFACTORER = "refactorer"
    SUPERVISOR = "supervisor"


class CodebaseFile(BaseModel):
    """Representation of a single file in codebase."""

    path: Path
    content: str
    language: str | None = None


class GitCommitInfo(BaseModel):
    """Information about a git commit."""

    sha: str
    message: str
    author: str
    timestamp: datetime
    files_changed: list[str]


class AgentContext(BaseModel):
    """Context provided to agents for execution."""

    kata_description: str = Field(description="Full kata description text")

    kata_constraints: list[str] = Field(
        default_factory=list, description="List of kata constraint descriptions"
    )

    cycle_number: int = Field(description="Current cycle number")

    codebase_files: list[CodebaseFile] = Field(
        default_factory=list, description="Current codebase files with content"
    )

    recent_commits: list[GitCommitInfo] = Field(
        default_factory=list, description="Last 5 git commits for context"
    )

    last_test_output: str | None = Field(
        default=None, description="Output from most recent test run"
    )

    last_error: str | None = Field(default=None, description="Last error message if agent failed")

    retry_attempt: int = Field(
        default=0, ge=0, description="Current retry attempt number (0 = first attempt)"
    )


class AgentResult(BaseModel):
    """Result from agent execution."""

    role: AgentRole = Field(description="Agent that produced this result")

    success: bool = Field(description="Whether agent completed successfully")

    message: str = Field(description="Human-readable result message")

    files_modified: list[Path] = Field(
        default_factory=list, description="Files created or modified"
    )

    tests_passed: bool | None = Field(
        default=None, description="Whether tests passed after agent action"
    )

    test_output: str | None = Field(default=None, description="Test execution output")

    commits_made: list[str] = Field(default_factory=list, description="Git commit SHAs created")

    overshoot_detected: bool = Field(
        default=False, description="Whether Tester detected premature test passing"
    )

    error_details: str | None = Field(
        default=None, description="Detailed error information if failed"
    )

    duration_seconds: float = Field(description="Execution duration in seconds")
