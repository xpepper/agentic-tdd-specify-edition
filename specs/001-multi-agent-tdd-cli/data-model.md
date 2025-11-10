# Data Model: Multi-Agent TDD CLI Tool

**Feature**: 001-multi-agent-tdd-cli  
**Created**: 2025-11-10  
**Purpose**: Define data structures, entities, and relationships

## Overview

This document defines the core data structures used throughout the multi-agent TDD system. All models use Pydantic for validation and serialization. Models are organized by domain area: configuration, kata representation, TDD cycle tracking, agent execution, and language runner abstraction.

---

## 1. Configuration Models

### 1.1 LLMProviderConfig

Configuration for LLM provider connection.

```python
from pydantic import BaseModel, Field, validator
from typing import Literal

class LLMProviderConfig(BaseModel):
    """Configuration for an OpenAI-compatible LLM provider."""
    
    provider: Literal["openai", "perplexity", "deepseek", "iflow", "custom"] = Field(
        description="Provider identifier"
    )
    
    model: str = Field(
        description="Model name (e.g., 'gpt-4', 'llama-2-70b-chat')"
    )
    
    api_key: str = Field(
        description="API key for authentication"
    )
    
    base_url: str | None = Field(
        default=None,
        description="Custom base URL (overrides provider default)"
    )
    
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="LLM temperature for code generation (low for determinism)"
    )
    
    timeout: int = Field(
        default=30,
        gt=0,
        description="Request timeout in seconds"
    )
    
    @validator("base_url", pre=True, always=True)
    def set_default_base_url(cls, v, values):
        """Set default base URL based on provider if not specified."""
        if v is not None:
            return v
        
        provider_urls = {
            "openai": "https://api.openai.com/v1",
            "perplexity": "https://api.perplexity.ai",
            "deepseek": "https://api.deepseek.com/v1",
            "iflow": "https://apis.iflow.cn/v1",
        }
        
        provider = values.get("provider")
        if provider == "custom":
            raise ValueError("Custom provider requires explicit base_url")
        
        return provider_urls.get(provider)
```

### 1.2 ToolConfig

Top-level configuration for the CLI tool.

```python
from pathlib import Path

class ToolConfig(BaseModel):
    """Configuration for the agentic-tdd CLI tool."""
    
    kata_path: Path = Field(
        description="Path to kata description markdown file"
    )
    
    work_dir: Path = Field(
        description="Working directory for kata implementation"
    )
    
    language: str = Field(
        default="rust",
        description="Target language for implementation (e.g., 'rust', 'python')"
    )
    
    llm_config: LLMProviderConfig = Field(
        description="LLM provider configuration"
    )
    
    max_cycles: int = Field(
        default=15,
        gt=0,
        description="Maximum number of TDD cycles before stopping"
    )
    
    max_retries: int = Field(
        default=3,
        gt=0,
        description="Maximum retry attempts per agent before escalation"
    )
    
    verbose: bool = Field(
        default=False,
        description="Enable verbose logging"
    )
    
    @validator("work_dir")
    def validate_work_dir(cls, v):
        """Ensure work directory is absolute and writable."""
        if not v.is_absolute():
            v = v.absolute()
        v.mkdir(parents=True, exist_ok=True)
        return v
```

---

## 2. Kata Representation

### 2.1 KataDescription

Parsed kata specification from markdown file.

```python
class KataConstraint(BaseModel):
    """A specific constraint for the kata implementation."""
    
    description: str = Field(
        description="Human-readable constraint description"
    )
    
    applies_to: Literal["code", "tests", "both"] = Field(
        default="code",
        description="Scope where constraint applies"
    )

class KataDescription(BaseModel):
    """Parsed kata specification."""
    
    title: str = Field(
        description="Kata title"
    )
    
    description: str = Field(
        description="Full kata description text"
    )
    
    requirements: list[str] = Field(
        default_factory=list,
        description="List of behavioral requirements"
    )
    
    constraints: list[KataConstraint] = Field(
        default_factory=list,
        description="Implementation constraints (e.g., 'No primitives', 'Single indentation level')"
    )
    
    examples: list[str] = Field(
        default_factory=list,
        description="Example inputs/outputs"
    )
    
    source_path: Path = Field(
        description="Path to original kata markdown file"
    )
    
    @classmethod
    def from_markdown(cls, path: Path) -> "KataDescription":
        """Parse kata description from markdown file.
        
        Expected structure:
        # Title
        ## Description
        ...
        ## Requirements
        - Req 1
        - Req 2
        ## Constraints (optional)
        - Constraint 1
        ## Examples (optional)
        ...
        """
        # Implementation in kata.py module
        raise NotImplementedError
```

---

## 3. TDD Cycle Tracking

### 3.1 TDDPhase

Enum representing current phase in TDD cycle.

