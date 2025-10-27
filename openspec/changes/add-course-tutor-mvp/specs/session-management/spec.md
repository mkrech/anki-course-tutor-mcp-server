## ADDED Requirements

### Requirement: Session Creation
The system SHALL allow users to create new learning sessions by selecting a deck and optional chapter.

#### Scenario: Create session with deck only
- **WHEN** user creates a session with deck name "Spanish Vocabulary"
- **THEN** system creates a new session with all cards from the deck
- **AND** assigns a unique session ID
- **AND** sets session state to "not_started"

#### Scenario: Create session with deck and chapter
- **WHEN** user creates a session with deck "Programming" and chapter "Python Basics"
- **THEN** system creates a session with only cards from that chapter
- **AND** filters cards by chapter metadata or tags

#### Scenario: Invalid deck name
- **WHEN** user attempts to create session with non-existent deck
- **THEN** system returns error "Deck not found"
- **AND** lists available decks

### Requirement: Session Persistence
The system SHALL save session state to JSON files and allow resuming from saved state.

#### Scenario: Save session state
- **WHEN** user answers a card during an active session
- **THEN** system saves updated session state to `data/sessions/{session_id}.json`
- **AND** includes card progress, timestamps, and statistics

#### Scenario: Resume session
- **WHEN** user requests to resume session with ID "abc-123"
- **THEN** system loads session state from JSON file
- **AND** restores learning position and progress
- **AND** continues from next unanswered card

#### Scenario: Session not found
- **WHEN** user attempts to resume non-existent session
- **THEN** system returns error "Session not found"
- **AND** lists available sessions

### Requirement: Session Listing
The system SHALL provide listing and filtering of existing sessions.

#### Scenario: List all sessions
- **WHEN** user requests all sessions
- **THEN** system returns list of sessions with ID, deck name, status, and last updated timestamp

#### Scenario: Filter sessions by deck
- **WHEN** user requests sessions for deck "Spanish Vocabulary"
- **THEN** system returns only sessions for that deck

#### Scenario: Filter sessions by status
- **WHEN** user requests sessions with status "in_progress"
- **THEN** system returns only incomplete sessions

### Requirement: Session Completion
The system SHALL mark sessions as complete and preserve final statistics.

#### Scenario: Complete session successfully
- **WHEN** all cards in session are answered
- **THEN** system sets session state to "completed"
- **AND** calculates final statistics (correct rate, duration, total cards)
- **AND** saves completion timestamp

#### Scenario: End session early
- **WHEN** user explicitly ends session before completion
- **THEN** system sets state to "paused"
- **AND** saves current progress for later resume
