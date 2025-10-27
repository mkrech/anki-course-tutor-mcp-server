# Project Context

## Purpose
Build an AI-powered learning system that combines Anki's spaced repetition flashcards with engaging AI tutoring. The system imports existing Anki decks and provides a chat-based interface where an AI tutor with rotating personalities helps students learn more effectively through contextual explanations.

## Tech Stack
- Python 3.10+
- uv (package manager and build tool)
- ruff (linting and formatting)
- FastMCP SDK for Python (AI integration)
- anki-mcp-server (Anki integration dependency)
- AnkiConnect (external Anki add-on)

## Project Conventions

### Code Style
- Use ruff for formatting and linting
- Follow PEP 8 conventions
- Type hints required for all public APIs
- Docstrings in Google style format
- Maximum line length: 100 characters

### Architecture Patterns
- Separate concerns: session, learning, tutor, progress, anki integration
- State machine pattern for learning flow
- Anti-corruption layer for external dependencies (Anki)
- Domain models separate from persistence (Card, Session, Progress)
- MCP tools for user interaction
- JSON for data persistence

### Testing Strategy
- Unit tests for all core logic
- Integration tests with mock Anki and AI
- Test coverage minimum: 80%
- Use pytest as test framework
- Mock external dependencies (AnkiConnect, FastMCP)

### Git Workflow
- Conventional commits
- Feature branches from main
- Squash and merge to main
- Tag releases with semantic versioning

## Domain Context
- **Anki**: Spaced repetition flashcard software
- **AnkiConnect**: Anki add-on providing HTTP API
- **MCP**: Model Context Protocol for LLM-tool integration
- **FastMCP**: Python SDK for building MCP servers
- **Note Types**: Templates defining card structure (Basic, Cloze, custom)
- **Decks**: Organizational containers for cards
- **Sessions**: Learning sessions with progress tracking
- **Spaced Repetition**: Learning technique with increasing intervals
- **Card Types**: Basic (Q&A), Cloze (fill-in-blank), Multiple Choice

## Important Constraints
- Must maintain compatibility with anki-mcp-server
- Chat-based interaction via MCP (no standalone GUI)
- Local data storage only (no cloud sync for MVP)
- Model-agnostic AI integration (works with any MCP-compatible LLM)
- Simple spaced repetition for MVP (retry incorrect cards, not SM-2/FSRS)

## External Dependencies
- anki-mcp-server: Provides AnkiConnect client wrapper
- Anki Desktop: Must be running with AnkiConnect add-on
- FastMCP: Handles AI communication
- MCP-compatible AI client: Claude Desktop, or similar