```python
from enum import Enum

class TDDPhase(str, Enum):
    """Phase within a TDD cycle."""
    
    TESTING = "testing"           # Tester writing failing test
    IMPLEMENTING = "implementing" # Implementer making test pass
    REFACTORING = "refactoring"   # Refactorer improving quality
    COMPLETE = "complete"         # Cycle complete, ready for next
    FAILED = "failed"             # Cycle failed, requires intervention
```

### 3.2 CycleState

State tracking for a single TDD cycle.

```python
from datetime import datetime

class CycleState(BaseModel):
    """State tracking for a single TDD cycle."""
    
    cycle_num: int = Field(
        ge=1,
        description="Cycle number (1-indexed)"
    )
    
    phase: TDDPhase = Field(
        default=TDDPhase.TESTING,
        description="Current phase in cycle"
    )
    
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Cycle start timestamp"
    )
    
    completed_at: datetime | None = Field(
        default=None,
        description="Cycle completion timestamp"
    )
    
    test_file_path: Path | None = Field(
        default=None,
        description="Path to test file created/modified in this cycle"
    )
    
    implementation_files: list[Path] = Field(
        default_factory=list,
        description="Implementation files modified in this cycle"
    )
    
    commits: list[str] = Field(
        default_factory=list,
        description="Git commit SHAs created in this cycle"
    )
    
    errors: list[str] = Field(
        default_factory=list,
        description="Error messages encountered in this cycle"
    )
    
    def mark_complete(self):
        """Mark cycle as complete."""
        self.phase = TDDPhase.COMPLETE
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self, error: str):
        """Mark cycle as failed."""
        self.phase = TDDPhase.FAILED
        self.errors.append(error)
        self.completed_at = datetime.utcnow()
```

### 3.3 SessionState

Overall TDD session state tracking.

```python
class SessionState(BaseModel):
    """State tracking for entire TDD session."""
    
    kata: KataDescription = Field(
        description="Kata being implemented"
    )
    
    work_dir: Path = Field(
        description="Working directory"
    )
    
    current_cycle: int = Field(
        default=1,
        ge=1,
        description="Current cycle number"
    )
    
    cycles: list[CycleState] = Field(
        default_factory=list,
        description="History of all cycles"
    )
    
    total_commits: int = Field(
        default=0,
        description="Total commits made"
    )
    
    started_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Session start timestamp"
    )
    
    completed_at: datetime | None = Field(
        default=None,
        description="Session completion timestamp"
    )
    
    def get_current_cycle_state(self) -> CycleState:
        """Get or create current cycle state."""
        if not self.cycles or self.cycles[-1].phase == TDDPhase.COMPLETE:
            cycle = CycleState(cycle_num=self.current_cycle)
            self.cycles.append(cycle)
            return cycle
        return self.cycles[-1]
    
    def advance_cycle(self):
        """Advance to next cycle."""
        self.current_cycle += 1
```

---

## 4. Agent Execution Models

### 4.1 AgentRole

Enum for agent types.

```python
class AgentRole(str, Enum):
    """Agent role identifier."""
    
    TESTER = "tester"
    IMPLEMENTER = "implementer"
    REFACTORER = "refactorer"
    SUPERVISOR = "supervisor"
```

### 4.2 AgentContext

Context provided to agents before execution.

```python
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
    
    kata_description: str = Field(
        description="Full kata description text"
    )
    
    kata_constraints: list[str] = Field(
        default_factory=list,
        description="List of kata constraint descriptions"
    )
    
    cycle_number: int = Field(
        description="Current cycle number"
    )
    
    codebase_files: list[CodebaseFile] = Field(
        default_factory=list,
        description="Current codebase files with content"
    )
    
    recent_commits: list[GitCommitInfo] = Field(
        default_factory=list,
        description="Last 5 git commits for context"
    )
    
    last_test_output: str | None = Field(
        default=None,
        description="Output from most recent test run"
    )
    
    last_error: str | None = Field(
        default=None,
        description="Last error message if agent failed"
    )
    
    retry_attempt: int = Field(
        default=0,
        ge=0,
        description="Current retry attempt number (0 = first attempt)"
    )
```

### 4.3 AgentResult

Result returned by agent execution.

```python
class AgentResult(BaseModel):
    """Result from agent execution."""
    
    role: AgentRole = Field(
        description="Agent that produced this result"
    )
    
    success: bool = Field(
        description="Whether agent completed successfully"
    )
    
    message: str = Field(
        description="Human-readable result message"
    )
    
    files_modified: list[Path] = Field(
        default_factory=list,
        description="Files created or modified"
    )
    
    tests_passed: bool | None = Field(
        default=None,
        description="Whether tests passed after agent action"
    )
    
    test_output: str | None = Field(
        default=None,
        description="Test execution output"
    )
    
    commits_made: list[str] = Field(
        default_factory=list,
        description="Git commit SHAs created"
    )
    
    overshoot_detected: bool = Field(
        default=False,
        description="Whether Tester detected premature test passing"
    )
    
    error_details: str | None = Field(
        default=None,
        description="Detailed error information if failed"
    )
    
    duration_seconds: float = Field(
        description="Execution duration in seconds"
    )
```

