# Language Runner Contract

**Purpose**: Define the interface for language-specific execution adapters. Language runners abstract away language-specific tooling (build, test, format, lint) from the core agent logic.

---

## Interface Definition

### Abstract Base Class

```python
from abc import ABC, abstractmethod
from pathlib import Path
from models.runner import TestResult, CommandResult, QualityGateResult

class LanguageRunner(ABC):
    """Abstract interface for language-specific operations."""
    
    @property
    @abstractmethod
    def language_name(self) -> str:
        """Human-readable language name (e.g., 'Rust', 'Python')."""
        pass
    
    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """File extensions for this language (e.g., ['.rs', '.toml'])."""
        pass
    
    @abstractmethod
    def initialize_project(self, path: Path, project_name: str) -> CommandResult:
        """Initialize a new project in the given directory.
        
        Args:
            path: Directory where project should be initialized
            project_name: Name for the project/package
            
        Returns:
            CommandResult with initialization command output
            
        Example (Rust):
            cargo init --name kata_name
        
        Example (Python):
            poetry init --name kata_name --no-interaction
            Create src/ and tests/ directories
        """
        pass
    
    @abstractmethod
    def run_tests(self, path: Path) -> TestResult:
        """Execute test suite and parse results.
        
        Args:
            path: Project root directory
            
        Returns:
            TestResult with pass/fail status and test counts
            
        Example (Rust):
            cargo test --color=always
            Parse output for "test result: ok. 3 passed; 0 failed"
        
        Example (Python):
            pytest --verbose --tb=short
            Parse output for test counts
        """
        pass
    
    @abstractmethod
    def format_code(self, path: Path) -> QualityGateResult:
        """Format code according to language conventions.
        
        Args:
            path: Project root directory
            
        Returns:
            QualityGateResult with auto_fixed=True if formatting applied
            
        Example (Rust):
            cargo fmt
        
        Example (Python):
            black .
            isort .
        """
        pass
    
    @abstractmethod
    def lint_code(self, path: Path) -> QualityGateResult:
        """Run linter and report issues.
        
        Args:
            path: Project root directory
            
        Returns:
            QualityGateResult with issues_found list
            
        Example (Rust):
            cargo clippy -- -D warnings
        
        Example (Python):
            ruff check .
        """
        pass
    
    @abstractmethod
    def build(self, path: Path) -> CommandResult:
        """Build/compile the project.
        
        Args:
            path: Project root directory
            
        Returns:
            CommandResult with compilation output
            
        Example (Rust):
            cargo build
        
        Example (Python):
            python -m py_compile src/**/*.py  # Optional for Python
        """
        pass
    
    @abstractmethod
    def get_test_file_pattern(self) -> str:
        """Return glob pattern for test files.
        
        Returns:
            Glob pattern string
            
        Example (Rust): "tests/**/*.rs"
        Example (Python): "tests/**/test_*.py"
        """
        pass
    
    @abstractmethod
    def get_source_file_pattern(self) -> str:
        """Return glob pattern for source files.
        
        Returns:
            Glob pattern string
            
        Example (Rust): "src/**/*.rs"
        Example (Python): "src/**/*.py"
        """
        pass
```

---

## Implementation Contract

### Required Behavior

1. **Idempotency**: Multiple calls to same method with same state should be safe
2. **Working Directory**: All commands should execute in provided `path` directory
3. **Output Capture**: All stdout and stderr must be captured and returned
4. **Timeout Handling**: Commands should timeout after 30 seconds (configurable)
5. **Error Propagation**: Exceptions should be caught and returned in result objects

### Quality Gate Sequence

Before any commit, agents MUST execute in this order:

```python
# 1. Format (auto-fix)
format_result = runner.format_code(work_dir)
if format_result.auto_fixed:
    # Re-run tests after formatting
    test_result = runner.run_tests(work_dir)

# 2. Lint (must pass)
lint_result = runner.lint_code(work_dir)
if not lint_result.passed:
    raise QualityGateFailure("Lint issues must be fixed")

# 3. Tests (must pass)
test_result = runner.run_tests(work_dir)
if not test_result.passed:
    raise QualityGateFailure("Tests must pass")

# 4. Build (must succeed)
build_result = runner.build(work_dir)
if not build_result.success:
    raise QualityGateFailure("Build must succeed")
```

