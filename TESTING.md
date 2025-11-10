# Testing Guidelines for Agentic TDD Development

## Standard Testing Configuration

When testing new features or validating fixes, use the following standard configuration:

### Default Test Command

```bash
python -m agentic_tdd katas/battleships-kata.md \
  --provider iflow \
  --model qwen3-coder-plus \
  --work-dir ./tmp/kata1 \
  --max-cycles 5
```

### Configuration Details

- **Provider**: `iflow` - Chinese LLM provider with reliable availability
- **Model**: `qwen3-coder-plus` - Alibaba's code-focused model optimized for code generation
- **Work Directory**: `./tmp/kata1` (or incrementing: `./tmp/kata2`, etc.) - Easy cleanup, no pollution of main directory
- **Max Cycles**: `5` - Sufficient to test multi-cycle behavior without long wait times
- **API Key**: Set via environment variable `IFLOW_API_KEY`

### Environment Setup

```bash
# Set API key (required)
export IFLOW_API_KEY=your-key-here

# Verify it's set
echo $IFLOW_API_KEY
```

## Test Katas

Use these katas for different testing scenarios:

### 1. FizzBuzz (`katas/fizzbuzz-kata.md`)
- **Complexity**: Simple
- **Use Case**: Quick smoke tests, basic validation
- **Expected Cycles**: 3-5
- **Tests Expected**: 4-6 tests (fizz, buzz, fizzbuzz, normal numbers)

```bash
python -m agentic_tdd katas/fizzbuzz-kata.md \
  --provider iflow \
  --model qwen3-coder-plus \
  --work-dir ./tmp/fizzbuzz \
  --max-cycles 5
```

### 2. Battleships (`katas/battleships-kata.md`)
- **Complexity**: Medium
- **Use Case**: Test preservation validation, multi-cycle behavior
- **Expected Cycles**: 8-12
- **Tests Expected**: 8-12 tests (empty board, single ship, multiple ships, edge cases)

```bash
python -m agentic_tdd katas/battleships-kata.md \
  --provider iflow \
  --model qwen3-coder-plus \
  --work-dir ./tmp/battleships \
  --max-cycles 10
```

### 3. Mars Rover (`katas/mars-rover-kata.md`)
- **Complexity**: High
- **Use Case**: Complex domain logic, state management, full TDD workflow
- **Expected Cycles**: 12-20
- **Tests Expected**: 15+ tests (commands, rotation, movement, wrapping, obstacles)

```bash
python -m agentic_tdd katas/mars-rover-kata.md \
  --provider iflow \
  --model qwen3-coder-plus \
  --work-dir ./tmp/marsrover \
  --max-cycles 15
```

## Testing Workflows

### Quick Smoke Test (2-3 minutes)
```bash
# Test basic functionality with FizzBuzz
python -m agentic_tdd katas/fizzbuzz-kata.md \
  --provider iflow \
  --model qwen3-coder-plus \
  --work-dir ./tmp/smoke \
  --max-cycles 3
```

### Standard Validation Test (5-10 minutes)
```bash
# Test multi-cycle behavior with Battleships
python -m agentic_tdd katas/battleships-kata.md \
  --provider iflow \
  --model qwen3-coder-plus \
  --work-dir ./tmp/validation \
  --max-cycles 5

# Inspect results
cd ./tmp/validation
git log --oneline --all
cargo test
```

### Comprehensive Integration Test (15-30 minutes)
```bash
# Full kata run with Mars Rover
python -m agentic_tdd katas/mars-rover-kata.md \
  --provider iflow \
  --model qwen3-coder-plus \
  --work-dir ./tmp/integration \
  --max-cycles 15 \
  --verbose
```

## Post-Test Analysis

### Git History Analysis

```bash
cd ./tmp/kata1

# View all commits
git log --oneline --all

# View commit with details
git log --stat

# Count tests per commit
for commit in $(git log --oneline --reverse | awk '{print $1}'); do
  count=$(git show "$commit:src/lib.rs" 2>/dev/null | grep -c "#\[test\]" || echo 0)
  echo "Commit $commit: $count tests"
done

# View specific commit changes
git show <commit-hash>

# View file at specific commit
git show <commit-hash>:src/lib.rs
```

### Test Execution Analysis

```bash
cd ./tmp/kata1

# Run all tests
cargo test

# Run tests with output
cargo test -- --nocapture

# Run specific test
cargo test test_name

# Check code formatting
cargo fmt --check

# Run linting
cargo clippy
```

