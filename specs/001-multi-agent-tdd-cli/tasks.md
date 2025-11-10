# Tasks: Multi-Agent TDD CLI Tool

**Input**: Design documents from `/specs/001-multi-agent-tdd-cli/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single project structure at repository root:
- `agentic_tdd/` - Main package
- `tests/` - Test suite
- `pyproject.toml` - Poetry configuration

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure per plan.md (agentic_tdd/, tests/, docs/)
- [ ] T002 Initialize Python project with pyproject.toml (Poetry configuration)
- [ ] T003 [P] Configure development tools in Makefile (fmt, lint, test, install commands)
- [ ] T004 [P] Add .gitignore for Python artifacts
- [ ] T005 [P] Install core dependencies via Poetry: langchain-openai, typer, gitpython, rich, pydantic

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create configuration models in agentic_tdd/models/config.py (LLMProviderConfig, ToolConfig with Pydantic validation)
- [ ] T007 Create kata models in agentic_tdd/models/kata.py (KataDescription, KataConstraint with markdown parser)
- [ ] T008 [P] Create cycle tracking models in agentic_tdd/models/cycle.py (TDDPhase, CycleState, SessionState)
- [ ] T009 [P] Create agent models in agentic_tdd/models/agent.py (AgentRole, AgentContext, AgentResult)
- [ ] T010 [P] Create runner models in agentic_tdd/models/runner.py (TestResult, CommandResult, QualityGateResult)
- [ ] T011 Implement shell command execution utility in agentic_tdd/utils/shell.py (run_command with streaming and timeout)
- [ ] T012 [P] Implement git operations utility in agentic_tdd/utils/git.py (init, add, commit, revert, log operations)
- [ ] T013 [P] Implement logging configuration in agentic_tdd/utils/logging.py (Rich console logging with cycle/agent context)
- [ ] T014 Create LanguageRunner abstract base class in agentic_tdd/runners/base.py (interface per contracts/language_runner.md)
- [ ] T015 Create Agent abstract base class in agentic_tdd/agents/base.py (interface per contracts/agent_interface.md)
- [ ] T016 Implement LLM provider factory in agentic_tdd/llm/provider.py (ChatOpenAI with provider URL mapping)
- [ ] T017 [P] Create agent system prompts in agentic_tdd/llm/prompts.py (Tester, Implementer, Refactorer role-specific prompts)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Execute Basic Kata with Rust (Priority: P1) 🎯 MVP

**Goal**: Autonomous TDD execution for a single kata using Rust as target language

**Independent Test**: Run CLI with FizzBuzz kata markdown, verify working Rust solution with clean git history showing TDD cycles

### Implementation for User Story 1

- [ ] T018 [US1] Implement RustRunner in agentic_tdd/runners/rust.py (cargo init, test, build, fmt, clippy per contracts/language_runner.md)
- [ ] T019 [US1] Create runner factory in agentic_tdd/runners/__init__.py (get_runner function mapping language names to runner classes)
- [ ] T020 [US1] Implement TesterAgent in agentic_tdd/agents/tester.py (write failing test, verify red state, stage file)
- [ ] T021 [US1] Implement ImplementerAgent in agentic_tdd/agents/implementer.py (minimal implementation, verify green, commit test+code)
- [ ] T022 [US1] Implement RefactorerAgent in agentic_tdd/agents/refactorer.py (quality improvements, maintain green, bounded retries)
- [ ] T023 [US1] Implement SupervisorAgent in agentic_tdd/agents/supervisor.py (orchestrate cycle, handle failures, decide continuation)
- [ ] T024 [US1] Implement CLI command structure in agentic_tdd/cli.py (Typer app with run command)
- [ ] T025 [US1] Implement CLI entry point in agentic_tdd/__main__.py (poetry script entry)
- [ ] T026 [US1] Implement session orchestration logic in SupervisorAgent.run_session (initialize, cycle loop, completion detection)
- [ ] T027 [US1] Add agent execution with retry logic in agentic_tdd/agents/base.py (_execute_with_retry helper method)
- [ ] T028 [US1] Add console output formatting in agentic_tdd/cli.py (Rich progress indicators, cycle headers, agent status)
- [ ] T029 [US1] Add quality gate execution before commits in ImplementerAgent and RefactorerAgent (format, lint, test, build sequence)
- [ ] T030 [US1] Add overshoot detection in TesterAgent.execute (test passes immediately → report to supervisor)
- [ ] T031 [US1] Add failure recovery heuristics in SupervisorAgent (handle_tester_overshoot, handle_implementer_failure, handle_refactorer_failure)
- [ ] T032 [US1] Add session completion logic in SupervisorAgent (max cycles reached, no new tests, kata complete detection)

**Checkpoint**: At this point, User Story 1 should be fully functional - can execute FizzBuzz kata autonomously with Rust

---

## Phase 4: User Story 2 - Configure LLM Provider and Model (Priority: P2)

**Goal**: Flexible LLM provider/model selection via CLI with environment variable API key support

**Independent Test**: Run same kata with different providers (OpenAI, Perplexity, DeepSeek) and verify equivalent results

### Implementation for User Story 2

- [ ] T033 [US2] Add CLI parameters to agentic_tdd/cli.py run command (--provider, --model, --api-key, --base-url flags)
- [ ] T034 [US2] Implement environment variable resolution in agentic_tdd/config.py (provider-specific env vars, fallback to generic)
- [ ] T035 [US2] Add provider validation in agentic_tdd/llm/provider.py (supported providers list, clear error messages)
- [ ] T036 [US2] Add custom base URL support in agentic_tdd/llm/provider.py (override default provider URLs)
- [ ] T037 [US2] Add API key validation and error handling in agentic_tdd/config.py (detect missing/invalid credentials)
- [ ] T038 [US2] Update LLMProviderConfig model validation in agentic_tdd/models/config.py (enforce custom provider requires base_url)
- [ ] T039 [US2] Add provider configuration display in CLI startup output (show provider, model, base URL being used)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - can switch providers seamlessly

---

## Phase 5: User Story 3 - Handle Complex Kata Constraints (Priority: P3)

**Goal**: Parse and enforce kata-specific coding constraints during refactoring phase

**Independent Test**: Run kata with Object Calisthenics constraints, verify final code adheres to all rules

### Implementation for User Story 3

- [ ] T040 [US3] Extend KataDescription parser in agentic_tdd/models/kata.py (parse constraints section from markdown)
- [ ] T041 [US3] Add constraint extraction to KataDescription.from_markdown (## Constraints heading → list of KataConstraint objects)
- [ ] T042 [US3] Update AgentContext in agentic_tdd/models/agent.py (include kata_constraints field)
- [ ] T043 [US3] Update RefactorerAgent system prompt in agentic_tdd/llm/prompts.py (include constraint enforcement instructions)
- [ ] T044 [US3] Update RefactorerAgent user prompt in agentic_tdd/agents/refactorer.py (_build_user_prompt includes constraints)
- [ ] T045 [US3] Add constraint validation logic in RefactorerAgent (prioritize fixing violations in refactoring pass)
- [ ] T046 [US3] Add constraint violation reporting in SupervisorAgent (detect unresolvable constraint conflicts)

**Checkpoint**: All constraints from kata description are enforced during refactoring

---

## Phase 6: User Story 4 - Support Multiple Programming Languages (Priority: P4)

**Goal**: Pluggable language support starting with Python, extensible to TypeScript/Go

**Independent Test**: Run same kata with --language python and --language rust, verify both produce idiomatic working code

### Implementation for User Story 4

- [ ] T047 [P] [US4] Implement PythonRunner in agentic_tdd/runners/python.py (poetry init, pytest, black, ruff, mypy per contracts/language_runner.md)
- [ ] T048 [P] [US4] Add language detection logic in agentic_tdd/config.py (auto-detect from kata filename or content if not specified)
- [ ] T049 [US4] Update runner factory in agentic_tdd/runners/__init__.py (register PythonRunner, add supported_languages function)
- [ ] T050 [US4] Add --language CLI parameter in agentic_tdd/cli.py (enum of supported languages, default to rust)
- [ ] T051 [US4] Update project initialization in SupervisorAgent (call runner.initialize_project with language-specific setup)
- [ ] T052 [US4] Add language-specific error messages in runner factory (list supported languages if unsupported requested)
- [ ] T053 [US4] Update console output in agentic_tdd/cli.py (display selected language in startup banner)

**Checkpoint**: All user stories should now be independently functional with multi-language support

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T054 [P] Create README.md with project overview, installation, and quickstart reference
- [ ] T055 [P] Add command timeout configuration in agentic_tdd/models/config.py (ToolConfig.command_timeout field, default 30s)
- [ ] T056 [P] Add max retries configuration in CLI (--max-retries flag, default 3)
- [ ] T057 [P] Add verbose logging flag in CLI (--verbose flag, adjust logging level)
- [ ] T058 Add graceful interruption handling in SupervisorAgent (Ctrl+C → save state, allow resume)
- [ ] T059 Add resume detection in SupervisorAgent.run_session (detect existing git repo, continue from last cycle)
- [ ] T060 [P] Add kata description validation in agentic_tdd/models/kata.py (detect malformed markdown, missing sections)
- [ ] T061 [P] Add working directory validation in agentic_tdd/config.py (handle existing files, git conflicts)
- [ ] T062 Add LLM timeout and rate limit handling in agentic_tdd/llm/provider.py (retry on timeout, backoff on rate limits)
- [ ] T063 [P] Create FizzBuzz example kata in examples/katas/fizzbuzz.md
- [ ] T064 [P] Create Roman Numerals example kata in examples/katas/roman-numerals.md
- [ ] T065 [P] Add unit tests for models in tests/unit/test_models.py (Pydantic validation coverage)
- [ ] T066 [P] Add unit tests for utilities in tests/unit/test_utils.py (shell, git, logging)
- [ ] T067 [P] Add integration test for full kata execution in tests/integration/test_fizzbuzz_e2e.py
- [ ] T068 Validate quickstart.md instructions (manual walkthrough of installation and first kata)
- [ ] T069 Add error handling documentation in docs/errors.md (common errors and solutions)
- [ ] T070 Add extending guide in docs/extending.md (how to add new language runners)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3 → P4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Extends US1 CLI/config but independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - Extends US1 Refactorer but independently testable
- **User Story 4 (P4)**: Can start after Foundational (Phase 2) - Extends US1 runners but independently testable

### Within Each User Story

- Models before services/agents
- Utilities before agents that use them
- Base classes before concrete implementations
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- **Phase 1 Setup**: T003, T004, T005 can run in parallel
- **Phase 2 Foundational**: T008-T010, T012-T013, T017 can run in parallel after T006-T007
- **Phase 6 User Story 4**: T047 (PythonRunner) can run in parallel with T048-T049
- **Phase 7 Polish**: T054-T057, T060-T061, T063-T064, T065-T066 can run in parallel
- **Entire User Stories**: US1, US2, US3, US4 can be worked on in parallel by different team members after Phase 2

---

## Parallel Example: Foundational Phase

```bash
# After T006-T007 complete, launch in parallel:
Task: "T008 Create cycle tracking models in agentic_tdd/models/cycle.py"
Task: "T009 Create agent models in agentic_tdd/models/agent.py"
Task: "T010 Create runner models in agentic_tdd/models/runner.py"

