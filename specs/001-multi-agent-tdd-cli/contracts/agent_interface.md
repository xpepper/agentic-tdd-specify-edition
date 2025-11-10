# Agent Interface Contract

**Purpose**: Define the execution contract for TDD agents. All agents follow the same interface pattern while implementing role-specific behavior.

---

## Interface Definition

### Base Agent Class

```python
from abc import ABC, abstractmethod
from langchain_openai import ChatOpenAI
from models.agent import AgentRole, AgentContext, AgentResult

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
    
    def _run_llm(self, context: AgentContext) -> str:
        """Internal: Run LLM with system prompt and context.
        
        Args:
            context: Agent execution context
            
        Returns:
            LLM response text
        """
        from langchain.schema import SystemMessage, HumanMessage
        
        system_prompt = self.get_system_prompt()
        user_prompt = self._build_user_prompt(context)
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    @abstractmethod
    def _build_user_prompt(self, context: AgentContext) -> str:
        """Build user prompt from context.
        
        Args:
            context: Agent execution context
            
        Returns:
            Formatted prompt string with context details
        """
        pass
```

---

## Agent-Specific Contracts

### Tester Agent

**Role**: Write failing tests for next behavior.

**Responsibilities**:
1. Read kata description and existing code
2. Identify next untested behavior
3. Write ONE small test for that behavior
4. Run tests to verify RED state
5. Stage test file (git add) but DO NOT commit
6. Detect overshoot (test passes unexpectedly)

**Success Criteria**:
- Test written and staged
- Test fails when run (red state verified)
- No overshoot detected

**Failure Modes**:
- Test passes immediately (overshoot) → Report to Supervisor
- Cannot determine next test → Request clarification
- Syntax errors in test → Retry with error details

**Interface Additions**:
```python
class TesterAgent(Agent):
    @property
    def role(self) -> AgentRole:
        return AgentRole.TESTER
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Write and stage failing test.
        
        Returns:
            AgentResult with:
            - success=True if test written and fails
            - overshoot_detected=True if test passes immediately
            - files_modified=[test file path]
            - tests_passed=False (red state)
        """
        pass
```

---

### Implementer Agent

**Role**: Make failing test pass with minimal code.

**Responsibilities**:
1. Read staged test file
2. Read last test output (failure message)
3. Write MINIMAL code to pass test
4. Run all tests to verify GREEN state
5. Run quality gates (format, lint, build)
6. Commit test + implementation together

**Success Criteria**:
- All tests pass (green state)
- Quality gates pass
- Test and implementation committed together
- Code change is minimal (no extra features)

**Failure Modes**:
- Tests still fail after implementation → Retry with error details
- Quality gates fail → Fix and retry
- Implementation too broad → Supervisor detects on next cycle

**Interface Additions**:
```python
class ImplementerAgent(Agent):
    @property
    def role(self) -> AgentRole:
        return AgentRole.IMPLEMENTER
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Implement code to pass test, then commit.
        
        Returns:
            AgentResult with:
            - success=True if tests pass and committed
            - files_modified=[implementation file paths]
            - tests_passed=True (green state)
            - commits_made=[commit SHA]
        """
        pass
```

---

### Refactorer Agent

**Role**: Improve code quality while maintaining green state.

**Responsibilities**:
1. Read current codebase
2. Identify quality improvement opportunities:
   - Poor naming
   - Code duplication
   - Complex logic
   - Violation of kata constraints
3. Apply ONE refactoring change
4. Run tests to verify still GREEN
5. Run quality gates
6. Commit if green, revert if red
7. Up to 3 retry attempts

**Success Criteria**:
- Code quality improved
- All tests still pass
- Quality gates pass
- Refactoring committed

**Failure Modes**:
- Tests fail after refactoring → Revert and retry different refactoring
- Exceeded 3 retries → Report to Supervisor, revert, skip this cycle
- No improvements needed → Report success with no changes

