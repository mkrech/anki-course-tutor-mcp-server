## ADDED Requirements

### Requirement: Card-Level Progress Tracking
The system SHALL track attempts, correct/incorrect counts, and timestamps for each card.

#### Scenario: Track first attempt
- **WHEN** user answers card for first time in session
- **THEN** system records attempt number 1
- **AND** increments correct or incorrect count based on answer
- **AND** saves timestamp of attempt

#### Scenario: Track multiple attempts
- **WHEN** user answers same card 3 times (2 incorrect, 1 correct)
- **THEN** system records 3 total attempts
- **AND** stores correct_count = 1, incorrect_count = 2
- **AND** saves timestamp of latest attempt

#### Scenario: Card status classification
- **WHEN** card has only correct attempts
- **THEN** system marks card status as "mastered"
- **WHEN** card has incorrect attempts
- **THEN** system marks card status as "learning"

### Requirement: Session Statistics
The system SHALL calculate and persist session-level statistics.

#### Scenario: Calculate correct rate
- **WHEN** session has 20 total attempts with 15 correct
- **THEN** system calculates correct_rate = 0.75 (75%)

#### Scenario: Track session duration
- **WHEN** session starts at 10:00 and ends at 10:30
- **THEN** system records session_duration_seconds = 1800

#### Scenario: Count unique cards
- **WHEN** session includes 10 cards, 3 answered multiple times
- **THEN** system reports total_cards = 10
- **AND** completed_cards increments as unique cards are answered

### Requirement: JSON Persistence
The system SHALL save progress to JSON files with atomic writes and validation.

#### Scenario: Atomic write with backup
- **WHEN** system saves progress update
- **THEN** writes to temporary file first
- **AND** renames temporary file to actual filename (atomic operation)
- **AND** creates backup of previous version

#### Scenario: Validate on load
- **WHEN** system loads progress file
- **THEN** validates JSON schema
- **AND** checks for required fields (session_id, deck_name, cards)
- **AND** returns error if validation fails

#### Scenario: Corrupted file recovery
- **WHEN** progress file is corrupted
- **THEN** system attempts to load from backup
- **AND** logs error about corruption
- **AND** allows creating new session if recovery fails

### Requirement: Progress Querying
The system SHALL provide queries for progress data and statistics.

#### Scenario: Get session statistics
- **WHEN** user requests statistics for session "abc-123"
- **THEN** system returns correct_rate, total_cards, completed_cards, session_duration

#### Scenario: Get card history
- **WHEN** user requests history for specific card
- **THEN** system returns all attempts with timestamps and outcomes

#### Scenario: Get deck progress summary
- **WHEN** user requests progress for deck "Spanish Vocabulary"
- **THEN** system aggregates statistics across all sessions for that deck
- **AND** returns total_cards_studied, average_correct_rate, total_time_spent

### Requirement: Progress Export
The system SHALL allow exporting progress data in standard formats.

#### Scenario: Export session as JSON
- **WHEN** user exports session progress
- **THEN** system provides complete JSON with all card attempts and statistics

#### Scenario: Export format structure
- **WHEN** progress is exported
- **THEN** JSON includes session metadata, card progress array, and statistics object
- **AND** follows documented schema for external tools
