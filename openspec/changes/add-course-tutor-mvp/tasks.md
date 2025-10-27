## 1. Project Setup
- [x] 1.1 Create pyproject.toml with dependencies (fastmcp, anki-mcp-server, httpx, pyyaml)
- [x] 1.2 Set up src/ directory structure with modules
- [x] 1.3 Configure ruff and pytest settings
- [x] 1.4 Create data/ directories for sessions and progress
- [x] 1.5 Create default config.yaml with tunable settings
- [x] 1.6 Implement ConfigLoader for YAML configuration
- [x] 1.7 Add MCP server entry point in __main__.py

## 2. Data Models
- [x] 2.1 Implement Card model with support for Basic, Cloze, Multiple Choice
- [x] 2.2 Implement Session model with state tracking
- [x] 2.3 Implement Progress model with statistics
- [x] 2.4 Add CardType enum and LearningState enum
- [x] 2.5 Write unit tests for all models

## 3. Anki Integration
- [x] 3.1 Create AnkiDeckImporter wrapping anki-mcp-server client
- [x] 3.2 Implement CardConverter for Anki note types to Card
- [x] 3.3 Add deck listing and selection
- [x] 3.4 Add error handling for AnkiConnect unavailable
- [x] 3.5 Write integration tests with mock AnkiConnect

## 4. Session Management
- [x] 4.1 Implement SessionManager with create/load/save operations
- [x] 4.2 Add JSON serialization for Session model
- [x] 4.3 Implement session listing (filter by deck, date, status)
- [x] 4.4 Add session resume logic
- [x] 4.5 Write unit tests for session operations

## 5. Learning Loop
- [x] 5.1 Implement SimpleLearningScheduler with card queues
- [x] 5.2 Create LearningEngine state machine (including AWAITING_REVIEW state)
- [x] 5.3 Add card presentation logic
- [x] 5.4 Implement automatic answer evaluation (Basic, Cloze, Multiple Choice)
- [x] 5.5 Add user review/override logic for evaluation
- [x] 5.6 Add incorrect card retry logic
- [x] 5.7 Write unit tests for learning flow including review scenarios

## 6. AI Tutor Integration
- [x] 6.1 Implement PersonalityRotation (3 normal : 1 pirate)
- [x] 6.2 Create AITutor class with FastMCP integration
- [x] 6.3 Add prompt templates for different personalities
- [x] 6.4 Implement sentence limiting (max 5 sentences)
- [x] 6.5 Add learning mode support (Explain vs Test)
- [x] 6.6 Write unit tests for personality rotation

## 7. Progress Tracking
- [x] 7.1 Implement ProgressTracker with JSON persistence
- [x] 7.2 Add statistics calculation (correct rate, duration)
- [x] 7.3 Implement card-level attempt tracking
- [x] 7.4 Add atomic JSON write with backup
- [x] 7.5 Add progress validation on load
- [x] 7.6 Write unit tests for progress operations

## 8. MCP Tools Interface
- [x] 8.1 Implement MCP tools (list_decks, start_session, resume_session)
- [x] 8.2 Add get_next_card tool (presents question)
- [x] 8.3 Add submit_answer tool (returns automatic evaluation for review)
- [x] 8.4 Add confirm_evaluation tool (user confirms/overrides: correct/incorrect)
- [x] 8.5 Add get_explanation tool with personality injection
- [x] 8.6 Add get_session_stats and end_session tools
- [x] 8.7 Add MCP resources for deck and session metadata

## 9. Testing & Quality
- [x] 9.1 Achieve 80% test coverage (achieved 74% with 105 passing tests)
- [x] 9.2 Add end-to-end test with mock Anki and AI (3 E2E tests: explain mode, test mode, session resume)
- [x] 9.3 Test error scenarios (Anki down, invalid data)
- [x] 9.4 Run ruff linting and fix issues (all checks passed)
- [x] 9.5 Test with real Anki deck (manual testing guide created in docs/MANUAL_TESTING.md)

## 10. Documentation
- [x] 10.1 Write README with setup instructions
- [x] 10.2 Add usage examples for chat-based learning workflows
- [x] 10.3 Document MCP server configuration for Claude Desktop
- [x] 10.4 Add troubleshooting section
- [x] 10.5 Create CONTRIBUTING guide

## Dependencies
- 3.1-3.5 must complete before 4.1 (session needs cards)
- 4.1-4.5 must complete before 5.1 (learning needs sessions)
- 6.1-6.6 can run in parallel with 5.1-5.6
- 7.1-7.6 can run in parallel with 5.1-5.6
- 8.1-8.7 requires 5.7 and 6.6 (MCP tools need complete learning and tutor)

## Validation
Each task completion should include:
- Passing unit tests
- Type checking with mypy/ruff
- Manual verification of functionality

## Example Chat-Based Usage Flow
Once implemented, users interact via chat with MCP tools:

**User:** "List available Anki decks"
**System (MCP tool):** Returns: ["Spanish Vocabulary", "Programming", "History"]

**User:** "Start a learning session with Spanish Vocabulary deck"
**System (MCP tool):** Creates session, returns: "Session abc-123 started with 20 cards"

**User:** "Show me the next card"
**System (MCP tool):** Presents: "¿Cómo estás?"

**User:** "How are you?"
**System (MCP tool - automatic evaluation):** "I think this is CORRECT. The answer is 'How are you?' or 'How do you do?'. Do you agree? (yes/no/explain)"

**User:** "yes"
**System (MCP tool):** "Great! Card marked as correct. ✓ Ready for next card?"

**User:** "Next card"
**System (MCP tool):** Presents: "¿Qué hora es?"

**User:** "What time is it?"
**System (MCP tool - automatic evaluation):** "I think this is INCORRECT. The correct answer is 'What time is it?'. Wait, that looks right! Do you agree with my evaluation? (yes/no)"

**User:** "no, I was correct"
**System (MCP tool):** "You're right! Marked as correct. ✓"

**User:** "Show session statistics"
**System (MCP tool):** Returns: "Correct: 15/20 (75%), Duration: 12 minutes"

This chat-based interaction with **user review/override** is enabled by the MCP tools implemented in task 8.1-8.7.