**Interface Additions**:
```python
class RefactorerAgent(Agent):
    @property
    def role(self) -> AgentRole:
        return AgentRole.REFACTORER
    
    def execute(self, context: AgentContext) -> AgentResult:
        """Refactor code while maintaining green state.
        
        Returns:
            AgentResult with:
            - success=True if refactored and committed (or no changes needed)
            - files_modified=[refactored file paths]
            - tests_passed=True (green state maintained)
            - commits_made=[commit SHA] (if changes made)
        """
        pass
```

---

### Supervisor Agent

**Role**: Orchestrate TDD cycles and handle failures.

**Responsibilities**:
1. Initialize TDD session (git repo, project structure)
2. Orchestrate cycle: Tester → Implementer → Refactorer
3. Detect and handle failures:
   - Tester overshoot → Request different test
   - Implementer failure → Retry with hints or simplify test
   - Refactorer failure → Bounded retries then skip
4. Decide cycle continuation or session completion
5. Track metrics and state

**Success Criteria**:
- All cycles complete successfully
- Kata requirements satisfied
- Clean git history (no red commits)

**Failure Modes**:
- Max cycles reached → Complete with partial implementation
- Unrecoverable agent failure → Abort with reason
- Kata requirements unclear → Request clarification

**Interface Differences**:
```python
class SupervisorAgent:
    """Supervisor does not inherit from Agent (different interface)."""
    
    def __init__(
        self,
        tester: TesterAgent,
        implementer: ImplementerAgent,
        refactorer: RefactorerAgent,
        runner: LanguageRunner,
        config: ToolConfig
    ):
        self.tester = tester
        self.implementer = implementer
        self.refactorer = refactorer
        self.runner = runner
        self.config = config
        self.session_state = SessionState(...)
    
    def run_session(self) -> SessionState:
        """Execute complete TDD session.
        
        Returns:
            SessionState with complete cycle history
        """
        pass
    
    def run_cycle(self) -> CycleState:
        """Execute single TDD cycle.
        
        Returns:
            CycleState with cycle results
        """
        pass
    
    def handle_tester_overshoot(self, result: AgentResult) -> Action:
        """Handle test passing immediately."""
        pass
    
    def handle_implementer_failure(
        self,
        result: AgentResult,
        attempt: int
    ) -> Action:
        """Handle implementer unable to pass test."""
        pass
    
    def handle_refactorer_failure(
        self,
        result: AgentResult,
        attempt: int
    ) -> Action:
        """Handle refactorer breaking tests."""
        pass
```

---

## Execution Protocol

### Agent Execution Flow

```python
# 1. Context gathering
context = AgentContext(
    kata_description=read_file(kata_path),
    codebase_files=read_codebase(work_dir),
    recent_commits=git_log(limit=5),
    last_test_output=last_test_output,
    cycle_number=current_cycle
)

# 2. Agent execution
result = agent.execute(context)

# 3. Validation
if not result.success:
    if context.retry_attempt < max_retries:
        # Add error details to context and retry
        context.last_error = result.error_details
        context.retry_attempt += 1
        result = agent.execute(context)
    else:
        # Escalate to supervisor
        raise AgentExecutionError(result.error_details)

# 4. State update
update_session_state(result)
```

### Supervisor Cycle Flow

```python
def run_cycle(self) -> CycleState:
    """Execute single TDD cycle."""
    cycle_state = self.session_state.get_current_cycle_state()
    
    # Phase 1: Tester
    cycle_state.phase = TDDPhase.TESTING
    context = self._build_context()
    tester_result = self.tester.execute(context)
    
    if tester_result.overshoot_detected:
        return self.handle_tester_overshoot(tester_result)
    
    # Phase 2: Implementer
    cycle_state.phase = TDDPhase.IMPLEMENTING
    impl_result = self._execute_with_retry(
        self.implementer,
        context,
        max_attempts=3
    )
    
    if not impl_result.success:
        return self.handle_implementer_failure(impl_result)
    
    # Phase 3: Refactorer
    cycle_state.phase = TDDPhase.REFACTORING
    refactor_result = self._execute_with_retry(
        self.refactorer,
        context,
        max_attempts=3
    )
    
    # Refactorer failure is non-fatal (revert and proceed)
    if not refactor_result.success:
        git.revert_to_last_commit()
    
    cycle_state.mark_complete()
    return cycle_state
```

