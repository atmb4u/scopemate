# 🪜 scopemate

A CLI tool for breaking down complex tasks into smaller subtasks with LLM-powered scope estimation and planning.

## Conceptual Framework

Scopemate is built around a three-part framework for strategic decision making:

### 🧭 Purpose → Strategic Relevance

**"Why does this matter now?"**

- Is it aligned with a company priority, customer need, or mission-critical goal?
- If we didn't do it, would anything break or stall?
- Does this move us closer to where we want to be?

> **✅ If not strategic, it's a distraction.**

### 📦 Scope → Executable Shape

**"Can we actually do this — fast and clearly?"**

- Is it defined tightly enough to start today or this week?
- Can one person or squad own it end-to-end?
- What's the smallest useful version we can ship?

> **✅ If it's vague or sprawling, it needs slicing.**

### 🎯 Outcome → Meaningful Result

**"What will change once this is done?"**

- Will this give us clarity, value, or unlock something else?
- How will we measure success — learning, delivery, or stability?
- What does "done" look like in a way others can see?

> **✅ If the outcome is fuzzy, stop and clarify.**

## Features

- Break down complex tasks into smaller subtasks
- LLM-driven scope estimation & breakdown
- Interactive task breakdown with alternative approaches
- Automatic fixing of inconsistent time estimates
- Checkpointing (pause & resume)
- Auto-detect when child tasks take more time than parents
- Auto-adjust parent scope estimates based on child complexity
- Pydantic validation
- Cross-platform support (Windows, macOS, Linux)
- Works with Python 3.10 and above
- Automatic Markdown export of plans for easy sharing

## Requirements

- Python 3.10 or higher
- OpenAI API key set as environment variable (`OPENAI_API_KEY`)

## Installation

### From PyPI (Recommended)

The easiest way to install scopemate is from PyPI:

```bash
# Install using pip (any platform)
pip install scopemate

# Or using pip3 on some systems
pip3 install scopemate
```

### Platform-Specific Installation Scripts

#### macOS and Linux

```bash
# Clone the repository
git clone https://github.com/atmb4u/scopemate.git
cd scopemate

# Install using the script (automatically checks Python version)
./install.sh
```

#### Windows

```powershell
# Clone the repository
git clone https://github.com/atmb4u/scopemate.git
cd scopemate

# Install using the script (automatically checks Python version)
.\install.bat
```

### Manual Installation from Source

```bash
# Clone the repository
git clone https://github.com/atmb4u/scopemate.git
cd scopemate

# Install in development mode
pip install -e .
```

### Setting up the OpenAI API Key

scopemate requires an OpenAI API key to function. Set it as an environment variable:

#### macOS/Linux
```bash
export OPENAI_API_KEY=your-api-key-here
```

#### Windows Command Prompt
```cmd
set OPENAI_API_KEY=your-api-key-here
```

#### Windows PowerShell
```powershell
$env:OPENAI_API_KEY = "your-api-key-here"
```

For permanent setup, add this to your shell profile or environment variables.

## Usage

### Quick Start

```bash
# Run in interactive mode (recommended for first-time users)
scopemate --interactive
```

### Command-line Options

```bash
# Get help and see all available options
scopemate --help

# Generate a project plan with purpose and outcome
scopemate --purpose="Build a REST API for user management" --outcome="A documented API with authentication and user CRUD operations" --output="project_plan.json"
```

**Note:** A Markdown version of the output is automatically generated alongside the JSON file. For example, if you specify `--output="project_plan.json"`, a file named `project_plan.md` will also be created.

### Interactive Mode Workflow

The interactive mode (`scopemate --interactive`) will guide you through:

1. **Initial Setup**:
   - Create a new task or load an existing plan
   - Set the main purpose and intended outcome

2. **Task Definition**:
   - Define the scope of work
   - Set dependencies and identify risks
   - Define acceptance criteria

3. **Task Breakdown**:
   - Automatically break down complex tasks into manageable subtasks
   - Review and modify suggested breakdowns
   - Explore alternative approaches to solving the problem

4. **Validation and Refinement**:
   - Automatically detect and fix inconsistent time estimates
   - Check for tasks where children take more time than parents
   - Adjust parent scope estimates based on child complexity

5. **Save and Export**:
   - Save your plan to a JSON file
   - Resume work later using checkpoints

### Output Format

scopemate generates both JSON and Markdown output files:

1. **JSON Output** - Structured data format with the following structure:

