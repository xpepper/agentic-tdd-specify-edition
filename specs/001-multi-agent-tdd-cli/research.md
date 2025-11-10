# Research: Multi-Agent TDD CLI Tool

**Feature**: 001-multi-agent-tdd-cli  
**Created**: 2025-11-10  
**Purpose**: Resolve technical unknowns and establish implementation patterns

## 1. LangChain Multi-Agent Patterns

### Decision: Sequential Agent Execution with State Handoff

**Rationale**: The TDD workflow is inherently sequential (Tester → Implementer → Refactorer → repeat). We don't need parallel agent execution or complex routing. Each agent completes its task, updates the file system and git state, then passes control to the next agent.

**Implementation Pattern**:
```python
# Supervisor orchestrates sequential execution
class SupervisorAgent:
    def run_cycle(self, cycle_num: int) -> CycleResult:
        # Tester writes failing test
        tester_result = self.tester.execute(context=self.get_context())
        if tester_result.test_already_passes:
            return self.handle_overshoot()
        
        # Implementer makes test pass
        impl_result = self.implementer.execute(context=self.get_context())
        if not impl_result.success:
            return self.handle_impl_failure(impl_result)
        
        # Refactorer improves quality
        refactor_result = self.refactorer.execute(context=self.get_context())
        
        return CycleResult(success=True, cycle=cycle_num)
```

**Alternatives Considered**:
- **LangGraph**: Too complex for sequential workflow, designed for DAG-based agent graphs
- **LangChain AgentExecutor with custom tools**: Adds unnecessary tool-calling overhead when agents just need to run shell commands
- **AutoGen multi-agent conversation**: Optimized for chat-based collaboration, not file system operations

**Key Insight**: Agents don't need to "talk" to each other. They read shared state (codebase + git) and execute their role. This minimizes token usage and simplifies orchestration.

---

## 2. Token Optimization Strategies

### Decision: Stateless Agents Reading Fresh Context Per Execution

**Rationale**: Each agent execution reads current codebase state (via file reads) and recent git history (last 3-5 commits). No conversation history preserved between cycles. This keeps prompts bounded and context-relevant.

**Implementation Pattern**:
```python
def get_context(self) -> AgentContext:
    return AgentContext(
        kata_description=read_file(self.kata_path),
        current_code=read_directory_tree(self.work_dir, include_content=True),
        recent_commits=git_log(limit=5),
        last_test_output=self.last_test_result,
        cycle_number=self.current_cycle
    )
```

**Context Budget Per Agent**:
- Kata description: ~500-2000 tokens
- Current codebase: ~500-3000 tokens (small katas)
- Recent git commits: ~200-500 tokens
- System prompt: ~300-500 tokens
- **Total input**: ~1500-6000 tokens per agent call

**Token Savings**:
- No conversation history (saves 1000s of tokens in long sessions)
- No inter-agent messages (saves 100s of tokens per cycle)
- Fresh context each time (agents never get stale info)

**Alternatives Considered**:
- **Persistent conversation memory**: Grows unbounded, not suitable for 15+ cycle executions
- **RAG over codebase**: Overkill for small katas (<500 LOC)
- **Incremental updates**: Adds complexity tracking what changed; simpler to re-read

---

## 3. Git-Based Agent Communication

### Decision: Git Commits as Agent Message Protocol

**Rationale**: Commits provide structured, time-ordered communication with clear semantics. Commit messages describe intent, diffs show changes, test results shown in commit body or tags.

**Implementation Pattern**:
```python
# Tester stages but doesn't commit
git.add("tests/test_fizzbuzz.py")
# (no commit yet - waiting for implementation)

# Implementer commits test + implementation together
git.add("src/fizzbuzz.py")
git.commit(
    message="feat: implement fizzbuzz basic cases\n\nPasses tests: test_fizz, test_buzz",
    stage_all=True  # includes previously staged test
)

# Refactorer commits refactoring
git.commit(
    message="refactor: extract number classification logic\n\nImproves: readability, naming"
)
```

**Agent Context Reading**:
```python
# Agents read git history to understand what happened
recent_commits = git_log(limit=5)
# Each commit shows:
# - Who: test/feat/refactor prefix indicates agent
# - What: file diffs
# - Why: commit message body
```

**Alternatives Considered**:
- **Shared database**: Adds external dependency, overkill for file-based workflow
- **JSON state file**: Less intuitive than git, loses time-ordered history
- **Agent-to-agent messages**: Verbose, increases token usage

---

## 4. OpenAI-Compatible Provider Support

### Decision: LangChain ChatOpenAI with Custom Base URLs

