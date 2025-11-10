# Agentic TDD

Autonomous multi-agent TDD CLI tool for kata solving.

## Overview

Agentic TDD is a command-line tool that autonomously solves programming katas using Test-Driven Development (TDD). Four specialized LLM agents collaborate to write tests, implement code, and refactor solutions following strict TDD principles.

## Features

- **Autonomous TDD Execution**: Fully automated red-green-refactor cycles
- **Multi-Agent Architecture**: Tester, Implementer, Refactorer, and Supervisor agents
- **Language Support**: Rust (MVP), with pluggable runner architecture
- **LLM Provider Flexibility**: OpenAI-compatible API support
- **Git-Based Communication**: Clean commit history showing TDD progression
- **Quality Gates**: Automated formatting, linting, and testing before commits

## Installation

### Prerequisites

- Python 3.11+
- Poetry
- Git
- Rust toolchain (for Rust katas)
- OpenAI-compatible API key

### Install from Source

```bash
git clone <repository-url>
cd agentic-tdd-specify-edition
poetry install
```

## Quick Start

### Basic Usage

```bash
# Run a kata with default settings (Rust, OpenAI GPT-4)
export OPENAI_API_KEY=your-api-key
poetry run agentic-tdd run katas/fizzbuzz.md

# Or specify API key directly
poetry run agentic-tdd run katas/fizzbuzz.md --api-key your-api-key
```

### CLI Reference

```bash
poetry run agentic-tdd run KATA_FILE [OPTIONS]
```

#### Required Arguments

- `KATA_FILE` - Path to kata description markdown file

#### Options

**Working Directory & Language:**
- `-w, --work-dir PATH` - Working directory for implementation (default: `./kata-work`)
- `-l, --language TEXT` - Target programming language (default: `rust`)

**LLM Provider Configuration:**
- `-p, --provider TEXT` - LLM provider (choices: `openai`, `perplexity`, `deepseek`, `iflow`, `custom`) (default: `openai`)
- `-m, --model TEXT` - LLM model name (default: `gpt-4`)
  - Examples: `gpt-4`, `gpt-4-turbo`, `llama-3.1-sonar-large-128k-online`, `deepseek-chat`
- `--api-key TEXT` - API key for LLM provider (or set via environment variable)
- `--base-url TEXT` - Custom base URL for LLM provider (required for `custom` provider, optional for others)
- `-t, --temperature FLOAT` - LLM temperature for generation (0.0-1.0, default: `0.7`)

**Session Control:**
- `--max-cycles INT` - Maximum number of TDD cycles (default: `15`)
- `--max-retries INT` - Maximum retry attempts per agent (default: `3`)
- `--command-timeout INT` - Timeout for shell commands in seconds (default: `300`)

**Output:**
- `-V, --verbose` - Enable verbose logging

### Examples

**Using OpenAI:**
```bash
export OPENAI_API_KEY=sk-...
poetry run agentic-tdd run katas/fizzbuzz.md --model gpt-4
```

**Using Perplexity:**
```bash
export PERPLEXITY_API_KEY=pplx-...
poetry run agentic-tdd run katas/fizzbuzz.md \
  --provider perplexity \
  --model llama-3.1-sonar-large-128k-online
```

**Using DeepSeek:**
```bash
export DEEPSEEK_API_KEY=sk-...
poetry run agentic-tdd run katas/fizzbuzz.md \
  --provider deepseek \
  --model deepseek-chat
```

**Using Custom OpenAI-Compatible Provider:**
```bash
poetry run agentic-tdd run katas/fizzbuzz.md \
  --provider custom \
  --base-url https://your-api.example.com/v1 \
  --model your-model-name \
  --api-key your-api-key
```

**Advanced Configuration:**
```bash
poetry run agentic-tdd run katas/mars-rover.md \
  --work-dir ./my-kata \
  --language rust \
  --provider openai \
  --model gpt-4-turbo \
  --temperature 0.5 \
  --max-cycles 20 \
  --max-retries 5 \
  --verbose
```

### Environment Variables

The tool looks for API keys in the following environment variables:
- `OPENAI_API_KEY` - For OpenAI provider
- `PERPLEXITY_API_KEY` - For Perplexity provider
- `DEEPSEEK_API_KEY` - For DeepSeek provider
- `IFLOW_API_KEY` - For iFlow provider

### Built-in Providers

| Provider | Default Base URL | Environment Variable |
|----------|------------------|----------------------|
| `openai` | `https://api.openai.com/v1` | `OPENAI_API_KEY` |
| `perplexity` | `https://api.perplexity.ai` | `PERPLEXITY_API_KEY` |
| `deepseek` | `https://api.deepseek.com/v1` | `DEEPSEEK_API_KEY` |
| `iflow` | `https://apis.iflow.cn/v1` | `IFLOW_API_KEY` |
| `custom` | *Required via `--base-url`* | Use `--api-key` flag |

**Note:** You can override the base URL for any built-in provider using the `--base-url` flag.

## Development

```bash
# Format code
make fmt

# Lint code
make lint

# Run tests
make test

# Clean artifacts
make clean
```

## How It Works

1. **Initialize Session**: Creates a git repository and initializes the project structure
2. **TDD Cycle Loop**: Executes red-green-refactor cycles until kata completion or max cycles reached
   - **Tester Agent**: Writes a failing test for the next requirement
   - **Implementer Agent**: Makes the test pass with minimal code
   - **Refactorer Agent**: Improves code quality while keeping tests green
3. **Quality Gates**: Each phase includes automated testing, linting, and formatting
4. **Git History**: Every successful phase creates a commit, providing a clear audit trail

## Project Status

**Current Status**: ✅ CLI Infrastructure Complete

- ✅ Multi-agent architecture implemented
- ✅ Rust language runner with cargo integration
- ✅ CLI with full argument parsing
- ✅ Git-based communication between agents
- ✅ Quality gates (format, lint, test)
- 🚧 Testing phase with real-world katas (in progress)

See `/specs/001-multi-agent-tdd-cli/plan.md` for detailed progress.

## Documentation

See the `/specs/001-multi-agent-tdd-cli/` directory for detailed specifications:

- `spec.md` - Feature specification and requirements
- `plan.md` - Implementation plan and phases
- `data-model.md` - Data structures and models
- `quickstart.md` - User guide and walkthrough
- `contracts/` - Interface specifications

## License

See LICENSE file for details.
