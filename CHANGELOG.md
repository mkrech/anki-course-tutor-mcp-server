# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Anki Scheduler Integration**: Reviews now submitted directly to Anki Desktop via AnkiConnect
  - `answer_card()` API method for submitting reviews
  - `get_card_info()` API method for retrieving card state
  - `get_reviews_of_cards()` API method for review history
  - Binary ease mapping: correct=4 (Easy), incorrect=1 (Again)
- Configuration flag `use_anki_scheduler` in config.yaml (default: true)
- AnkiClient integration in LearningEngine with async review submission
- 5 new integration tests for Anki scheduler functionality
- Comprehensive troubleshooting guide for AnkiConnect setup
- Manual testing guide for AnkiWeb sync workflow

### Changed
- `LearningEngine.confirm_evaluation()` is now async
- MCP server `confirm_evaluation` tool is now async
- Updated all affected tests to use async/await patterns
- README updated with Anki scheduler documentation
- Test count decreased from 111 to 100 tests (11 scheduler tests removed)
- Code coverage: 74%
- **Architecture Simplification**: Removed `SimpleLearningScheduler` class
  - Card management now directly uses session state (`_cards` list, `_retry_queue` deque)
  - Retry queue persisted in `Session.retry_queue` field
  - Statistics calculated from session data instead of scheduler state
  - New cards prioritized first, then retry cards (same behavior as before)
  - Anki is now the single source of truth for long-term scheduling

### Removed
- **Personality System**: Removed personality rotation feature for simplified codebase
  - Removed `Personality` enum and `PersonalityRotation` class
  - Removed pirate personality prompts and rotation logic
  - Removed 9 personality-related tests
  - Simplified AITutor to single prompt template
  - Updated all documentation to remove personality references
- Removed `personality_count` field from Session model
- **SimpleLearningScheduler**: Removed separate scheduler class
  - Deleted `src/anki_course_tutor/scheduler.py` (109 lines)
  - Deleted `tests/test_scheduler.py` (11 tests)
  - Card management integrated directly into `LearningEngine`
  - Simpler architecture with Anki as single scheduling authority

### Fixed
- All 111 tests now passing
- No unused imports (verified with ruff)
- Consistent async/await usage throughout codebase

### Architecture
- **Simplified Card Management**: Direct session-based iteration
  - `LearningEngine` uses `_cards` list, `_current_index`, and `_retry_queue`
  - New cards prioritized first, then retry queue
  - Session state persisted in `Session.retry_queue` and `Session.current_card_index`
  - No separate scheduler layer needed
- **Anki Integration**: Anki scheduler handles long-term spaced repetition (SRS)
  - Local card management for within-session ordering
  - Anki SM-2 algorithm for cross-session intervals and due dates
- Two-tier architecture: local session management + Anki SRS
- Fail-fast error handling for Anki connectivity issues

## [0.1.0] - 2025-10-27

### Added
- Initial MVP release
- Chat-based learning via MCP (Model Context Protocol)
- 11 MCP tools for complete learning workflow
- Support for 3 card types: Basic, Cloze, Multiple Choice
- Automatic answer evaluation
- User review/override system
- AI-powered explanations for incorrect answers
- Progress tracking with JSON storage
- Session management with pause/resume
- Session-based card management (new cards + retry queue)
- AnkiConnect integration for deck import
- Comprehensive test suite (100 tests)
- Documentation: README, CONTRIBUTING, MANUAL_TESTING

### Technical Details
- Python 3.13+ with uv package manager
- FastMCP SDK for MCP server implementation
- pytest for testing with asyncio support
- OpenSpec for spec-driven development
- Type hints throughout codebase
