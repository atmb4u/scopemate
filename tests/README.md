# scopemate Tests

This directory contains tests for the scopemate package. The tests are organized by module and functionality.

## Test Structure

- `conftest.py`: Common fixtures used across test files
- `test_models.py`: Tests for Pydantic models
- `test_storage.py`: Tests for saving and loading tasks
- `test_task_analysis.py`: Tests for task analysis functionality
- `test_breakdown.py`: Tests for task breakdown functionality
- `test_llm.py`: Tests for LLM interaction (mocked)
- `test_cli.py`: Tests for command-line interface 
- `test_interaction.py`: Tests for user interaction helpers
- `test_integration.py`: Integration tests across multiple modules
- `test_basic.py`: Basic import and version tests
- `test_platform.py`: Platform compatibility tests

## Running Tests

### Prerequisites

Install the development dependencies:

```bash
# Using pip
pip install -r requirements-dev.txt

# Or using uv (recommended)
uv pip install -r requirements-dev.txt
```

### Run All Tests

```bash
# Run with pytest
pytest

# Run with detailed output
pytest -v

# Run with coverage report
pytest --cov=scopemate
```

### Run Specific Test Files

```bash
# Run just the models tests
pytest tests/test_models.py

# Run multiple specific test files
pytest tests/test_models.py tests/test_storage.py
```

### Run Tests by Category

```bash
# Run only fast tests (skip slow ones)
pytest -m "not slow"

# Run only integration tests
pytest -m "integration"
```

### Run a Specific Test

```bash
# Run a specific test function
pytest tests/test_models.py::test_get_utc_now

# Run a specific test class
pytest tests/test_models.py::TestScopeMateTaskModel
```

## Test Environment

Most tests use mocking to avoid:
1. Actual OpenAI API calls
2. User interaction prompts
3. File system dependencies (when possible)

This means that most tests can run without setting up actual LLM API keys or manually responding to prompts.

## Adding New Tests

When adding new tests:

1. Use appropriate fixtures from `conftest.py`
2. Mock external dependencies and I/O operations
3. Add proper test categorization/markers if needed
4. Follow the naming conventions:
   - Test files: `test_*.py`
   - Test functions: `test_*`
   - Test classes: `Test*` 