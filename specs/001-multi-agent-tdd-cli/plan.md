# Implementation Plan: Multi-Agent TDD CLI Tool

**Branch**: `001-multi-agent-tdd-cli` | **Date**: 2025-11-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-multi-agent-tdd-cli/spec.md`

## Summary

Build an autonomous multi-agent TDD CLI tool that accepts a kata description (markdown) and produces a complete, tested solution through iterative red-green-refactor cycles. Four specialized LLM agents (Tester, Implementer, Refactorer, Supervisor) collaborate via code and git commits. The tool supports pluggable language runners (starting with Rust), configurable LLM providers (OpenAI-compatible APIs), and enforces strict TDD discipline with no red commits.

**Technical Approach**: Python-based CLI using LangChain for agent orchestration. Agents have full codebase access and execute shell commands (build, test, git operations). Token efficiency achieved through git-based communication rather than verbose inter-agent messages. Language runners provide abstraction for multi-language support.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: LangChain (agent orchestration), Typer (CLI framework), GitPython or subprocess (git operations), Rich (console output), Pydantic (data validation)  
**Storage**: File system (kata working directory), git repository (version control and agent communication)  
**Testing**: pytest (tool development), language-specific runners for kata execution (cargo test for Rust MVP)  
**Target Platform**: macOS/Linux CLI (Python 3.11+ with git and target language toolchain installed)  
**Project Type**: Single project (CLI tool)  
**Performance Goals**: Complete simple kata (FizzBuzz) in <15 TDD cycles, agent transition latency <2 seconds, LLM response timeout 30 seconds  
**Constraints**: Token-efficient prompts (full codebase access per agent), autonomous execution (no manual intervention), 100% green commits (no red state commits)  
**Scale/Scope**: MVP supports single language (Rust), 3+ LLM providers, typical kata complexity 50-500 LOC, 5-20 TDD cycles

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Test-First Development ✅

**Compliance**: 
- FR-007, FR-008: Tester agent writes and verifies failing tests before handoff
- FR-009: Tests staged (not committed) until implementation passes
- FR-017: Supervisor detects implementation overshoot (test passing prematurely)

**Design Alignment**: Agent workflow enforces strict red state verification before proceeding.

### Principle II: Incremental Implementation ✅

**Compliance**:
- FR-010: Implementer makes minimal changes to pass current test
- FR-017: Supervisor penalizes overshoot behavior

**Design Alignment**: Implementer agent prompt emphasizes "minimal change" constraint.

### Principle III: Refactoring Discipline ✅

**Compliance**:
- FR-013, FR-014: Refactorer improves quality while maintaining green state
- FR-015, FR-016: Up to 3 retries before escalation, commit on success or revert

**Design Alignment**: Refactorer agent has bounded retry logic and quality improvement focus areas.

### Principle IV: Git Commit Hygiene ✅

**Compliance**:
- FR-025: Never commit failing tests
- FR-012: Implementer commits test + code together when green
- FR-024: Conventional commit messages (test:/feat:/refactor:)

**Design Alignment**: Git operations gated by test suite status checks.

### Principle V: Agent Autonomy & Communication ✅

**Compliance**:
- User input specifies: "Agents communicate mainly via actual codebase and git commits"
- FR-006: Four agent roles with specific responsibilities
- FR-029: Graceful failure handling with escalation

**Design Alignment**: Agents read codebase + git history for context, minimal inter-agent messaging.

### Principle VI: Code Quality Standards ✅

**Compliance**:
- FR-023: Language-specific build/test commands
- SC-009: Generated code follows formatting/linting standards
- Quality gates implicit in language runner interface

**Design Alignment**: Language runners enforce format/lint/build checks before commits.

### Principle VII: Language-Agnostic Design ✅

**Compliance**:
- FR-021: Pluggable language runners
- FR-022: Language-specific project initialization
- FR-023: Language-specific build/test commands

**Design Alignment**: Runner abstraction separates language concerns from agent logic.

**GATE STATUS**: ✅ **PASSED** - All constitutional principles satisfied by design.

## Project Structure

### Documentation (this feature)

```text
specs/001-multi-agent-tdd-cli/
├── plan.md              # This file
├── research.md          # Phase 0: LangChain patterns, multi-agent best practices
├── data-model.md        # Phase 1: Agent, Runner, Config, TDDCycle entities
├── quickstart.md        # Phase 1: Installation and first kata execution
├── contracts/           # Phase 1: Agent interfaces, Runner protocol
└── checklists/
    └── requirements.md  # Spec quality validation (complete)
```

### Source Code (repository root)

```text
agentic_tdd/
├── __init__.py
├── __main__.py          # CLI entry point
├── cli.py               # Typer CLI command definitions
├── config.py            # Configuration parsing (CLI args + env vars)
├── agents/
│   ├── __init__.py
│   ├── base.py          # Base agent class
│   ├── tester.py        # Tester agent implementation
│   ├── implementer.py   # Implementer agent implementation
│   ├── refactorer.py    # Refactorer agent implementation
│   └── supervisor.py    # Supervisor agent orchestration
├── runners/
│   ├── __init__.py
│   ├── base.py          # Language runner interface
│   └── rust.py          # Rust runner (cargo commands)
├── llm/
│   ├── __init__.py
│   ├── provider.py      # OpenAI-compatible provider abstraction
│   └── prompts.py       # Agent system prompts
├── models/
│   ├── __init__.py
│   ├── kata.py          # Kata description parsing
│   ├── cycle.py         # TDD cycle state tracking
│   └── result.py        # Agent execution results
├── utils/
│   ├── __init__.py
│   ├── git.py           # Git operations (init, stage, commit, revert)
│   ├── shell.py         # Shell command execution with streaming
│   └── logging.py       # Structured logging configuration
└── templates/
    └── prompts/         # LangChain prompt templates