### Code Quality Analysis

```bash
cd ./tmp/kata1

# Check for test duplication
grep -n "#\[test\]" src/lib.rs

# Check function count
grep -c "^fn " src/lib.rs
grep -c "^pub fn " src/lib.rs

# Check lines of code
wc -l src/lib.rs

# View test module
sed -n '/^#\[cfg(test)\]/,/^}$/p' src/lib.rs
```

## Cleanup

### Clean Single Test Run
```bash
rm -rf ./tmp/kata1
```

### Clean All Test Runs
```bash
rm -rf ./tmp/kata*
```

### Clean and Reset
```bash
# Clean all test directories
rm -rf ./tmp/*

# Verify
ls -la ./tmp/
```

## Alternative Providers

If iflow is unavailable, use these alternatives:

### OpenAI (requires quota)
```bash
export OPENAI_API_KEY=sk-...
python -m agentic_tdd katas/battleships-kata.md \
  --provider openai \
  --model gpt-4o-mini \
  --work-dir ./tmp/kata1 \
  --max-cycles 5
```

### Perplexity
```bash
export PERPLEXITY_API_KEY=pplx-...
python -m agentic_tdd katas/battleships-kata.md \
  --provider perplexity \
  --model llama-3.1-sonar-large-128k-online \
  --work-dir ./tmp/kata1 \
  --max-cycles 5
```

### DeepSeek
```bash
export DEEPSEEK_API_KEY=sk-...
python -m agentic_tdd katas/battleships-kata.md \
  --provider deepseek \
  --model deepseek-chat \
  --work-dir ./tmp/kata1 \
  --max-cycles 5
```

## Troubleshooting

### API Key Not Found
```bash
# Check if key is set
echo $IFLOW_API_KEY

# Set it if missing
export IFLOW_API_KEY=your-key-here

# Or provide directly in command
python -m agentic_tdd katas/battleships-kata.md \
  --provider iflow \
  --model qwen3-coder-plus \
  --api-key your-key-here \
  --work-dir ./tmp/kata1
```

### Rate Limiting
```bash
# Reduce frequency with lower temperature
python -m agentic_tdd katas/battleships-kata.md \
  --provider iflow \
  --model qwen3-coder-plus \
  --temperature 0.3 \
  --work-dir ./tmp/kata1
```

### Timeout Issues
```bash
# Increase timeout
python -m agentic_tdd katas/battleships-kata.md \
  --provider iflow \
  --model qwen3-coder-plus \
  --command-timeout 600 \
  --work-dir ./tmp/kata1
```

### Work Directory Already Exists
```bash
# Clean before running
rm -rf ./tmp/kata1

# Or use different directory
python -m agentic_tdd katas/battleships-kata.md \
  --provider iflow \
  --model qwen3-coder-plus \
  --work-dir ./tmp/kata-$(date +%s)
```

## CI/CD Integration

For automated testing in CI/CD pipelines:

```bash
#!/bin/bash
# ci-test.sh

set -e  # Exit on error

export IFLOW_API_KEY=${IFLOW_API_KEY}

# Clean previous runs
rm -rf ./tmp/ci-test

# Run test
python -m agentic_tdd katas/fizzbuzz-kata.md \
  --provider iflow \
  --model qwen3-coder-plus \
  --work-dir ./tmp/ci-test \
  --max-cycles 3

# Verify results
cd ./tmp/ci-test

# Check tests pass
cargo test

# Check formatting
cargo fmt --check

# Check linting
cargo clippy -- -D warnings

# Validate git history
commit_count=$(git log --oneline | wc -l)
if [ "$commit_count" -lt 3 ]; then
  echo "❌ Expected at least 3 commits, got $commit_count"
  exit 1
fi

echo "✅ CI tests passed"
```

## Best Practices

1. **Always use tmp directories**: Avoid polluting main workspace
2. **Increment directory names**: Use `kata1`, `kata2`, etc. for parallel testing
3. **Clean between runs**: Remove previous test directories before new runs
4. **Document findings**: Keep notes on LLM behavior, edge cases, failures
5. **Test incrementally**: Start with simple katas before complex ones
6. **Verify git history**: Always check commit history for expected TDD pattern
7. **Use verbose mode for debugging**: Add `--verbose` flag when investigating issues