# Then launch utilities in parallel:
Task: "T012 Implement git operations utility in agentic_tdd/utils/git.py"
Task: "T013 Implement logging configuration in agentic_tdd/utils/logging.py"
Task: "T017 Create agent system prompts in agentic_tdd/llm/prompts.py"
```

## Parallel Example: User Story 4

```bash
# Language runners can be developed in parallel:
Task: "T047 Implement PythonRunner in agentic_tdd/runners/python.py"
# (RustRunner already exists from US1)

# Factory and detection logic:
Task: "T048 Add language detection logic in agentic_tdd/config.py"
Task: "T049 Update runner factory in agentic_tdd/runners/__init__.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T005)
2. Complete Phase 2: Foundational (T006-T017) - CRITICAL
3. Complete Phase 3: User Story 1 (T018-T032)
4. **STOP and VALIDATE**: Test with FizzBuzz kata independently
5. Deploy/demo MVP

**Estimated MVP**: 32 tasks, ~40-60 hours of development

### Incremental Delivery

1. **Foundation** (Phase 1-2): Setup + Foundational → ~15 tasks → Core infrastructure ready
2. **MVP** (+ Phase 3): Add US1 → +15 tasks → Working Rust kata solver!
3. **Provider Flexibility** (+ Phase 4): Add US2 → +7 tasks → Multi-provider support
4. **Constraint Enforcement** (+ Phase 5): Add US3 → +7 tasks → Advanced refactoring
5. **Multi-Language** (+ Phase 6): Add US4 → +7 tasks → Python support
6. **Production Ready** (+ Phase 7): Polish → +17 tasks → Complete tool