**Rationale**: LangChain's `ChatOpenAI` class accepts `base_url` parameter, allowing any OpenAI-compatible provider. We just need a mapping of provider names to default base URLs.

**Implementation Pattern**:
```python
from langchain_openai import ChatOpenAI

PROVIDER_URLS = {
    "openai": "https://api.openai.com/v1",
    "perplexity": "https://api.perplexity.ai",
    "deepseek": "https://api.deepseek.com/v1",
    "iflow": "https://apis.iflow.cn/v1",
}

def create_llm(provider: str, model: str, api_key: str, base_url: str | None = None):
    url = base_url or PROVIDER_URLS.get(provider)
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=url,
        temperature=0.1,  # Low temp for deterministic code generation
    )
```

**API Key Resolution**:
1. CLI `--api-key` flag (highest priority)
2. Provider-specific env var: `{PROVIDER_NAME}_API_KEY` (e.g., `OPENAI_API_KEY`)
3. Generic env var: `AGENTIC_TDD_API_KEY`
4. Error if none found

**Alternatives Considered**:
- **LiteLLM**: Adds extra dependency, LangChain already provides what we need
- **Custom HTTP client**: Reinventing wheel, LangChain handles retries/errors

---

## 5. Shell Command Execution from Agents

### Decision: Subprocess with Streaming Output and Timeout

**Rationale**: Agents need to see live output from commands (test results, compiler errors) to make decisions. Subprocess with line-by-line streaming provides this without buffering delays.

**Implementation Pattern**:
```python
import subprocess
from typing import Iterator

def run_command(
    cmd: list[str],
    cwd: str,
    timeout: int = 30
) -> tuple[int, str]:
    """Execute command, stream output, return exit code and captured output."""
    output_lines = []
    
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1  # Line buffered
    )
    
    try:
        for line in iter(process.stdout.readline, ''):
            print(line, end='')  # Live console output
            output_lines.append(line)
        
        process.wait(timeout=timeout)
        return process.returncode, ''.join(output_lines)
    
    except subprocess.TimeoutExpired:
        process.kill()
        raise TimeoutError(f"Command timed out after {timeout}s")
```

**Safety Considerations**:
- Commands run in kata working directory (sandboxed)
- Timeout prevents infinite loops
- No shell=True (prevents injection attacks)

**Alternatives Considered**:
- **LangChain ShellTool**: Designed for LLM-generated commands, we have predetermined command structures
- **Blocking subprocess**: Loses live output, agent can't react to long-running tests

---

## 6. Rust Language Runner

### Decision: Cargo Command Sequence for TDD Workflow

**Rationale**: Rust has excellent tooling with clear command-line interfaces. Cargo provides all necessary operations.

**Command Mapping**:
```python
class RustRunner(LanguageRunner):
    def initialize_project(self, path: Path) -> CommandResult:
        # Create new Cargo project if needed
        if not (path / "Cargo.toml").exists():
            return run_command(["cargo", "init", "--name", "kata"], cwd=path)
    
    def run_tests(self, path: Path) -> TestResult:
        # Run tests with color output
        exit_code, output = run_command(
            ["cargo", "test", "--color=always"],
            cwd=path
        )
        return TestResult(
            passed=(exit_code == 0),
            output=output,
            test_count=self._parse_test_count(output)
        )
    
    def build(self, path: Path) -> CommandResult:
        return run_command(["cargo", "build"], cwd=path)
    
    def format_code(self, path: Path) -> CommandResult:
        return run_command(["cargo", "fmt"], cwd=path)
    
    def lint_code(self, path: Path) -> CommandResult:
        return run_command(
            ["cargo", "clippy", "--", "-D", "warnings"],
            cwd=path
        )
```

**Quality Gate Sequence** (before commit):
1. `cargo fmt` (auto-format)
2. `cargo clippy` (lint check)
3. `cargo test` (all tests must pass)
4. `cargo build` (final compilation check)

**Alternatives Considered**:
- **Custom test harness**: Cargo test is already excellent
- **Separate rustfmt/clippy**: Cargo wraps these tools nicely

---

## 7. Agent Failure Recovery

### Decision: Supervisor with Retry and Escalation Strategy

**Rationale**: Agents can fail due to LLM mistakes, unclear requirements, or environmental issues. Supervisor needs heuristics to decide: retry, simplify, or abort.

**Recovery Strategies**:

