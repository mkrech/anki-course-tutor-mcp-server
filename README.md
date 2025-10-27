# Anki Course Tutor MCP Server

AI-powered learning system that combines Anki's spaced repetition with personality-driven tutoring.

## Features

- 🎓 **Chat-based Learning** - Natural conversation interface via MCP
- 🎭 **Personality Rotation** - AI tutor alternates between Normal (3x) and Pirate (1x) modes
- ✅ **User Review System** - Confirm or override automatic answer evaluation
- 📊 **Progress Tracking** - Detailed statistics and learning analytics
- 🔄 **Simple SRS** - Retry incorrect cards automatically
- 🎯 **Flexible Modes** - Explain mode (with AI explanations) or Test mode (assessment only)

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

# Create virtual environment
python3.13 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Or with uv (faster)
uv pip install -e ".[dev]"
```

## Configuration

Edit `config.yaml` to customize:

- Anki connection settings
- Tutor personalities and weights
- Learning modes
- Evaluation behavior
- Storage paths

## Usage with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "anki-tutor": {
      "command": "/path/to/.venv/bin/python",
      "args": ["-m", "anki_course_tutor"]
    }
  }
}
```

## Chat Example

```
You: "List my Anki decks"
AI: [calls list_decks] "You have: Spanish Vocabulary, Programming, History"

You: "Start learning Spanish Vocabulary"
AI: [calls start_session] "Session started! Ready for the first card?"

You: "Yes"
AI: [calls get_next_card] "¿Cómo estás?"

You: "How are you?"
AI: [evaluates] "I think that's CORRECT! Do you agree? (yes/no)"

You: "yes"
AI: "Great! ✓ Next card?"
```

## Development

```bash
# Run tests
pytest

# Lint and format
ruff check .
ruff format .

# Type checking
ruff check --select=F,I,B,C4,UP
```

## License

MIT

## Status

🚧 Work in Progress - Currently implementing MVP features
