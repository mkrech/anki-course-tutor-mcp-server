# Anki Course Tutor MCP Server

AI-powered learning system that combines Anki's spaced repetition with personality-driven tutoring via chat interface.

[![Tests](https://img.shields.io/badge/tests-102%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-74%25-green)](htmlcov/)
[![Python](https://img.shields.io/badge/python-3.13+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

## ✨ Features

- 🎓 **Chat-based Learning** - Natural conversation interface via MCP
- 🎭 **Personality Rotation** - AI tutor alternates between Normal (3x) and Pirate (1x) modes
- ✅ **User Review System** - Confirm or override automatic answer evaluation
- 📊 **Progress Tracking** - Detailed statistics and learning analytics
- 🔄 **Simple SRS** - Retry incorrect cards automatically
- 🎯 **Flexible Modes** - Explain mode (with AI explanations) or Test mode (assessment only)
- 🔌 **11 MCP Tools** - Complete learning workflow via chat interface
- 📝 **3 Card Types** - Support for Basic, Cloze, and Multiple Choice cards

## Prerequisites

1. [Anki](https://apps.ankiweb.net/) installed and running
2. [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on installed
3. Python 3.13+
4. [uv](https://github.com/astral-sh/uv) for package management

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd anki-course-tutor-mcp-server

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e ".[dev]"
```

## Anki Setup

1. Install [Anki](https://apps.ankiweb.net/)
2. Install [AnkiConnect addon](https://ankiweb.net/shared/info/2055492159):
   - Open Anki → Tools → Add-ons → Get Add-ons
   - Enter code: `2055492159`
   - Restart Anki
3. Keep Anki running in the background when using the tutor

## Configuration

Edit `config.yaml` to customize:

- Anki connection settings
- Tutor personalities and weights
- Learning modes
- Evaluation behavior
- Storage paths

## Usage with Claude Desktop

Add to your `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "anki-course-tutor": {
      "command": "uv",
      "args": [
        "--directory",
        "/full/path/to/anki-course-tutor-mcp-server",
        "run",
        "anki-course-tutor"
      ]
    }
  }
}
```

Restart Claude Desktop to load the MCP server.

## 💬 Usage Examples

### Starting a Session

```
You: List my Anki decks
AI: I found these decks:
    1. Spanish Vocabulary (150 cards)
    2. Python Programming (87 cards)

You: Start a learning session with Spanish Vocabulary in EXPLAIN mode
AI: ✓ Created session abc-123 with 150 cards
    Ready to begin! Type "next card" to start.
```

### Learning with Review

```
You: Next card
AI: 📝 Card 1/150
    Question: ¿Cómo estás?

You: How are you?
AI: 🤔 I think this is CORRECT!
    Expected: "How are you?" or "How do you do?"
    
    Do you agree? (yes/no)

You: yes
AI: ✅ Correct! Progress: 1/150 cards completed
```

### Getting Explanations (EXPLAIN Mode)

```
You: What hour is it?
AI: 🤔 I think this is INCORRECT.
    Expected: "What time is it?"
    
    Do you agree? (yes/no)

You: yes
AI: Let me explain:
    
    "¿Qué hora es?" translates to "What time is it?" in English. 
    While "hour" and "time" are related, we use "What time" as the 
    standard expression. Think of "time" as the specific point on 
    the clock, while "hour" is more about duration.
```

### Pirate Personality (Every 4th Explanation)

```
AI: Arrr! Let me explain this, matey!
    
    "Estar" be the verb for temporary states, like how ye be feelin' 
    right now, savvy? "Ser" be for permanent things, like yer name!
```

## 🏗️ Architecture

### State Machine

```
NOT_STARTED → PRESENTING_CARD → AWAITING_ANSWER
                                      ↓
                               EVALUATING
                                      ↓
                              AWAITING_REVIEW
                                   ↙    ↘
                         (correct)        (incorrect)
                              ↓                ↓
                   AWAITING_ANSWER ← EXPLAINING
                              ↓
                   SESSION_COMPLETE
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `list_decks` | List all available Anki decks |
| `start_session` | Create new learning session |
| `resume_session` | Resume paused session |
| `get_next_card` | Present next card question |
| `submit_answer` | Submit answer for evaluation |
| `confirm_evaluation` | Confirm/override evaluation |
| `get_explanation` | Get AI explanation (EXPLAIN mode) |
| `get_session_stats` | Get session statistics |
| `end_session` | Complete and save session |

## Configuration

Edit `config.yaml` to customize settings:

```yaml
anki:
  connect_url: "http://localhost:8765"
  connect_timeout: 10

tutor:
  personalities:
    - name: "normal"
      ratio: 3
    - name: "pirate"
      ratio: 1
  modes:
    explain:
      max_sentences: 5

learning:
  simple_srs:
    retry_incorrect: true
  evaluation:
    case_sensitive: false
```

## Development

```bash
# Run tests (102 tests, 74% coverage)
uv run pytest

# Run with coverage report
uv run pytest --cov=src --cov-report=html

# Lint and format
ruff check src/ tests/
ruff format src/ tests/

# Type checking
ruff check --select=F,I,B,C4,UP
```

### Project Structure

```
anki-course-tutor-mcp-server/
├── src/anki_course_tutor/
│   ├── mcp_server.py         # FastMCP tools and resources
│   ├── learning_engine.py    # State machine and evaluation
│   ├── session_manager.py    # Session CRUD
│   ├── progress_tracker.py   # Statistics and persistence
│   ├── scheduler.py          # Card scheduling
│   ├── ai_tutor.py           # Personality and explanations
│   └── anki_client.py        # Anki integration
├── tests/                    # 102 tests
├── docs/                     # Documentation
│   └── MANUAL_TESTING.md     # Testing guide
└── data/                     # Sessions and progress (gitignored)
```

## 🐛 Troubleshooting

**"AnkiConnect not available"**
- Ensure Anki is running
- Verify AnkiConnect addon is installed
- Test connection: `curl http://localhost:8765`

**"Deck not found"**
- Check deck name is exact (case-sensitive)
- Verify deck contains cards
- Refresh Anki

See [docs/MANUAL_TESTING.md](docs/MANUAL_TESTING.md) for detailed troubleshooting.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

Key points:
- Follow ruff formatting
- Add tests for new features (target: 80% coverage)
- Update OpenSpec proposals for significant changes
- Use type hints everywhere

## License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

Copyright 2025 Michael Krech

## Status

✅ **MVP Complete** - All core features implemented with 102 passing tests (74% coverage)