```json
{
  "tasks": [
    {
      "id": "TASK-abc123",
      "title": "Task title",
      "purpose": {
        "detailed_description": "Why this task matters",
        "alignment": ["Strategic goal 1", "Strategic goal 2"],
        "urgency": "strategic"
      },
      "scope": {
        "size": "complex",
        "time_estimate": "sprint",
        "dependencies": ["Dependency 1"],
        "risks": ["Risk 1", "Risk 2"]
      },
      "outcome": {
        "type": "customer-facing",
        "detailed_outcome_definition": "What will be delivered",
        "acceptance_criteria": ["Criterion 1", "Criterion 2"],
        "metric": "Success measurement",
        "validation_method": "How to validate"
      },
      "meta": {
        "status": "backlog",
        "priority": 1,
        "created": "2023-06-01T12:00:00Z",
        "updated": "2023-06-01T12:00:00Z",
        "due_date": null,
        "confidence": "medium"
      },
      "parent_id": null
    }
  ]
}
```

2. **Markdown Output** - Human-readable format automatically generated with the same basename as the JSON file. The Markdown output includes:
   - A summary of the plan with task counts and complexity breakdown
   - Hierarchical task structure preserving parent-child relationships
   - All relevant task details formatted for easy reading
   - Properly formatted sections for purpose, scope, outcome, and metadata

This dual output approach makes it easy to both process the data programmatically (using the JSON) and share the plan with team members (using the Markdown).

### Integrating with Other Tools

You can use scopemate's JSON output with other project management tools:

- Import tasks into JIRA using their API
- Convert to CSV for import into spreadsheets
- Integrate with custom project dashboards

## Development

### Setting Up Development Environment

#### Prerequisites

- Python 3.10 or higher
- Git

#### Using pip

```bash
# Clone the repository
git clone https://github.com/atmb4u/scopemate.git
cd scopemate

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .
```

#### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver:

```bash
# Install uv if you don't have it
pip install uv

# Clone the repository
git clone https://github.com/atmb4u/scopemate.git
cd scopemate

# Install development dependencies with uv
uv pip install -r requirements-dev.txt

# Install the package in development mode
uv pip install -e .
```

#### Using pipx

[pipx](https://github.com/pypa/pipx) is useful for installing and running Python applications in isolated environments:

```bash
# Install pipx if you don't have it
pip install pipx

# Clone the repository
git clone https://github.com/atmb4u/scopemate.git
cd scopemate

# Install the package in development mode with force flag
# This is useful when making changes and wanting to test the CLI immediately
pipx install --force .
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run a specific test file
pytest tests/test_basic.py

# Run tests with coverage report
pytest --cov=scopemate
```

### Building Distribution Packages

#### macOS and Linux

```bash
# Build distribution packages
./publish.sh

# Upload to PyPI (when ready)
twine upload dist/*
```

#### Windows

```powershell
# Build distribution packages
.\publish.bat

# Upload to PyPI (when ready)
twine upload dist/*
```

### Code Style and Linting

We use ruff for linting and code formatting:

```bash
# Run linter
ruff check src tests

# Format code
ruff format src tests
```

### Testing Cross-Platform Compatibility

Use tox to test across multiple Python versions:

```bash
# Install tox
pip install tox

# Run tox
tox

# Run tox for a specific Python version
tox -e py310
```

## Repository Structure

```
.
├── LICENSE             # MIT License
├── MANIFEST.in         # Package manifest
├── README.md           # Project documentation
├── publish.sh          # Build and publish script (Unix)
├── publish.bat         # Build and publish script (Windows)
├── install.sh          # Installation script (Unix)
├── install.bat         # Installation script (Windows)
├── pyproject.toml      # Project configuration
├── requirements.txt    # Project dependencies
├── requirements-dev.txt # Development dependencies
├── setup.py            # Package setup
├── tox.ini             # Tox configuration
├── tests/              # Test directory
│   ├── __init__.py     # Test package initialization
│   ├── test_basic.py   # Basic tests
│   └── test_platform.py # Platform compatibility tests
└── src/                # Source code
    └── scopemate/      # Main package
        ├── __init__.py # Package initialization
        ├── __main__.py # Entry point
        ├── breakdown.py # Task breakdown logic
        ├── cli.py      # Command-line interface
        ├── core.py     # Core functionality
        ├── engine.py   # Main application logic
        ├── interaction.py # User interaction helpers
        ├── llm.py      # LLM integration
        ├── models.py   # Data models
        ├── storage.py  # Task storage
        └── task_analysis.py # Task analysis helpers
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.