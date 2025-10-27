# Contributing to Anki Course Tutor MCP Server

Thank you for your interest in contributing! This guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [OpenSpec Process](#openspec-process)
- [Pull Request Process](#pull-request-process)
- [Architecture Guidelines](#architecture-guidelines)

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Follow the project's technical standards

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) package manager
- Anki with AnkiConnect addon (for integration testing)
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/anki-course-tutor-mcp-server.git
cd anki-course-tutor-mcp-server

# Install dependencies with dev tools
uv sync

# Install pre-commit hooks (optional but recommended)
uv run pre-commit install
```

### Project Structure

```
anki-course-tutor-mcp-server/
├── src/anki_course_tutor/     # Main source code
│   ├── __main__.py            # Entry point
│   ├── mcp_server.py          # MCP tools (11 tools + 2 resources)
│   ├── learning_engine.py     # State machine (7 states)
│   ├── session_manager.py     # Session CRUD
│   ├── progress_tracker.py    # Statistics & persistence
│   ├── scheduler.py           # Two-queue scheduling
│   ├── ai_tutor.py            # Personality rotation & explanations
│   ├── anki_client.py         # Anki integration
│   ├── config.py              # Configuration management
│   └── models/                # Data models
├── tests/                     # Test suite (102 tests)
├── docs/                      # Documentation
├── openspec/                  # Project specifications
│   ├── project.md             # Project overview
│   └── changes/               # Change proposals
└── config.yaml                # Default configuration
```

## Development Workflow

### 1. Create a Branch

```bash
# For features
git checkout -b feature/your-feature-name

# For bug fixes
git checkout -b fix/issue-description

# For documentation
git checkout -b docs/what-you-are-documenting
```

### 2. Make Changes

- Write clean, readable code
- Follow existing patterns and conventions
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_learning_engine.py -v

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Check coverage report
open htmlcov/index.html
```

### 4. Lint and Format

```bash
# Check for linting issues
uv run ruff check src/ tests/

# Auto-fix issues
uv run ruff check --fix src/ tests/

# Format code
uv run ruff format src/ tests/

# Type checking (optional)
uv run mypy src/
```

## Testing

### Writing Tests

- Place tests in `tests/` directory
- Follow naming convention: `test_<module>.py`
- Use descriptive test names: `test_<what>_<when>_<expected>`
- Aim for 80% coverage minimum

Example test structure:

```python
"""Tests for learning engine."""

import pytest

from anki_course_tutor.learning_engine import LearningEngine
from anki_course_tutor.models import Card, CardType, Session

class TestLearningEngine:
    """Test suite for LearningEngine."""
    
    def test_start_session_sets_state_correctly(self, sample_session, sample_cards):
        """Test that starting a session transitions to AWAITING_ANSWER state."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.EXPLAIN)
        engine.start()
        
        assert engine.session.state == LearningState.AWAITING_ANSWER
        assert engine.current_card is not None
```

### Fixtures

Use pytest fixtures for common test data:

```python
@pytest.fixture
def sample_cards():
    """Create sample cards for testing."""
    return [
        Card(
            id="card-1",
            type=CardType.BASIC,
            question="What is Python?",
            answer="A programming language",
            deck="Test"
        )
    ]
```

### Async Tests

For async functions, use `pytest.mark.asyncio`:

```python
@pytest.mark.asyncio
async def test_get_explanation_generates_text(self):
    """Test AI explanation generation."""
    tutor = AITutor()
    explanation = await tutor.generate_explanation(
        card=sample_card,
        user_answer="wrong",
        personality=Personality.NORMAL
    )
    
    assert len(explanation) > 0
```

## Code Style

### General Principles

- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Document all public functions and classes
- **Constants**: Use UPPER_CASE for constants
- **Private Methods**: Prefix with underscore `_method_name`
- **Line Length**: Max 100 characters (enforced by ruff)

### Example

```python
"""Module for card scheduling logic."""

from collections import deque
from typing import List

from anki_course_tutor.models import Card

class SimpleLearningScheduler:
    """Scheduler with two-queue system for new and retry cards.
    
    Args:
        cards: List of cards to schedule
    """
    
    def __init__(self, cards: list[Card]) -> None:
        """Initialize scheduler with cards."""
        self.new_queue: deque[Card] = deque(cards)
        self.retry_queue: deque[Card] = deque()
        self.completed_cards: list[Card] = []
    
    def get_next_card(self) -> Card | None:
        """Get next card prioritizing new cards over retries.
        
        Returns:
            Next card to present or None if no cards available
        """
        if self.new_queue:
            return self.new_queue.popleft()
        if self.retry_queue:
            return self.retry_queue.popleft()
        return None
```

### Imports

Order imports according to ruff/isort:

1. Standard library
2. Third-party packages
3. Local modules

```python
import json
import logging
from pathlib import Path

from fastmcp import FastMCP
import pytest

from anki_course_tutor.models import Card, Session
from anki_course_tutor.learning_engine import LearningEngine
```

## OpenSpec Process

For significant changes (new features, breaking changes, architecture shifts), follow the OpenSpec process:

### 1. Create a Proposal

```bash
# Create proposal directory
mkdir -p openspec/changes/your-feature-name

# Create proposal document
touch openspec/changes/your-feature-name/proposal.md
```

### 2. Proposal Template

```markdown
# Proposal: [Feature Name]

## Summary
Brief description of the change

## Motivation
Why is this change needed?

## Design
How will it be implemented?

## Impact
- Breaking changes?
- Performance implications?
- New dependencies?

## Testing
How will it be tested?

## Alternatives
What other approaches were considered?
```

### 3. Implementation

Create `tasks.md` with specific implementation steps:

```markdown
## 1. [Task Name]
- [ ] 1.1 Subtask description
- [ ] 1.2 Subtask description

## 2. [Next Task]
- [ ] 2.1 Subtask description
```

### 4. Review and Merge

- Get feedback on proposal before implementing
- Implement according to tasks
- Update proposal with any changes during implementation

## Pull Request Process

### Before Submitting

1. ✅ All tests pass: `uv run pytest`
2. ✅ Linting clean: `uv run ruff check src/ tests/`
3. ✅ Code formatted: `uv run ruff format src/ tests/`
4. ✅ Coverage maintained: `uv run pytest --cov=src`
5. ✅ Documentation updated
6. ✅ CHANGELOG.md updated (if applicable)

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Added unit tests
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

### Review Process

- PRs require at least one approval
- Address all review comments
- Keep PRs focused and reasonably sized
- Respond to feedback promptly

## Architecture Guidelines

### State Machine

When modifying `learning_engine.py`:

- Maintain the 7-state flow
- Ensure all state transitions are valid
- Add tests for new state transitions

States:
1. NOT_STARTED
2. PRESENTING_CARD
3. AWAITING_ANSWER
4. EVALUATING
5. AWAITING_REVIEW
6. EXPLAINING
7. SESSION_COMPLETE

### MCP Tools

When adding MCP tools to `mcp_server.py`:

- Use `@mcp.tool()` decorator
- Provide clear descriptions
- Handle errors gracefully
- Return structured data
- Add integration tests

```python
@mcp.tool()
async def your_new_tool(param: str) -> dict[str, Any]:
    """Tool description for MCP client.
    
    Args:
        param: Parameter description
        
    Returns:
        Dictionary with results
    """
    try:
        # Implementation
        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Tool error: {e}")
        return {"success": False, "error": str(e)}
```

### Data Models

When adding models to `models/`:

- Use `@dataclass` for simplicity
- Add type hints
- Include `__post_init__` for validation if needed
- Keep models immutable when possible

```python
from dataclasses import dataclass
from enum import Enum

@dataclass
class NewModel:
    """Description of model."""
    
    field1: str
    field2: int
    field3: list[str] | None = None
    
    def __post_init__(self):
        """Validate model data."""
        if self.field2 < 0:
            raise ValueError("field2 must be non-negative")
```

### Async/Await

- Use async for I/O operations (AI API calls, file operations)
- Don't use async for CPU-bound operations
- Await all async calls properly
- Handle async exceptions

## Common Tasks

### Adding a New Card Type

1. Update `CardType` enum in `models/card.py`
2. Add conversion logic in `anki_client.py`
3. Update evaluation logic in `learning_engine.py`
4. Add tests in `tests/test_learning_engine.py`
5. Update documentation

### Adding a New Personality

1. Update `Personality` enum in `models/__init__.py`
2. Add prompt template in `ai_tutor.py`
3. Update rotation logic if needed
4. Add tests in `tests/test_ai_tutor.py`
5. Update config.yaml example

### Adding a New MCP Tool

1. Define tool in `mcp_server.py`
2. Implement business logic
3. Add error handling
4. Create tests in `tests/test_mcp_server.py`
5. Update README with tool documentation

## Questions?

- 📖 Check [docs/MANUAL_TESTING.md](docs/MANUAL_TESTING.md)
- 💬 Open a [Discussion](https://github.com/yourusername/anki-course-tutor-mcp-server/discussions)
- 🐛 Report [Issues](https://github.com/yourusername/anki-course-tutor-mcp-server/issues)

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
