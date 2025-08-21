# Testing Guide

This guide covers how to run tests, linting, and formatting for Orbyte using `uv run`.

## Quick Start

```bash
# Run all tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/orbyte

# Run linting
uv run ruff check .

# Run formatting
uv run ruff format .

# Run type checking
uv run mypy src/
```

## Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run tests with coverage report
uv run pytest --cov=src/orbyte --cov-report=html

# Run tests with coverage in terminal
uv run pytest --cov=src/orbyte --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_core.py

# Run specific test method
uv run pytest tests/test_core.py::test_render_basic

# Run tests matching pattern
uv run pytest -k "test_render"

# Run tests in verbose mode
uv run pytest -v

# Run tests and stop on first failure
uv run pytest -x
```

### Coverage Options

```bash
# Generate HTML coverage report (opens in browser)
uv run pytest --cov=src/orbyte --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux

# Generate XML coverage report (for CI)
uv run pytest --cov=src/orbyte --cov-report=xml

# Show missing lines in terminal
uv run pytest --cov=src/orbyte --cov-report=term-missing

# Set minimum coverage threshold
uv run pytest --cov=src/orbyte --cov-fail-under=90
```

## Linting with Ruff

### Checking Code Quality

```bash
# Check all files for linting issues
uv run ruff check .

# Check specific file
uv run ruff check src/orbyte/core.py

# Check with detailed output
uv run ruff check . --verbose

# Show only errors (no warnings)
uv run ruff check . --quiet

# Check and show fixes that would be applied
uv run ruff check . --diff
```

### Auto-fixing Issues

```bash
# Fix all auto-fixable issues
uv run ruff check . --fix

# Preview fixes without applying
uv run ruff check . --fix --diff

# Fix specific file
uv run ruff check src/orbyte/core.py --fix
```

## Code Formatting with Ruff

### Formatting Code

```bash
# Format all files
uv run ruff format .

# Format specific file
uv run ruff format src/orbyte/core.py

# Check formatting without making changes
uv run ruff format . --check

# Show diff of what would be formatted
uv run ruff format . --diff
```

### Formatting Options

```bash
# Check if files need formatting (exit code 1 if changes needed)
uv run ruff format . --check

# Format and show what was changed
uv run ruff format . --diff

# Format only Python files in specific directory
uv run ruff format src/
```

## Type Checking with MyPy

### Running Type Checks

```bash
# Check all source files
uv run mypy src/

# Check specific file
uv run mypy src/orbyte/core.py

# Check with verbose output
uv run mypy src/ --verbose

# Check and show error codes
uv run mypy src/ --show-error-codes

# Check with strict mode
uv run mypy src/ --strict
```

### MyPy Configuration

The project uses `mypy.ini` for configuration. Common options:

```bash
# Check if config file is being used
uv run mypy src/ --show-files

# Ignore specific error types temporarily
uv run mypy src/ --disable-error-code=import-untyped
```

## Running All Checks

### Using Nox (Recommended)

```bash
# Run all checks (tests, linting, formatting, type checking)
uv run nox

# Run specific nox session
uv run nox -s tests
uv run nox -s lint
uv run nox -s typecheck

# List available nox sessions
uv run nox --list
```

### Manual All-in-One

```bash
# Run everything manually
uv run ruff check . && \
uv run ruff format --check . && \
uv run mypy src/ && \
uv run pytest --cov=src/orbyte
```

## Development Workflow

### Before Committing

```bash
# 1. Format code
uv run ruff format .

# 2. Fix linting issues
uv run ruff check . --fix

# 3. Check types
uv run mypy src/

# 4. Run tests
uv run pytest

# 5. Check coverage
uv run pytest --cov=src/orbyte --cov-fail-under=90
```

### Pre-commit Setup

For automated checks, consider setting up a pre-commit hook:

```bash
# Install pre-commit (optional)
pip install pre-commit

# Set up pre-commit hooks (if .pre-commit-config.yaml exists)
pre-commit install
```

## Continuous Integration

The project uses GitHub Actions for CI. The following commands mirror what runs in CI:

```bash
# Linting (what runs in CI)
uv run ruff check .
uv run ruff format --check .

# Type checking (what runs in CI)
uv run mypy src/ tests/

# Testing (what runs in CI)
uv run pytest --cov=src/orbyte --cov-report=xml
```

## Troubleshooting

### Common Issues

**Import errors during testing:**
```bash
# Make sure package is installed in development mode
uv pip install -e .
```

**Coverage not working:**
```bash
# Ensure pytest-cov is installed
uv add --group dev pytest-cov

# Check if coverage is configured in pyproject.toml
grep -A 10 "tool.coverage" pyproject.toml
```

**MyPy can't find modules:**
```bash
# Check if types are installed
uv add --group dev types-click types-babel

# Verify PYTHONPATH includes src/
export PYTHONPATH="${PWD}/src:${PYTHONPATH}"
uv run mypy src/
```

**Ruff configuration issues:**
```bash
# Check current configuration
uv run ruff check --show-settings

# Test specific rule
uv run ruff check --select E501 .  # Line length
```

### Performance Tips

```bash
# Run tests in parallel (if pytest-xdist is available)
uv run pytest -n auto

# Run only fast tests (if marked)
uv run pytest -m "not slow"

# Cache MyPy results for faster subsequent runs
uv run mypy src/ --cache-dir=.mypy_cache
```

## Configuration Files

The testing behavior is configured in:

- **`pyproject.toml`** - pytest, coverage, and ruff settings
- **`mypy.ini`** - MyPy type checking configuration  
- **`noxfile.py`** - Nox automation sessions

See these files for customizing test behavior, coverage thresholds, and code quality rules.