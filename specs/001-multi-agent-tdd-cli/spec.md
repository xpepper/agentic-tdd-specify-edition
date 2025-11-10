# Feature Specification: Multi-Agent TDD CLI Tool

**Feature Branch**: `001-multi-agent-tdd-cli`  
**Created**: 2025-11-10  
**Status**: Draft  
**Input**: User description: "Build a multi-agent Test-Driven Development (TDD) CLI tool that is able to develop a code kata autonomously, following the classic TDD cycle, utilizing a user-supplied kata description. The final outcome, after a given amount of TDD steps, should be a codebase containing the code kata."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Execute Basic Kata with Single Language (Priority: P1)

A developer wants to automatically solve a simple code kata (e.g., FizzBuzz) using the TDD approach without writing any code themselves. They provide a kata description file and watch as the tool autonomously writes tests, implements code, and refactors through multiple TDD cycles.

**Why this priority**: This is the core MVP - demonstrating that autonomous multi-agent TDD can work end-to-end for at least one programming language. Without this, the tool has no value.

**Independent Test**: Can be fully tested by running the CLI with a simple kata markdown file (e.g., FizzBuzz) and verifying that a working, tested codebase is produced with a clean git history showing TDD cycles.

**Acceptance Scenarios**:

1. **Given** a kata description file (markdown) and a target language, **When** user runs the CLI with max cycles set to 15, **Then** the tool creates a working directory, initializes a git repository, and produces a complete kata solution with passing tests
2. **Given** the tool is executing a kata, **When** observing the console output, **Then** user sees clear progress indicators showing which agent is active (Tester/Implementer/Refactorer), what action is being taken, and test results
3. **Given** a completed kata execution, **When** examining the git history, **Then** commits show a clear TDD pattern: test additions (staged), implementation commits (test + code), and refactor commits (all tests green)
4. **Given** the tool encounters a failing agent step, **When** the failure is reported, **Then** the Supervisor agent intervenes with recovery actions (simpler test, preparatory refactor) or gracefully terminates with error details

---

### User Story 2 - Configure LLM Provider and Model (Priority: P2)

A developer wants to use their preferred LLM provider (OpenAI, Perplexity, DeepSeek, etc.) and model, providing API credentials securely via environment variables rather than command-line arguments.

**Why this priority**: Flexibility in LLM provider choice is essential for cost control, performance optimization, and avoiding vendor lock-in. However, the tool can demonstrate value with a single hardcoded provider first.

**Independent Test**: Can be tested by running the same kata with different providers (e.g., OpenAI GPT-4, Perplexity Sonar, DeepSeek) and verifying all produce equivalent quality results.

**Acceptance Scenarios**:

1. **Given** API credentials stored in environment variables (e.g., OPENAI_API_KEY, PERPLEXITY_API_KEY), **When** user specifies provider and model via CLI flags, **Then** the tool authenticates successfully and uses the specified model
2. **Given** multiple provider options, **When** user switches between providers for different kata runs, **Then** each provider is used correctly without requiring code changes
3. **Given** missing or invalid API credentials, **When** tool attempts to initialize, **Then** a clear error message indicates which credential is missing or invalid
4. **Given** a custom OpenAI-compatible endpoint URL, **When** user provides base URL via CLI flag, **Then** the tool connects to that endpoint instead of default provider URLs

---

### User Story 3 - Handle Complex Kata Constraints (Priority: P3)

A developer wants to solve katas with specific coding constraints (e.g., "only one level of indentation per method", "no primitive types exposed", "no else keyword") and ensure the Refactorer agent enforces these rules.

**Why this priority**: Kata constraints teach specific design principles. However, basic TDD functionality is more critical than constraint enforcement for initial value.

**Independent Test**: Can be tested by running a kata with documented constraints (e.g., Object Calisthenics rules) and manually reviewing the final code to verify constraint adherence.

**Acceptance Scenarios**:

1. **Given** a kata description with explicit constraints listed, **When** the Refactorer agent improves code, **Then** all refactorings respect the documented constraints
2. **Given** code that violates a kata constraint, **When** the Refactorer evaluates it, **Then** it prioritizes fixing constraint violations in its refactoring pass
3. **Given** a constraint violation that cannot be fixed without breaking tests, **When** the Refactorer exhausts retry attempts, **Then** the Supervisor is notified with details about the constraint conflict

---

### User Story 4 - Support Multiple Programming Languages (Priority: P4)

A developer wants to solve katas in different programming languages (Rust, Python, TypeScript, Go, etc.) by simply specifying the target language or allowing auto-detection from kata file naming conventions.

**Why this priority**: Language flexibility greatly expands the tool's applicability, but demonstrating one language well is more valuable than partial support for many.

**Independent Test**: Can be tested by running the same kata description with different target languages and verifying each produces idiomatic, working code in that language.

**Acceptance Scenarios**:

1. **Given** a kata description and target language specified via CLI flag, **When** tool initializes, **Then** it creates appropriate project structure (e.g., cargo project for Rust, package.json for Node.js)
2. **Given** target language is not specified, **When** tool analyzes kata file name or content, **Then** it auto-detects the intended language and proceeds accordingly
3. **Given** a language without a registered runner, **When** tool attempts to initialize, **Then** it provides a clear error listing supported languages
4. **Given** language-specific build/test commands, **When** agents execute cycles, **Then** they use the correct toolchain for that language (cargo test, pytest, npm test, etc.)