tests/
├── unit/                # Unit tests for components
├── integration/         # Integration tests (agent workflows)
└── fixtures/            # Sample kata descriptions

pyproject.toml           # Poetry/setuptools configuration
README.md                # Project overview and quickstart
Makefile                 # Development tasks (fmt, lint, test)
```

**Structure Decision**: Single project structure selected. This is a standalone CLI tool without web/mobile components. All code organized under `agentic_tdd/` package with clear separation of concerns:
- `agents/`: LLM-backed agent implementations
- `runners/`: Language-specific execution adapters
- `llm/`: Provider abstraction and prompts
- `models/`: Data structures and parsing
- `utils/`: Cross-cutting utilities (git, shell, logging)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected** - Constitution Check passed all gates.

---

## Phase 0: Research

### Research Tasks

1. **LangChain Multi-Agent Patterns**: Research best practices for orchestrating multiple LangChain agents with minimal inter-agent message passing
2. **Token Optimization Strategies**: Investigate techniques for reducing token usage while giving agents full codebase context
3. **Git-Based Agent Communication**: Research patterns for using git commits and file system as primary communication channel
4. **OpenAI-Compatible Provider Support**: Identify LangChain patterns for supporting multiple OpenAI-compatible providers
5. **Shell Command Execution from Agents**: Research secure patterns for LangChain agents executing shell commands with output streaming
6. **Rust Language Runner**: Determine cargo commands for init, test, build, format, lint operations
7. **Agent Failure Recovery**: Research supervisor patterns for detecting and recovering from agent failures

### Phase 0 Status: ✅ COMPLETE

**Deliverable**: `research.md` - 8 technical decisions resolved (agent orchestration, token optimization, git communication, LLM providers, shell execution, Rust runner, failure recovery, prompt engineering)

---

## Phase 1: Design & Contracts

### Design Tasks

1. **Data Model Definition**: Define entities (KataDescription, AgentContext, TDDCycle, LLMProviderConfig, TestResult, etc.)
2. **Contract Specification**: Document interfaces for agents and language runners
3. **User Documentation**: Create quickstart guide with installation and first kata

### Phase 1 Status: ✅ COMPLETE

**Deliverables**:
- `data-model.md` - 8 model sections covering configuration, kata representation, cycle tracking, agent execution, and language runners (45+ entity definitions)
- `contracts/language_runner.md` - LanguageRunner interface with Rust and Python examples, factory pattern, quality gate sequence
- `contracts/agent_interface.md` - Agent base class, role-specific contracts (Tester, Implementer, Refactorer, Supervisor), execution protocol
- `quickstart.md` - Installation guide, FizzBuzz walkthrough, CLI reference, troubleshooting
- `AGENTS.md` updated with Python 3.11+ and tech stack

---

## Phase 2: Task Breakdown

**Next Step**: Generate `tasks.md` organized by user stories (P1 → P2 → P3 → P4)

Run the task generation command or use `/speckit.tasks` to create detailed task breakdown based on:
- User stories from spec.md
- Technical decisions from research.md
- Data models and contracts from Phase 1
- Constitution compliance requirements

Tasks should be:
- Independent and testable
- Ordered by priority (P1 MVP first)
- Estimated with complexity points
- Mapped to specific modules/files

### Phase 2 Status: ✅ COMPLETE

**Deliverable**: `tasks.md` - 70 tasks organized into 7 phases:
- **Phase 1 (Setup)**: 5 tasks - Project initialization
- **Phase 2 (Foundational)**: 12 tasks - Core infrastructure (BLOCKS all user stories)
- **Phase 3 (US1 - MVP)**: 15 tasks - Execute basic kata with Rust
- **Phase 4 (US2)**: 7 tasks - Configure LLM provider/model
- **Phase 5 (US3)**: 7 tasks - Handle kata constraints
- **Phase 6 (US4)**: 7 tasks - Multi-language support
- **Phase 7 (Polish)**: 17 tasks - Production readiness

**MVP Scope**: 32 tasks (Phases 1-3)
**Parallel Opportunities**: 18 tasks marked [P]
**Constitution Compliance**: All tasks mapped to principles (TDD, git hygiene, quality gates, language-agnostic)

---

## Next Steps: Implementation

With planning complete, proceed to implementation:

1. **Start with MVP** (Phases 1-3): 32 tasks focusing on User Story 1
2. **Validate independently**: Test FizzBuzz kata execution end-to-end
3. **Iterate incrementally**: Add US2, US3, US4 as independent enhancements
4. **Polish for production**: Complete Phase 7 for deployment readiness

**Recommended approach**: Follow tasks.md execution order, commit after each task, stop at checkpoints to validate
