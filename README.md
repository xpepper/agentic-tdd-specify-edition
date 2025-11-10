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

```bash
# Run a kata
poetry run agentic-tdd run katas/fizzbuzz.md --language rust

# Configure LLM provider
poetry run agentic-tdd run katas/fizzbuzz.md --provider openai --model gpt-4
```

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

## Project Status

This project is currently under active development. Phase 1 (Setup) is complete.

## Documentation

See the `/specs/001-multi-agent-tdd-cli/` directory for detailed specifications:

- `spec.md` - Feature specification and requirements
- `plan.md` - Implementation plan and phases
- `data-model.md` - Data structures and models
- `quickstart.md` - User guide and walkthrough
- `contracts/` - Interface specifications

## License

See LICENSE file for details.