---

## Concrete Implementations

### Rust Runner (MVP)

**Module**: `agentic_tdd/runners/rust.py`

**Dependencies**: Cargo, rustc, rustfmt, clippy (standard Rust toolchain)

**Commands**:
- Initialize: `cargo init --name {project_name}`
- Test: `cargo test --color=always`
- Format: `cargo fmt`
- Lint: `cargo clippy -- -D warnings`
- Build: `cargo build`

**Output Parsing**:
```python
# Parse cargo test output
# "test result: ok. 5 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out"
pattern = r"(\d+) passed; (\d+) failed"
match = re.search(pattern, output)
passed_count = int(match.group(1))
failed_count = int(match.group(2))
```

### Python Runner (Future)

**Module**: `agentic_tdd/runners/python.py`

**Dependencies**: pytest, black, ruff, mypy

**Commands**:
- Initialize: `poetry init --no-interaction`, create `src/` and `tests/`
- Test: `pytest --verbose --tb=short`
- Format: `black .`, `isort .`
- Lint: `ruff check .`
- Build: `mypy src/` (type check as build step)

---

## Factory Pattern

```python
from typing import Type
from runners.rust import RustRunner

_RUNNERS: dict[str, Type[LanguageRunner]] = {
    "rust": RustRunner,
    # Future: "python": PythonRunner, "typescript": TypeScriptRunner
}

def get_runner(language: str) -> LanguageRunner:
    """Get language runner instance by name.
    
    Args:
        language: Language identifier (e.g., 'rust', 'python')
        
    Returns:
        LanguageRunner instance
        
    Raises:
        ValueError: If language not supported
    """
    runner_class = _RUNNERS.get(language.lower())
    if runner_class is None:
        supported = ", ".join(_RUNNERS.keys())
        raise ValueError(f"Unsupported language: {language}. Supported: {supported}")
    
    return runner_class()
```

---

## Testing Contract

### Unit Tests

Each runner implementation MUST have unit tests covering:

1. **Project initialization**: Creates expected file structure
2. **Test execution**: Correctly parses pass/fail/counts
3. **Formatting**: Detects when files are modified
4. **Linting**: Parses and reports issues
5. **Building**: Detects compilation errors
6. **Error handling**: Handles missing tooling, timeouts

### Integration Tests

Runner integration tests use real language toolchains:

```python
def test_rust_runner_full_tdd_cycle(tmp_path):
    """Test full TDD cycle with Rust runner."""
    runner = RustRunner()
    
    # Initialize
    result = runner.initialize_project(tmp_path, "test_kata")
    assert result.success
    
    # Write failing test
    test_file = tmp_path / "tests" / "test_example.rs"
    test_file.write_text("""
        #[test]
        fn test_add() {
            assert_eq!(add(2, 3), 5);
        }
    """)
    
    # Should fail (function doesn't exist)
    test_result = runner.run_tests(tmp_path)
    assert not test_result.passed
    
    # Implement function
    src_file = tmp_path / "src" / "lib.rs"
    src_file.write_text("""
        pub fn add(a: i32, b: i32) -> i32 {
            a + b
        }
    """)
    
    # Should pass
    test_result = runner.run_tests(tmp_path)
    assert test_result.passed
    assert test_result.passed_count == 1
    
    # Quality gates should pass
    assert runner.format_code(tmp_path).passed
    assert runner.lint_code(tmp_path).passed
    assert runner.build(tmp_path).success
```

---

## Extension Guide

To add a new language runner:

1. **Create runner module**: `agentic_tdd/runners/{language}.py`
2. **Implement LanguageRunner**: Inherit and implement all abstract methods
3. **Add to factory**: Register in `_RUNNERS` dict
4. **Write tests**: Unit and integration tests
5. **Document tooling**: Required tools and versions in README
6. **Update CLI**: Add language to `--language` enum

---

**Version**: 1.0.0 | **Status**: Complete | **Related**: data-model.md Section 5
