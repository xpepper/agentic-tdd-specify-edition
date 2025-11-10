# Quickstart Guide: Multi-Agent TDD CLI

**Get started with autonomous TDD in under 5 minutes.**

---

## Prerequisites

Before installing, ensure you have:

1. **Python 3.11 or higher**
   ```bash
   python --version  # Should show 3.11+
   ```

2. **Git**
   ```bash
   git --version
   ```

3. **Rust toolchain** (for MVP language support)
   ```bash
   cargo --version
   rustc --version
   rustfmt --version
   cargo clippy --version
   ```
   
   If not installed, get it from [rustup.rs](https://rustup.rs/):
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

4. **OpenAI-compatible API access**
   - OpenAI API key, or
   - Perplexity API key, or
   - DeepSeek API key, or
   - Any OpenAI-compatible provider

---

## Installation

### Option 1: Install from PyPI (when released)

```bash
pip install agentic-tdd
```

### Option 2: Install from source (development)

```bash
# Clone repository
git clone https://github.com/yourusername/agentic-tdd.git
cd agentic-tdd

# Install with Poetry
poetry install

# Or with pip
pip install -e .
```

### Verify Installation

```bash
agentic-tdd --version
# Output: agentic-tdd version 0.1.0
```

---

## Configuration

### Set API Key

Choose one method:

**Environment Variable (Recommended)**:
```bash
export OPENAI_API_KEY="sk-..."
# Or for other providers:
export PERPLEXITY_API_KEY="pplx-..."
export DEEPSEEK_API_KEY="sk-..."
```

**CLI Flag**:
```bash
agentic-tdd run kata.md --api-key "sk-..."
```

---

## Your First Kata: FizzBuzz

### Step 1: Create Kata Description

Create a file `fizzbuzz.md`:

```markdown
# FizzBuzz Kata

## Description

Write a function that takes a number and returns:
- "Fizz" if divisible by 3
- "Buzz" if divisible by 5
- "FizzBuzz" if divisible by both 3 and 5
- The number as a string otherwise

## Requirements

- Function should handle positive integers
- Function should handle the special cases in order (FizzBuzz, Fizz, Buzz)
- Function should return a string

## Examples

Input: 1 → Output: "1"
Input: 3 → Output: "Fizz"
Input: 5 → Output: "Buzz"
Input: 15 → Output: "FizzBuzz"
```

### Step 2: Run the Tool

```bash
agentic-tdd run fizzbuzz.md \
  --work-dir ./fizzbuzz-solution \
  --language rust \
  --provider openai \
  --model gpt-4
```

### Step 3: Watch the Magic

You'll see output like:

```
🚀 Starting TDD Session
📄 Kata: FizzBuzz Kata
🗂️  Work Directory: ./fizzbuzz-solution
🦀 Language: Rust
🤖 LLM: openai/gpt-4

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cycle 1/15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧪 Tester: Writing failing test...
   ✅ Test written: tests/test_fizzbuzz.rs::test_returns_number_as_string
   ❌ Test failed (red state verified)
   📝 Staged: tests/test_fizzbuzz.rs

⚙️  Implementer: Making test pass...
   ✅ Implementation complete: src/lib.rs::fizzbuzz
   ✅ All tests passed (green state)
   ✨ Quality gates passed
   📦 Committed: feat: implement fizzbuzz number return

🔧 Refactorer: Improving code quality...
   ✅ No refactoring needed (code already clean)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Cycle 2/15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🧪 Tester: Writing failing test...
   ✅ Test written: tests/test_fizzbuzz.rs::test_returns_fizz_for_three
   ❌ Test failed (red state verified)
   📝 Staged: tests/test_fizzbuzz.rs

...
```

### Step 4: Explore the Solution

```bash
cd fizzbuzz-solution

# View git history
git log --oneline

# Run tests
cargo test

# See the code
cat src/lib.rs
cat tests/test_fizzbuzz.rs
```

---

## CLI Reference

### `agentic-tdd run`

Execute a kata with autonomous TDD.

```bash
agentic-tdd run <kata-file> [OPTIONS]
```

**Arguments**:
- `<kata-file>`: Path to kata description markdown file (required)

**Options**:
- `--work-dir PATH`: Working directory for implementation (default: `./kata-work`)
- `--language LANG`: Target language (default: `rust`, future: `python`, `typescript`)
- `--provider PROVIDER`: LLM provider (choices: `openai`, `perplexity`, `deepseek`, `iflow`, `custom`)
- `--model MODEL`: Model name (e.g., `gpt-4`, `llama-2-70b-chat`)
- `--api-key KEY`: API key for LLM provider (or use env var)
- `--base-url URL`: Custom base URL for provider (for `custom` provider)
- `--max-cycles NUM`: Maximum TDD cycles (default: 15)
- `--max-retries NUM`: Max retry attempts per agent (default: 3)
- `--verbose`: Enable verbose logging

**Examples**:

```bash
# Basic usage with OpenAI
agentic-tdd run fizzbuzz.md --provider openai --model gpt-4

# Use Perplexity
agentic-tdd run mars-rover.md \
  --provider perplexity \
  --model llama-3.1-sonar-large-128k-online

# Custom provider
agentic-tdd run bowling.md \
  --provider custom \
  --base-url https://my-llm-provider.com/v1 \
  --model my-model

# Verbose output
agentic-tdd run gilded-rose.md --verbose
```

---

## Common Workflows

### Working with Existing Code

To continue from an existing implementation:

```bash
# Run with existing work directory
agentic-tdd run kata.md --work-dir ./existing-solution

# Tool will:
# 1. Detect existing git repo
# 2. Read current code
# 3. Continue from current state
```

### Stopping and Resuming

The tool can be stopped with `Ctrl+C` and resumed:

```bash
# Stop during execution (Ctrl+C)
^C
🛑 Session interrupted after cycle 5

# Resume later
agentic-tdd run kata.md --work-dir ./kata-work
# Tool detects existing state and continues
```

### Reviewing Agent Decisions

```bash
cd kata-work

# View commit history (shows agent decisions)
git log --oneline --decorate

# View specific commit
git show <commit-sha>

# See what test was written
git show :/^test:

# See what implementation was added
git show :/^feat:

# See refactoring changes
git show :/^refactor:
```

---

## Configuration File (Optional)

Create `.agentic-tdd.yaml` in your project:

```yaml
provider: openai
model: gpt-4
language: rust
max_cycles: 20
max_retries: 3
work_dir: ./solutions

# API key from environment
api_key_env: OPENAI_API_KEY
```

Then run without flags:

```bash
agentic-tdd run fizzbuzz.md
```

---

## Troubleshooting

### "API key not found"

**Solution**: Set environment variable or use `--api-key` flag:
```bash
export OPENAI_API_KEY="sk-..."
```

### "Language toolchain not found"

**Solution**: Install required tools:
- Rust: [rustup.rs](https://rustup.rs/)
- Python: `pip install pytest black ruff mypy`

### "Tests keep failing"

**Possible causes**:
1. Kata description unclear → Simplify requirements
2. LLM model too weak → Try GPT-4 instead of GPT-3.5
3. Max retries too low → Increase with `--max-retries 5`

### "Too many cycles"

**Solution**: Kata might be too complex. Try:
1. Break kata into smaller pieces
2. Increase `--max-cycles 25`
3. Review generated code and provide clearer constraints

---

## Example Katas

Try these classic katas:

### 1. FizzBuzz (Beginner)
**Complexity**: 3-5 cycles  
**Time**: ~2-3 minutes  
**File**: See example above

### 2. Roman Numerals (Intermediate)
**Complexity**: 8-12 cycles  
**Time**: ~5-8 minutes  
**Description**: Convert integers to Roman numerals (1-3999)

### 3. Bowling Game (Advanced)
**Complexity**: 10-15 cycles  
**Time**: ~10-15 minutes  
**Description**: Score a bowling game with strikes and spares

---

## Next Steps

- **Read full documentation**: `docs/` directory
- **Explore kata library**: `examples/katas/`
- **Customize agent behavior**: `docs/configuration.md`
- **Add language support**: `docs/extending.md`
- **Report issues**: GitHub Issues

---

## Getting Help

- **Documentation**: [https://agentic-tdd.readthedocs.io](https://agentic-tdd.readthedocs.io)
- **Issues**: [https://github.com/yourusername/agentic-tdd/issues](https://github.com/yourusername/agentic-tdd/issues)
- **Discussions**: [https://github.com/yourusername/agentic-tdd/discussions](https://github.com/yourusername/agentic-tdd/discussions)

---

**Version**: 1.0.0 | **Last Updated**: 2025-11-10
