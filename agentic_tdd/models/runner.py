"""Language runner models."""

from typing import Literal

from pydantic import BaseModel, Field


class TestResult(BaseModel):
    """Result from running test suite."""

    passed: bool = Field(description="Whether all tests passed")

    test_count: int = Field(ge=0, description="Total number of tests run")

    passed_count: int = Field(ge=0, description="Number of tests passed")

    failed_count: int = Field(ge=0, description="Number of tests failed")

    output: str = Field(description="Raw test execution output")

    duration_seconds: float = Field(description="Test execution duration")

    error_message: str | None = Field(
        default=None, description="Error message if tests failed to run"
    )


class CommandResult(BaseModel):
    """Result from shell command execution."""

    command: list[str] = Field(description="Command that was executed")

    exit_code: int = Field(description="Process exit code")

    output: str = Field(description="Combined stdout and stderr")

    success: bool = Field(description="Whether command succeeded (exit code 0)")

    duration_seconds: float = Field(description="Execution duration")

    timed_out: bool = Field(default=False, description="Whether command exceeded timeout")


class QualityGateResult(BaseModel):
    """Result from running quality gates."""

    gate_name: Literal["format", "lint", "type_check", "build"] = Field(
        description="Quality gate identifier"
    )

    passed: bool = Field(description="Whether gate passed")

    command_result: CommandResult = Field(description="Underlying command result")

    auto_fixed: bool = Field(
        default=False,
        description="Whether issues were automatically fixed (e.g., formatting)",
    )

    issues_found: list[str] = Field(
        default_factory=list, description="List of issues found (for lint, type check)"
    )