---

## Prompt Engineering Standards

### System Prompt Structure

```python
SYSTEM_PROMPT_TEMPLATE = """You are a {role} agent in an autonomous TDD system.

**Your Role**: {role_description}

**Responsibilities**:
{responsibilities_list}

**Constraints**:
{constraints_list}

**Available Tools**:
{tools_list}

**Output Format**:
{output_format_spec}

**Success Criteria**:
{success_criteria}
"""
```

### User Prompt Structure

```python
USER_PROMPT_TEMPLATE = """
# Kata Description
{kata_description}

# Current Cycle
Cycle {cycle_number} of {max_cycles}

# Recent Commits
{recent_commits_formatted}

# Current Codebase
{codebase_files_formatted}

# Last Test Output
{last_test_output}

# Your Task
{agent_specific_task}
"""
```

### Response Parsing

Agents return structured responses that are parsed into AgentResult:

```python
def parse_agent_response(response: str, role: AgentRole) -> AgentResult:
    """Parse LLM response into AgentResult.
    
    Expected format:
    ---
    SUCCESS: true/false
    MESSAGE: Human-readable summary
    FILES_MODIFIED: path1, path2, ...
    TESTS_PASSED: true/false (if applicable)
    ---
    
    Args:
        response: LLM response text
        role: Agent role for context
        
    Returns:
        AgentResult with parsed fields
    """
    # Implementation parses structured output
    pass
```

---

## Testing Contract

### Agent Unit Tests

Each agent MUST have unit tests covering:

1. **System prompt generation**: Correct for role
2. **User prompt building**: Includes all context
3. **Response parsing**: Handles success and failure cases
4. **Error handling**: Graceful degradation

### Agent Integration Tests

Integration tests use real LLM (or mock) and file system:

```python
def test_tester_agent_writes_failing_test(tmp_path):
    """Test Tester agent writes failing test."""
    # Setup
    kata = KataDescription(...)
    llm = ChatOpenAI(...)  # Or mock
    agent = TesterAgent(llm, tmp_path)
    
    # Execute
    context = AgentContext(kata_description=str(kata), ...)
    result = agent.execute(context)
    
    # Verify
    assert result.success
    assert len(result.files_modified) == 1
    assert result.tests_passed == False  # Red state
    assert not result.overshoot_detected
```

---

## Error Handling

### Exception Hierarchy

```python
class AgentError(Exception):
    """Base exception for agent errors."""
    pass

class AgentExecutionError(AgentError):
    """Agent execution failed unrecoverably."""
    pass

class AgentTimeoutError(AgentError):
    """Agent execution exceeded timeout."""
    pass

class QualityGateFailure(AgentError):
    """Quality gate check failed."""
    pass
```

### Retry Strategy

```python
def execute_with_retry(
    agent: Agent,
    context: AgentContext,
    max_attempts: int = 3
) -> AgentResult:
    """Execute agent with retry logic.
    
    Args:
        agent: Agent to execute
        context: Execution context
        max_attempts: Maximum retry attempts
        
    Returns:
        AgentResult from successful execution
        
    Raises:
        AgentExecutionError: If all attempts fail
    """
    for attempt in range(max_attempts):
        try:
            context.retry_attempt = attempt
            result = agent.execute(context)
            
            if result.success:
                return result
            
            # Add error to context for next attempt
            context.last_error = result.error_details
            
        except Exception as e:
            if attempt == max_attempts - 1:
                raise AgentExecutionError(f"Failed after {max_attempts} attempts: {e}")
            
            context.last_error = str(e)
    
    raise AgentExecutionError(f"Failed after {max_attempts} attempts")
```

---

**Version**: 1.0.0 | **Status**: Complete | **Related**: data-model.md Section 4
