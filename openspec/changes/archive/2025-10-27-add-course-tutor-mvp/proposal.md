## Why

Students need an effective learning system that combines structured spaced repetition with engaging AI explanations. Existing solutions either provide repetition without understanding (traditional flashcard apps) or understanding without structure (standalone AI tutors). This system bridges both worlds by integrating existing Anki decks with a personality-driven AI tutor, creating a learning experience that improves both comprehension and long-term retention.

## What Changes

- Add Python package `anki-course-tutor-mcp-server` with chat-based learning system
- Implement session management for courses, chapters, and learning sessions
- Build card learning system supporting Basic, Multiple Choice, and Cloze card types
- Integrate AI tutor with rotating personalities (3 normal : 1 pirate) via FastMCP
- Add progress tracking with JSON-based persistence
- Leverage existing `anki-mcp-server` for Anki deck import
- Support two learning modes: Explain mode (max 5 sentences) and Test mode (no explanations)
- Implement simple spaced repetition logic (incorrect cards repeat at session end)

## Impact

- Affected specs:
  - `session-management` (new)
  - `card-learning` (new) 
  - `ai-tutor` (new)
  - `progress-tracking` (new)
  - `anki-integration` (new)
- Affected code:
  - New package structure under project root
  - Python package with uv/ruff tooling
  - FastMCP SDK integration for AI
  - AnkiConnect integration via anki-mcp-server
  - Chat-based interface for user interaction
