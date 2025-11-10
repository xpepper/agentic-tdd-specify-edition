"""TDD cycle tracking models."""

from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field

from .kata import KataDescription


class TDDPhase(str, Enum):
    """Phase within a TDD cycle."""

    TESTING = "testing"  # Tester writing failing test
    IMPLEMENTING = "implementing"  # Implementer making test pass
    REFACTORING = "refactoring"  # Refactorer improving quality
    COMPLETE = "complete"  # Cycle complete, ready for next
    FAILED = "failed"  # Cycle failed, requires intervention


class CycleState(BaseModel):
    """State tracking for a single TDD cycle."""

    cycle_num: int = Field(ge=1, description="Cycle number (1-indexed)")

    phase: TDDPhase = Field(default=TDDPhase.TESTING, description="Current phase in cycle")

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Cycle start timestamp",
    )

    completed_at: datetime | None = Field(default=None, description="Cycle completion timestamp")

    test_file_path: Path | None = Field(
        default=None, description="Path to test file created/modified in this cycle"
    )

    implementation_files: list[Path] = Field(
        default_factory=list, description="Implementation files modified in this cycle"
    )

    commits: list[str] = Field(
        default_factory=list, description="Git commit SHAs created in this cycle"
    )

    errors: list[str] = Field(
        default_factory=list, description="Error messages encountered in this cycle"
    )

    def mark_complete(self) -> None:
        """Mark cycle as complete."""
        self.phase = TDDPhase.COMPLETE
        self.completed_at = datetime.now(UTC)

    def mark_failed(self, error: str) -> None:
        """Mark cycle as failed."""
        self.phase = TDDPhase.FAILED
        self.errors.append(error)
        self.completed_at = datetime.now(UTC)


class SessionState(BaseModel):
    """State tracking for entire TDD session."""

    kata: KataDescription = Field(description="Kata being implemented")

    work_dir: Path = Field(description="Working directory")

    current_cycle: int = Field(default=1, ge=1, description="Current cycle number")

    cycles: list[CycleState] = Field(default_factory=list, description="History of all cycles")

    total_commits: int = Field(default=0, description="Total commits made")

    started_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Session start timestamp",
    )

    completed_at: datetime | None = Field(default=None, description="Session completion timestamp")

    def get_current_cycle_state(self) -> CycleState:
        """Get or create current cycle state."""
        if not self.cycles or self.cycles[-1].phase == TDDPhase.COMPLETE:
            cycle = CycleState(cycle_num=self.current_cycle)
            self.cycles.append(cycle)
            return cycle
        return self.cycles[-1]

    def advance_cycle(self) -> None:
        """Advance to next cycle."""
        self.current_cycle += 1