### Parallel Team Strategy

With multiple developers after Phase 2 complete:

- **Developer A**: User Story 1 (T018-T032) - Core TDD workflow
- **Developer B**: User Story 2 (T033-T039) - Provider configuration  
- **Developer C**: User Story 3 (T040-T046) - Constraint handling
- **Developer D**: User Story 4 (T047-T053) - Python runner

Stories complete and integrate independently.

---

## Task Count Summary

- **Phase 1 (Setup)**: 5 tasks
- **Phase 2 (Foundational)**: 12 tasks (BLOCKS all user stories)
- **Phase 3 (US1 - MVP)**: 15 tasks
- **Phase 4 (US2)**: 7 tasks
- **Phase 5 (US3)**: 7 tasks
- **Phase 6 (US4)**: 7 tasks
- **Phase 7 (Polish)**: 17 tasks

**Total**: 70 tasks

**MVP Scope** (Recommended): Phase 1 + Phase 2 + Phase 3 = 32 tasks

**Parallel Opportunities**: 18 tasks marked [P] can run in parallel with other tasks in same phase

---

## Success Criteria Mapping

Tasks mapped to success criteria from spec.md:

- **SC-001** (Complete FizzBuzz in <15 cycles): T018-T032 (US1 implementation)
- **SC-002** (100% green commits): T029 (quality gates), T012 (git operations)
- **SC-003** (All tests pass): T018 (RustRunner test execution)
- **SC-004** (Fully autonomous): T023-T032 (Supervisor orchestration)
- **SC-005** (Clear console output): T028 (Rich formatting)
- **SC-006** (3+ LLM providers): T033-T039 (US2 provider config)
- **SC-007** (80% failure recovery): T031 (Supervisor recovery heuristics)
- **SC-008** (Overshoot detection): T030 (TesterAgent overshoot check)
- **SC-009** (Language formatting): T029 (quality gates with fmt/lint)
- **SC-010** (Actionable errors): T037 (API key validation), T035 (provider validation)

---

## Notes

- **[P] tasks**: Different files, no dependencies, can run in parallel
- **[US#] label**: Maps task to specific user story for traceability
- **Tests not included**: Spec does not explicitly request TDD for tool development itself
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **Constitution compliance**: All agents follow TDD principles (T020-T022), git hygiene (T029, T012), quality gates (T029), language-agnostic design (T014, T018, T047)

---

**Version**: 1.0.0 | **Generated**: 2025-11-10 | **Status**: Ready for implementation
