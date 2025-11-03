# Anki Course Tutor MCP Server

AI-powered learning system that combines Anki's spaced repetition with AI-driven tutoring via chat interface.

[![Tests](https://img.shields.io/badge/tests-102%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-74%25-green)](htmlcov/)
[![Python](https://img.shields.io/badge/python-3.13+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)

## ✨ Features

- 🎓 **Chat-based Learning** - Natural conversation interface via MCP
- 🤖 **AI Explanations** - Contextual explanations for incorrect answers
- ✅ **User Review System** - Confirm or override automatic answer evaluation
- 📊 **Progress Tracking** - Detailed statistics and learning analytics
- 🔄 **Anki Scheduler Integration** - Submit reviews directly to Anki's spaced repetition system
- 🎯 **Flexible Modes** - Explain mode (with AI explanations) or Test mode (assessment only)
- 🔌 **11 MCP Tools** - Complete learning workflow via chat interface
- 📝 **Multiple Card Types** - Basic, Cloze, Multiple Choice (MC), Single Choice (SC), and KPRIM
- 🎨 **Flexible Answer Formats** - Accept R/F, T/F, Y/N, or 1/0 for KPRIM questions

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

### Anki Connection & Scheduler

```yaml
anki:
  connect_url: "http://localhost:8765"  # AnkiConnect URL
  connect_timeout: 30                    # Connection timeout (seconds)
  retry_attempts: 3                      # Number of retry attempts
  use_anki_scheduler: true               # Enable Anki scheduler integration
```

**Scheduler Integration:**
- When `use_anki_scheduler: true`, reviews are submitted to Anki's native spaced repetition scheduler
- Cards will appear in Anki with updated due dates based on your answers
- **Ease mapping**: Correct = 4 (Easy), Incorrect = 1 (Again)
- Requires Anki Desktop running with AnkiConnect
- Set to `false` for local-only mode (no Anki scheduler updates)

**Requirements:**
- Anki Desktop must be running
- AnkiConnect addon installed and enabled
- Cards must have numeric IDs from Anki

### Other Settings

- **Tutor personalities and weights** - Control Normal/Pirate rotation
- **Learning modes** - EXPLAIN (with AI) or TEST (assessment only)
- **Evaluation behavior** - Case sensitivity, whitespace handling
- **Storage paths** - Session and progress data locations

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

### KPRIM Questions with Flexible Formats

```
You: Next card
AI: 📝 Card 5/150
    Question: Welche Aussagen über Conditional Parameterization sind korrekt?
    
    Options:
    Q_1: Sie ist die graphische Darstellung von P(G|I)
    Q_2: Sie verwendet bedingte Wahrscheinlichkeitstabellen
    Q_3: Sie ist nur für diskrete Variablen definiert
    Q_4: Sie ermöglicht effiziente Inferenz in Bayesianischen Netzen
    Q_5: Sie ersetzt die Chain Rule vollständig
    
    Hint: Sources: Folie 5 | Extra: Conditional Parameterization ist 
          die graphische Darstellung von P(G|I)

You: RRFRF
AI: You answered: 'RRFRF'
    Correct answer: '1 1 0 1 0'
    
    Was your answer correct? (yes/no)

You: yes
AI: ✅ Correct! Progress: 5/150 cards completed
```

**Supported KPRIM answer formats:**
- **R/F** (German): `RRFRF`, `R,R,F,R,F`, `R R F R F`
- **T/F** (English): `TTFTT`, `T,T,F,T,T`, `T T F T T`
- **Y/N**: `YYNYN`, `Y,Y,N,Y,N`, `Y Y N Y N`
- **1/0** (Numeric): `11010`, `1,1,0,1,0`, `1 1 0 1 0`

All formats are case-insensitive and separator-agnostic.
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
│   ├── ai_tutor.py           # AI explanations
│   └── anki_client.py        # Anki integration
├── tests/                    # 100 tests
├── docs/                     # Documentation
│   └── MANUAL_TESTING.md     # Testing guide
└── data/                     # Sessions and progress (gitignored)
```

## 🐛 Troubleshooting

### AnkiConnect Issues

**"AnkiConnect not available"**
- Ensure Anki Desktop is running
- Verify AnkiConnect addon is installed (Tools → Add-ons)
- Test connection: `curl http://localhost:8765`
- Check AnkiConnect configuration allows local connections

**"Failed to submit review to Anki"**
- Anki Desktop must be running during learning sessions
- Check `use_anki_scheduler: true` in `config.yaml`
- Verify card IDs are numeric (imported from Anki)
- Review AnkiConnect logs in Anki (Tools → Add-ons → AnkiConnect → View Files)

### Deck and Card Issues

**"Deck not found"**
- Check deck name is exact (case-sensitive)
- Verify deck contains cards in Anki
- Refresh Anki deck list
- Try listing decks first to see available names

**"Invalid card ID"**
- Cards must be imported from Anki with numeric IDs
- Cannot use manually created cards with string IDs for scheduler integration
- Set `use_anki_scheduler: false` for local-only mode without Anki updates

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
