<!--
SYNC IMPACT REPORT
==================
Version Change: INITIAL → 1.0.0
Modified Principles: N/A (initial version)
Added Sections:
  - Core Principles (7 principles)
  - Quality Gates
  - Development Workflow
  - Governance
Removed Sections: N/A
Templates Status:
  ✅ plan-template.md - Constitution Check section aligns with principles
  ✅ spec-template.md - User story structure supports independent testing (P3)
  ✅ tasks-template.md - Task phases align with TDD cycle and testing discipline
Follow-up TODOs: None - all placeholders filled
==================
-->

# Agentic-TDD Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)

**TDD cycle MUST be strictly enforced across all agents:**

- Tests MUST be written before implementation code
- Each test MUST fail (red state) before implementation begins
- Implementation proceeds ONLY after test failure is verified
- The Tester agent MUST run tests to confirm red state before staging
- If a newly written test passes immediately, this signals implementation overshoot and MUST be reported to the Supervisor

**Rationale**: Test-first discipline ensures behavioral clarity, prevents gold-plating, and enables the multi-agent system to validate progress objectively at each step.

### II. Incremental Implementation

**The Implementer agent MUST make the minimal change required to pass the failing test:**

- No speculative features or "nice to have" additions
- Implementation focuses solely on satisfying the current test
- Overly broad implementations that cause future tests to pass prematurely are violations
- The Supervisor penalizes implementation overshoot to maintain discipline

**Rationale**: Minimal increments keep the codebase aligned with test coverage, prevent scope creep, and maintain clear agent handoffs.

### III. Refactoring Discipline

**The Refactorer agent MUST improve code quality while preserving all test outcomes:**

- Refactoring occurs ONLY after all tests pass (green state)
- Tests MUST remain green throughout refactoring
- Focus areas: readability, naming, modularity, structure, adherence to kata constraints
- Up to 3 retry attempts allowed; escalate to Supervisor on persistent failure
- Commit on success; revert on exhaustion of retries

**Quality targets:**
- Small functions/methods with clear responsibilities
- Descriptive names (no abbreviations unless domain-standard)
- Single level of indentation per method (when kata constraint applies)
- No code duplication
- Clear separation of concerns

**Rationale**: Refactoring maintains long-term code health without risking behavioral regressions. Bounded retries prevent infinite loops.

### IV. Git Commit Hygiene (NON-NEGOTIABLE)

**Commits MUST reflect clean, stable states:**

- **NEVER commit red builds** (failing tests)
- Tester agent stages tests but does NOT commit until implementation succeeds
- Implementer agent commits test + implementation together when green
- Refactorer agent commits refactorings that maintain green state
- Commit messages MUST be descriptive and follow conventional format:
  - `test: add test for [behavior]`
  - `feat: implement [behavior] to pass [test]`
  - `refactor: improve [aspect] in [component]`

**Rationale**: Clean git history enables agents to understand prior work via commit log. Red commits break agent trust and workflow integrity.

### V. Agent Autonomy & Communication

**Agents communicate primarily through code and git artifacts:**

- Each agent reads current codebase state and git history to understand context
- Agents MUST have full access to:
  - Install dependencies (e.g., `cargo add`, `pip install`)
  - Compile/build code
  - Run tests
  - Stage and commit changes
- Minimal inter-agent messaging; prefer observable actions (commits, test results)
- Supervisor receives failure reports and orchestrates recovery

**Failure escalation:**
- Tester: Test passes immediately → Report overshoot, write different test
- Implementer: Cannot make test pass → Report to Supervisor with reason
- Refactorer: Cannot maintain green after 3 attempts → Report to Supervisor

**Rationale**: Explicit code/git communication reduces coordination overhead and creates an auditable, deterministic workflow.

### VI. Code Quality Standards

**All code MUST meet baseline quality criteria:**

- **Compilation**: Code MUST compile/parse without errors before commit
- **Testing**: Full test suite MUST pass before commit
- **Formatting**: Code MUST be formatted according to language conventions (e.g., `rustfmt`, `black`, `prettier`)
- **Linting**: Code MUST pass linter checks (e.g., `clippy`, `ruff`, `eslint`)
- **Type Safety**: When applicable, code MUST satisfy type checker (e.g., `mypy`, TypeScript)
- **Documentation**: Public functions/modules MUST have docstrings/comments explaining purpose