---

## 5. Language Runner Models

### 5.1 TestResult

Result from test suite execution.

```python
class TestResult(BaseModel):
    """Result from running test suite."""
    
    passed: bool = Field(
        description="Whether all tests passed"
    )
    
    test_count: int = Field(
        ge=0,
        description="Total number of tests run"
    )
    
    passed_count: int = Field(
        ge=0,
        description="Number of tests passed"
    )
    
    failed_count: int = Field(
        ge=0,
        description="Number of tests failed"
    )
    
    output: str = Field(
        description="Raw test execution output"
    )
    
    duration_seconds: float = Field(
        description="Test execution duration"
    )
    
    error_message: str | None = Field(
        default=None,
        description="Error message if tests failed to run"
    )
```

### 5.2 CommandResult

Generic result from shell command execution.

```python
class CommandResult(BaseModel):
    """Result from shell command execution."""
    
    command: list[str] = Field(
        description="Command that was executed"
    )
    
    exit_code: int = Field(
        description="Process exit code"
    )
    
    output: str = Field(
        description="Combined stdout and stderr"
    )
    
    success: bool = Field(
        description="Whether command succeeded (exit code 0)"
    )
    
    duration_seconds: float = Field(
        description="Execution duration"
    )
    
    timed_out: bool = Field(
        default=False,
        description="Whether command exceeded timeout"
    )
```

### 5.3 QualityGateResult

Result from running quality gates (format, lint, build).

```python
class QualityGateResult(BaseModel):
    """Result from running quality gates."""
    
    gate_name: Literal["format", "lint", "type_check", "build"] = Field(
        description="Quality gate identifier"
    )
    
    passed: bool = Field(
        description="Whether gate passed"
    )
    
    command_result: CommandResult = Field(
        description="Underlying command result"
    )
    
    auto_fixed: bool = Field(
        default=False,
        description="Whether issues were automatically fixed (e.g., formatting)"
    )
    
    issues_found: list[str] = Field(
        default_factory=list,
        description="List of issues found (for lint, type check)"
    )
```

---

## 6. Relationships and Usage

### 6.1 Data Flow

```
CLI Input
  ↓
ToolConfig → LLMProviderConfig
  ↓
KataDescription ← from_markdown(kata_path)
  ↓
SessionState (tracks cycles)
  ↓
Supervisor orchestrates agents
  ↓
AgentContext → Agent → AgentResult
  ↓                    ↓
  ↓                 updates
  ↓                    ↓
  ← LanguageRunner → TestResult, CommandResult, QualityGateResult
  ↓
CycleState (updated with results)
  ↓
Repeat until complete or max_cycles
```

### 6.2 Key Invariants

1. **CycleState.cycle_num** matches **SessionState.current_cycle** for active cycle
2. **AgentResult.tests_passed** must be `True` before Implementer commits
3. **AgentResult.tests_passed** must remain `True` after Refactorer commits
4. **SessionState.total_commits** equals sum of commits across all cycles
5. **TestResult.passed_count + failed_count** equals **test_count**
6. **QualityGateResult.passed** must be `True` before any agent commits

### 6.3 Serialization

All models support:
- **JSON serialization**: `model.model_dump_json()` for logging and storage
- **Validation**: Pydantic validates on construction
- **Type safety**: Models provide type hints for IDE support

---

## 7. Future Extensions

### 7.1 Additional Languages

When adding new language runners, extend:
- **LanguageRunner** interface (see contracts/language_runner.py)
- **ToolConfig.language** enum values
- **CodebaseFile.language** detection logic

### 7.2 Additional Providers

When adding new LLM providers, extend:
- **LLMProviderConfig.provider** literal type
- **provider_urls** mapping in validator
- **API key environment variable** naming in config.py

### 7.3 Metrics and Analytics

Future additions might include:
- **SessionMetrics**: Token usage, cost, latency per agent
- **CycleMetrics**: Time per phase, retry counts
- **QualityMetrics**: Test coverage, code complexity trends

---

## 8. Implementation Files

Models organized by domain:

- `models/config.py` → LLMProviderConfig, ToolConfig
- `models/kata.py` → KataDescription, KataConstraint
- `models/cycle.py` → TDDPhase, CycleState, SessionState
- `models/agent.py` → AgentRole, AgentContext, AgentResult
- `models/runner.py` → TestResult, CommandResult, QualityGateResult

All models import from `pydantic` and use Python 3.11+ type hints.

---

**Version**: 1.0.0 | **Status**: Complete | **Next**: contracts/ and quickstart.md