```python
class SupervisorAgent:
    def handle_tester_overshoot(self) -> Action:
        """Test passes immediately - implementer wrote too much code."""
        self.penalize_implementer()  # Note in logs/metrics
        return Action.REQUEST_DIFFERENT_TEST
    
    def handle_implementer_failure(self, result: ImplResult, attempts: int) -> Action:
        """Implementer can't make test pass."""
        if attempts < 3:
            return Action.RETRY_WITH_HINT  # Include error details in context
        
        if self._test_is_too_complex(result):
            return Action.REQUEST_SIMPLER_TEST
        
        if self._refactoring_needed(result):
            return Action.PREPARATORY_REFACTOR
        
        return Action.ABORT_WITH_REASON
    
    def handle_refactorer_failure(self, attempts: int) -> Action:
        """Refactorer broke tests."""
        if attempts < 3:
            return Action.RETRY_REFACTOR
        
        # After 3 attempts, revert and proceed
        git.revert_to_last_commit()
        return Action.SKIP_REFACTOR_THIS_CYCLE
```

**Failure Signals**:
- Tester: `test_already_passes` flag in result
- Implementer: Test suite still failing after N attempts
- Refactorer: Test suite red after refactoring

**Alternatives Considered**:
- **Infinite retries**: Can loop forever, need bounded attempts
- **Immediate abort**: Too strict, agents should get multiple tries
- **LLM-based recovery**: Too expensive, use heuristics first

---

## 8. Prompt Engineering for Code Kata Agents

### Decision: Role-Specific System Prompts with Kata Context

**Implementation Pattern**:
```python
TESTER_PROMPT = """You are a TDD Tester agent. Your role:
1. Read the kata description and existing code
2. Write ONE small failing test for the next behavior
3. Run tests to verify it fails (red state)
4. Stage (git add) the test file but DO NOT commit

Constraints:
- Test must fail initially (if it passes, you overshot)
- Test ONE behavior at a time
- Use clear test names describing the behavior
- Current kata: {kata_description}
- Current cycle: {cycle_num}/15
"""

IMPLEMENTER_PROMPT = """You are a TDD Implementer agent. Your role:
1. Read the failing test from the Tester
2. Write MINIMAL code to make that test pass
3. Run all tests to verify green state
4. Commit test + implementation together

Constraints:
- Minimal change ONLY (no extra features)
- All tests must pass before commit
- Use conventional commit message: "feat: <behavior>"
"""

REFACTORER_PROMPT = """You are a TDD Refactorer agent. Your role:
1. Improve code quality while keeping tests green
2. Focus: naming, structure, duplication, readability
3. Run tests after each change
4. Commit if green, revert if red

Constraints:
- Tests must stay green
- Honor kata constraints: {kata_constraints}
- Up to 3 retry attempts
"""
```

**Alternatives Considered**:
- **Single mega-prompt**: Less focused, agents get confused about role boundaries
- **Few-shot examples**: Increases token usage, system prompts + role clarity sufficient

---

## Summary of Key Decisions

| Area | Decision | Primary Rationale |
|------|----------|-------------------|
| Agent Orchestration | Sequential execution with state handoff | TDD is inherently sequential, no parallelism needed |
| Token Optimization | Stateless agents with fresh context | Bounded context, no conversation history growth |
| Agent Communication | Git commits as message protocol | Structured, time-ordered, semantic communication |
| LLM Provider | LangChain ChatOpenAI with custom base URLs | Native support for OpenAI-compatible APIs |
| Shell Execution | Subprocess with streaming and timeout | Live output for agent feedback, safety via timeout |
| Rust Support | Cargo command sequence | Comprehensive tooling for TDD workflow |
| Failure Recovery | Supervisor with bounded retries and heuristics | Pragmatic recovery without infinite loops |
| Prompts | Role-specific system prompts | Clear role boundaries, minimal token overhead |

---

## Technology Stack Summary

**Core Framework**: LangChain 0.1.x (agent orchestration)  
**CLI**: Typer 0.9.x (argument parsing, command structure)  
**LLM Client**: langchain-openai (ChatOpenAI with custom base URLs)  
**Git Operations**: GitPython 3.1.x (git command wrappers)  
**Shell Execution**: subprocess (Python stdlib)  
**Console Output**: Rich 13.x (colored, structured output)  
**Data Validation**: Pydantic 2.x (config and data models)  
**Testing**: pytest 7.x (tool development tests)  

**Python Version**: 3.11+ (required for modern type hints and performance)

---

## Next Steps

1. **Phase 1**: Create data models (Agent, Runner, Config, TDDCycle)
2. **Phase 1**: Define contracts (Language Runner interface, Agent interface)
3. **Phase 1**: Write quickstart guide (installation, first kata execution)
4. **Phase 2**: Generate tasks.md organized by user stories