**Quality gates run before each commit:**
1. Format check
2. Lint check
3. Type check (if applicable)
4. Full test suite
5. Build/compile verification

**Rationale**: Automated quality gates prevent technical debt accumulation and ensure consistent code standards across agent iterations.

### VII. Language-Agnostic Design

**The tool architecture MUST support multiple programming languages via pluggable runners:**

- Initial implementation supports Rust (`cargo test`, `cargo build`, `cargo fmt`, `cargo clippy`)
- Runners abstracted behind common interface:
  - `initialize_project()`: Setup project structure if needed
  - `run_tests()`: Execute test suite, capture results
  - `format_code()`: Apply language-specific formatting
  - `lint_code()`: Run language-specific linter
  - `build()`: Compile/build if applicable
- Kata description files are language-agnostic markdown
- Future language support (Python, TypeScript, Go, etc.) requires only new runner implementation

**Rationale**: Language-agnostic design maximizes tool utility and ensures the TDD methodology applies universally.

## Quality Gates

**Every commit MUST pass these gates (enforced by agents before committing):**

| Gate | Tool/Command | Failure Action |
|------|--------------|----------------|
| Format | `cargo fmt --check` (Rust) | Auto-format, re-verify |
| Lint | `cargo clippy` (Rust) | Fix issues, re-verify |
| Type Check | Language-specific (e.g., `mypy`) | Fix type errors, re-verify |
| Test Suite | `cargo test` (Rust) | Implementer: fix until green; Refactorer: revert on exhaustion |
| Build | `cargo build` (Rust) | Fix compilation errors, re-verify |

**Gate exemptions**: None. All agents MUST pass all applicable gates.

## Development Workflow

**Workflow for developing the `agentic-tdd` tool itself:**

1. **Feature Specification**: Document requirements in spec.md (user stories, acceptance criteria)
2. **Implementation Planning**: Create plan.md with technical context, structure, constitution check
3. **Task Breakdown**: Generate tasks.md organized by user story (independent, testable slices)
4. **Incremental Development**:
   - Write tests for one user story
   - Implement to pass tests
   - Refactor for quality
   - Commit after each logical unit
   - Run quality gates before each commit
5. **Independent Testing**: Each user story MUST be testable in isolation
6. **Iterative Delivery**: MVP first (P1 user story), then incremental additions (P2, P3, ...)

**Workflow for `agentic-tdd` CLI tool executing katas:**

1. **Initialization**: Parse kata markdown, setup work directory, initialize git repo
2. **TDD Cycle** (repeat until kata complete or max cycles reached):
   - **Tester**: Write next failing test, verify red, stage (do not commit)
   - **Implementer**: Make test pass minimally, verify green, commit test + implementation
   - **Refactorer**: Improve code quality, maintain green, commit or revert
   - **Supervisor**: Monitor progress, handle failures, decide continuation
3. **Completion**: Stop when no new failing tests can be produced or max cycles reached
4. **Output**: Git repository with complete kata implementation and clean commit history

## Governance

**Constitution authority:**
- This constitution supersedes all other development practices
- All agent behaviors MUST comply with these principles
- Violations require documented justification and Supervisor approval

**Amendment process:**
1. Propose amendment with rationale and impact analysis
2. Document in Sync Impact Report (version change, affected sections, template updates)
3. Update dependent templates (plan-template.md, spec-template.md, tasks-template.md)
4. Increment version according to semantic versioning:
   - **MAJOR**: Backward-incompatible principle removal/redefinition
   - **MINOR**: New principle or materially expanded guidance
   - **PATCH**: Clarifications, wording fixes, non-semantic refinements
5. Update all references in project documentation

**Compliance verification:**
- All feature plans MUST include "Constitution Check" section verifying alignment
- Code reviews MUST verify agent behaviors comply with principles
- Quality gates MUST be automated and enforced before commits
- Supervisor agent MUST enforce TDD cycle and escalation protocols

**Version**: 1.0.0 | **Ratified**: 2025-11-10 | **Last Amended**: 2025-11-10
