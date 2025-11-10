# Validation Guide for Test Preservation Fix

## Background

A critical bug was identified where agents were dropping existing tests and code during TDD cycles. This occurred because each agent used `file.write_text()` to overwrite entire files, and the LLM prompts didn't explicitly instruct preservation of existing code.

### Evidence of Bug (Pre-Fix)

From `./tmp/battleships-test` git history:

**Commit 3398591** (Cycle 1):
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }

    #[test]
    fn test_empty_board_has_no_ships() {
        let board = vec![];
        assert_eq!(count_battleships(board), 0);
    }
}
```
**Result**: ✅ 2 tests present

**Commit 62804c9** (Cycle 3):
```rust
#[test]
fn test_single_battleship() {
    let board = vec![vec!['X']];
    assert_eq!(count_battleships(board), 1);
}
```
**Result**: ❌ Only 1 test, previous 2 tests lost

## The Fix

**Commit**: `101bd65` - "fix: prevent agents from dropping existing tests/code during TDD cycles"

Enhanced prompts in three agent files with **CRITICAL** preservation instructions:

### Files Modified

1. **`agentic_tdd/agents/tester.py`** (lines 177-192)
2. **`agentic_tdd/agents/implementer.py`** (lines 198-217)
3. **`agentic_tdd/agents/refactorer.py`** (lines 215-236)

### Key Changes

Each agent prompt now includes:
- `**CRITICAL**: You MUST include/preserve ALL existing tests and code`
- Explicit instructions not to remove or replace existing code
- Clear guidance to respond with COMPLETE file content including existing code

## Validation Steps

### Option 1: Manual Validation (Recommended)

Run a simple kata and manually inspect git history:

```bash
# Run FizzBuzz kata (requires API access)
python -m agentic_tdd katas/fizzbuzz-kata.md \
  --provider openai \
  --model gpt-4o-mini \
  --max-cycles 5

# Navigate to work directory
cd kata-work

# Check git log
git log --oneline --all

# Inspect test accumulation across commits
git show <commit-1>:src/lib.rs | grep "#\[test\]" | wc -l
git show <commit-2>:src/lib.rs | grep "#\[test\]" | wc -l
git show <commit-3>:src/lib.rs | grep "#\[test\]" | wc -l
```

**Expected Result**: Test count should be monotonically increasing (or stable) across commits, never decreasing.

### Option 2: Automated Validation Script

Create a validation script that:
1. Runs a kata for N cycles
2. Extracts test count from each commit
3. Verifies test count never decreases
4. Reports success/failure

Example:
```bash
#!/bin/bash
# validate-test-preservation.sh

WORK_DIR="kata-work"
KATA_FILE="katas/fizzbuzz-kata.md"

# Run kata
python -m agentic_tdd "$KATA_FILE" --max-cycles 5

# Check test preservation
cd "$WORK_DIR"
commits=$(git log --oneline --reverse | awk '{print $1}')

prev_count=0
for commit in $commits; do
    count=$(git show "$commit:src/lib.rs" | grep -c "#\[test\]" || echo 0)
    echo "Commit $commit: $count tests"
    
    if [ "$count" -lt "$prev_count" ]; then
        echo "❌ FAIL: Test count decreased from $prev_count to $count"
        exit 1
    fi
    prev_count=$count
done

echo "✅ PASS: Test preservation validated"
```

### Option 3: Comparative Analysis

Compare pre-fix and post-fix runs:

```bash
# Pre-fix evidence (already exists)
cd tmp/battleships-test
git log --oneline --all > /tmp/pre-fix-commits.txt

# Post-fix run (requires API access)
python -m agentic_tdd katas/battleships-kata.md --max-cycles 5
cd kata-work
git log --oneline --all > /tmp/post-fix-commits.txt

# Compare test preservation patterns
# (Manual inspection of commits)
```

## Success Criteria

The fix is validated if:

1. ✅ **Test Accumulation**: Test count increases or remains stable across cycles
2. ✅ **No Test Loss**: Previously written tests are never removed
3. ✅ **Code Preservation**: Existing functions remain in file when new code is added
4. ✅ **Complete Files**: Each commit contains complete, compilable code

## Known Limitations

### Current Fix Limitations

The prompt-based fix relies on LLM compliance with instructions. Potential weaknesses:

1. **LLM Non-Compliance**: Model might ignore "CRITICAL" instructions under certain conditions
2. **Token Limits**: Very large files might cause truncation
3. **Format Confusion**: Complex code structures might confuse the LLM's merging logic

### Alternative Fix Strategies (If Current Fix Fails)

#### Strategy 1: AST-Based Merging
```python
# Parse existing file as AST
# Parse LLM output as AST
# Programmatically merge test modules and functions
# Write merged AST back to file
```

**Pros**: Deterministic, no LLM reliability issues  
**Cons**: Language-specific, complex implementation

#### Strategy 2: Diff-Based Editing
```python
# Change LLM output format to unified diff
# Apply diff using patch command
# Validate compilation after patch
```

**Pros**: Standard tooling, precise control  
**Cons**: Requires different prompt engineering, harder for LLM to generate diffs

#### Strategy 3: Append-Only Mode
```python
# For tests: Always append new tests to test module
# For implementation: Allow overwrites but preserve test sections
# Use file section markers (e.g., "// BEGIN TESTS", "// END TESTS")
```

**Pros**: Simple, predictable  
**Cons**: Limited flexibility, potential duplication issues

## Validation Status

- ✅ **Bug Identified**: Confirmed via git history analysis
- ✅ **Fix Implemented**: Prompt enhancements committed (`101bd65`)
- ⚠️ **Fix Validated**: **PENDING** - Requires successful multi-cycle kata run
- ⏳ **Blocker**: OpenAI API quota exceeded during validation attempt

## Next Steps

1. **Immediate**: User with API access should run validation (Option 1 or 2)
2. **If validation passes**: Update README.md with fix confirmation
3. **If validation fails**: Implement Strategy 1 (AST-based merging) as more robust solution

## Test Cases for Validation

### Test Case 1: Simple Accumulation
- **Kata**: FizzBuzz
- **Cycles**: 5
- **Expected**: 5+ tests by cycle 5, none removed

### Test Case 2: Complex Domain
- **Kata**: Battleships
- **Cycles**: 10
- **Expected**: 10+ tests by cycle 10, none removed

### Test Case 3: Edge Cases
- **Kata**: Mars Rover
- **Cycles**: 15
- **Expected**: Tests for all commands (f, b, l, r, position), none removed

## Reporting Results

After validation, update this document with:

```markdown
## Validation Results

**Date**: YYYY-MM-DD
**Validator**: [Your Name]
**Provider**: [openai/perplexity/deepseek]
**Model**: [model-name]

### Results
- Kata: [kata-name]
- Cycles Run: X
- Test Count by Cycle: [1, 2, 3, 5, 7, ...]
- Tests Lost: [Y] (should be 0)
- Status: [✅ PASS / ❌ FAIL]

### Notes
[Any observations about LLM behavior, edge cases, etc.]
```
