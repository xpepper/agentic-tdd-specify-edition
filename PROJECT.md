# Goal of `agentic-tdd`
I want to build a multi-agent Test-Driven Development (TDD) CLI tool (`agentic-tdd`) that is able to develop a code kata autonomously, following the classic TDD cycle, utilizing a user-supplied kata description. The final outcome, after a given amount of TDD steps, should be a codebase containing the code kata.

## First milestone
I want to be able to run the CLI tool (e.g. `agentic-tdd`) with a custom provided code kata in a markdown file, providing the selected OpenAI-compatible LLM provider (e.g. `perplexity`), their model (e.g. `sonar-pro`), their endpoint (e.g. `https://api.openai.com/v1/chat/completions`), and their API keys (supplied as env variables), and a working directory where the TDD process will take place.

The shape of the command may be something like:

```bash
agentic-tdd mars-rover-kata.md --model sonar-pro --provider perplexity --api-key $PERPLEXITY_API_KEY --work-dir /tmp/kata-output/ --base-url https://apis.iflow.cn/v1/  --max-cycles 15
```

Where:
- `mars-rover-kata.md` is the path to the code kata description file
- `sonar-pro` is the selected LLM model to use
- `perplexity` is the provider of the LLM model
- `$PERPLEXITY_API_KEY` is the API key to use for the LLM model
- `/tmp/kata-output/` is the working directory for the TDD process

## Process to follow to develop `agentic-tdd`
- I want to keep an up-to-date TODO list or backlog of the items we need to develop for `agentic-tdd`
- I want each small feature we add to `agentic-tdd` to be committed, instead of just batching a lot of changes. Before committing, run any quality check you think we should run (e.g. formatting, linting, testing).

## `agentic-tdd` requirements
There will be four agents involved in `agentic-tdd`, three core ones for each of the classical TDD roles (writing a new small test -> making it pass -> refactor the code -> repeat), and one for supervising the process and decide how to proceed when one of the core agent is stuck.

The overall flow for the core agents is to follow the TDD sequential flow:
- **Tester Agent:** Writes a small, failing unit test to capture the next required behavior to implement to fulfill the kata. It should be able to fully operate on the codebase, install needed dependencies, compile the code, run tests if needed. Then it will "hand the keyboard" to the implementor agent. The added test should fail, so the tester agent will run the test to verify that it is not passing before considering its step done. The tester may decide to git-stage the added test instead of committing, to avoid committing a broken test.
- **Implementer Agent:** Change the code to make the failing test pass using a minimal change required to implement the behavioural change needed. Then, once all the tests are passing, will commit the changes and "hand the keyboard" to the refactorer agent. It should be able to fully operate on the codebase, install needed dependencies, compile the code, run tests and commit.
- **Refactorer Agent:** Improves code understandability, readability, modularity, structure, and maintainability after all tests pass (e.g., splitting large functions, improving naming, make sure the code is composed of small functions / modules / classes with clear names and resposibilities). All the tests need to be passing after the refactor, so that it can commit the changes and then "hand the keyboard" again to the tester agent for the next test to add. The agent should be able to fully operate on the codebase, install needed dependencies, compile the code, run tests and commit.

Agents must operate in incremental TDD cycles: writing a failing test, implementing a simple passing solution, then refactoring.
Agents will communicate mainly via the actual codebase and the git commits produced for the changes, so that every agent can understand the changes done in the previous steps just by looking at the actual codebase and the git commits.

Agents may fail their step and communicate this to the supervisor:
- the *tester agent* could fail at writing a failing test (meaning the test written is already passing). In this case it should report to the supervisor and start adding a new test. The supervisor should take note of this by "penalizing" the implementor agent, that has written "too much code" compared to the one needed to just make the previous test pass.
- the *implementor agent* could fail at making the test pass. In this case it should communicate the reason of the failure to the supervisor agent, that will decide how to proceed (e.g. by requiring a preparatory refactoring to the refactorer agent)
- the *refactorer agent* could fail at making all the tests passing after the refactor. If this happens, it could retry doing the refactor up to a given number of retries (customizable, default: 3). In case of exhausting all the attempts, it will communicate the failure to the supervisor agent, that will decide how to proceed.

Each agent will be able to see and change the actual code and inspect the work done in the previous steps by looking at the actual code and their tests, and by looking at the previous git commits,