---

### Edge Cases

- What happens when the Tester agent cannot produce a failing test after multiple attempts (kata may be complete)?
- What happens when the Implementer agent makes a test pass on first try that was supposed to fail (implementation overshoot detection)?
- How does the system handle test suite execution timeout (e.g., infinite loops in implementation)?
- What happens when the Refactorer breaks tests and exhausts all retry attempts?
- How does the tool handle malformed kata description files (missing constraints, ambiguous requirements)?
- What happens when the working directory already exists and contains files?
- How does the tool behave when max cycles is reached but kata is incomplete?
- What happens when API rate limits are hit mid-execution?
- How does the tool handle git conflicts if working directory is already a git repository?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a kata description file path (markdown format) as primary input
- **FR-002**: System MUST accept LLM provider name, model name, API key source, and optional base URL via CLI parameters
- **FR-003**: System MUST accept a working directory path where kata development will occur
- **FR-004**: System MUST accept a maximum cycle count to limit execution time
- **FR-005**: System MUST initialize a git repository in the working directory if one does not exist
- **FR-006**: System MUST implement four agent roles: Tester, Implementer, Refactorer, Supervisor
- **FR-007**: Tester agent MUST write a single failing unit test based on kata requirements
- **FR-008**: Tester agent MUST run tests to verify the new test fails before handing off
- **FR-009**: Tester agent MUST stage (not commit) the failing test
- **FR-010**: Implementer agent MUST modify code to make the failing test pass with minimal changes
- **FR-011**: Implementer agent MUST run full test suite to verify all tests pass
- **FR-012**: Implementer agent MUST commit both test and implementation when all tests are green
- **FR-013**: Refactorer agent MUST improve code quality (naming, structure, duplication) after tests pass
- **FR-014**: Refactorer agent MUST run tests after refactoring to ensure they remain green
- **FR-015**: Refactorer agent MUST commit successful refactorings or revert changes on test failure
- **FR-016**: Refactorer agent MUST attempt up to 3 retries before escalating to Supervisor
- **FR-017**: Supervisor agent MUST detect when Tester produces a test that already passes (implementation overshoot)
- **FR-018**: Supervisor agent MUST handle Implementer failures by suggesting simpler tests or preparatory refactoring
- **FR-019**: Supervisor agent MUST decide when to terminate execution (max cycles reached or no progress possible)
- **FR-020**: System MUST display real-time console output showing current agent, action, and test results
- **FR-021**: System MUST support pluggable language runners (starting with Rust, extensible to others)
- **FR-022**: System MUST initialize language-specific project structure if working directory is empty
- **FR-023**: System MUST execute language-specific build and test commands via language runners
- **FR-024**: System MUST generate commit messages that clearly describe TDD step (test/feat/refactor)
- **FR-025**: System MUST never commit code when tests are failing
- **FR-026**: System MUST read API credentials from environment variables with fallback to CLI parameter
- **FR-027**: System MUST support OpenAI-compatible API endpoints with custom base URLs
- **FR-028**: System MUST parse kata constraints from markdown description and pass to Refactorer agent
- **FR-029**: System MUST handle agent failures gracefully with clear error messages
- **FR-030**: System MUST log all agent actions and decisions for debugging and transparency

### Key Entities

- **Kata Description**: Markdown document containing problem statement, requirements, acceptance criteria, and optional coding constraints
- **Agent**: Autonomous component with specific TDD role (Tester/Implementer/Refactorer/Supervisor), LLM-backed decision making, and ability to execute commands
- **Language Runner**: Pluggable component that knows how to initialize projects, run tests, build code, and format/lint for a specific programming language
- **TDD Cycle**: One iteration through Tester → Implementer → Refactorer sequence, resulting in one or more commits
- **Working Directory**: File system location where kata code is developed, includes git repository, source files, test files, and build artifacts
- **LLM Provider Config**: Configuration specifying provider name, model name, API endpoint URL, and authentication credentials

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tool successfully completes a simple kata (e.g., FizzBuzz) from description to working code in under 15 TDD cycles
- **SC-002**: 100% of commits in generated git history have passing tests (no red commits)
- **SC-003**: Generated code passes all test cases defined during execution
- **SC-004**: Tool executes without manual intervention from start to completion (fully autonomous)
- **SC-005**: Console output provides clear visibility into which agent is active and what action is occurring within 2 seconds of each transition
- **SC-006**: Tool successfully works with at least 3 different OpenAI-compatible LLM providers without code changes
- **SC-007**: Supervisor agent successfully recovers from at least 80% of agent failures without terminating execution
- **SC-008**: Tool detects and reports implementation overshoot (test passing when it should fail) within 1 cycle of occurrence
- **SC-009**: Generated code follows language-specific formatting and linting standards (e.g., rustfmt for Rust)
- **SC-010**: Tool provides actionable error messages that allow users to fix configuration issues within 1 attempt

### Assumptions

- Users have git installed and available in PATH
- Users have the target language toolchain installed (e.g., Rust with cargo for Rust katas)
- Kata descriptions are well-formed markdown with clear requirements
- LLM providers return responses within reasonable timeouts (30 seconds typical)
- Working directory has write permissions and sufficient disk space
- Users understand basic TDD concepts and kata structure
- Initial implementation focuses on Rust; other languages added incrementally
- Default kata language is Rust if not specified
- Default max cycles is 15 if not specified
- Default working directory is ./agentic-tdd-output if not specified