### Supervisor Agent
There is a fourth agent, the **Supervisor Agent:**, which oversees the TDD workflow, monitors agent progress, and intervenes if progress stalls (for example, by proposing simpler tests or preemptive refactoring if the Tester Agent cannot produce a viable test).

## Technical requirements
We could use *Python* as the language for the tool and *LangChain* as the lib for managing the agents.
For any of the agents we'll be using LLM providers via LangChain. It should be possible to use any LLM provider compatible with the OpenAI API standard.

## `agentic-tdd` configuration requirements
- I should be able to *feed the code kata description as a markdown file* (e.g. `fizz-buzz.md`, `mars-rover-kata.md`). This file contains the description of the kata and any specific kata constraint (e.g. "Only one level of indentation per method", "Wrap All Primitives And Strings", etc).
- I should be able to *use any LLM provider compatible with OpenAI API format* (e.g. deepseek, perplexity, iflow, ...).
- Related to this, I prefer not to put their API keys directly in the code or in the CLI, so it would be nice to be able to provide those *API keys as env variables* (e.g. `PERPLEXITY_API_KEY`)
- I want to be able to follow and watch the TDD steps (add a test, make it pass, refactor, add a new test, make it pass, etc) as they go, by looking at the CLI console.

## Nice to have, to be added to the future plan
- Integration with GitHub Copilot to select its models (e.g. Copilot GPT-5)

## Current Implementation Status

### ✅ Completed (MVP Feature-Complete)

1. **Multi-Agent Architecture**
   - ✅ Tester Agent (writes failing tests)
   - ✅ Implementer Agent (makes tests pass)
   - ✅ Refactorer Agent (improves code quality)
   - ✅ Supervisor Agent (orchestrates workflow)

2. **CLI Infrastructure**
   - ✅ Full argument parsing with Typer
   - ✅ Support for multiple LLM providers (OpenAI, Perplexity, DeepSeek, iFlow, custom)
   - ✅ Environment variable support for API keys
   - ✅ Configurable max-cycles, retries, timeouts
   - ✅ Rich console output with progress indicators

3. **Language Support**
   - ✅ Rust runner with cargo integration
   - ✅ Pluggable runner architecture for future languages

4. **Git Integration**
   - ✅ Automatic git repository initialization
   - ✅ Agent communication via commits
   - ✅ Clean commit history showing TDD progression

5. **Quality Gates**
   - ✅ Automated formatting (`cargo fmt`)
   - ✅ Linting (`cargo clippy`)
   - ✅ Test execution before commits
   - ✅ Retry logic for transient failures

### 🔧 Known Issues & Fixes

1. **Test Preservation Bug** (Fix Applied, Pending Validation)
   - **Issue**: Agents were replacing entire files, causing test loss across cycles
   - **Root Cause**: `file.write_text()` overwrites + insufficient LLM instructions
   - **Fix**: Enhanced prompts with CRITICAL preservation instructions (commit `101bd65`)
   - **Status**: ⏳ Awaiting validation with live kata run
   - **Documentation**: See `VALIDATION.md` for full details and validation guide
   - **Alternative Solutions**: AST-based merging, diff-based editing, append-only mode

### 🚧 In Progress

1. **Real-World Testing**
   - Testing with various katas (FizzBuzz, Battleships, Mars Rover)
   - Validation of test preservation fix
   - LLM behavior assessment across different providers

### 📋 Not Yet Started

1. **Additional Language Support**
   - Python runner
   - JavaScript/TypeScript runner
   - Other languages as needed

2. **Enhanced Supervisor Intelligence**
   - Detecting when to suggest simpler tests
   - Preemptive refactoring recommendations
   - Better stall detection and recovery

3. **Documentation**
   - Comprehensive developer documentation
   - Architecture diagrams
   - Contributing guidelines

4. **Testing**
   - Unit tests for agents
   - Integration tests for workflows
   - Mock LLM for deterministic testing

## Next Immediate Steps

1. **Validate test preservation fix** (requires API access)
   - Run multi-cycle kata with working API key
   - Verify tests accumulate without loss
   - Document results in `VALIDATION.md`

2. **Based on validation results**:
   - If fix works: Mark as resolved, continue testing phase
   - If fix fails: Implement AST-based merging strategy

3. **Continue real-world testing**
   - Test with various kata complexities
   - Document LLM behavior patterns
   - Tune prompts and retry logic as needed

