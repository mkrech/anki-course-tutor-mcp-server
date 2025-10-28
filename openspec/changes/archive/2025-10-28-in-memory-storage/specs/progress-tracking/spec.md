## MODIFIED Requirements

### Requirement: Card-Level Progress Tracking
The system SHALL track attempts, correct/incorrect counts, and timestamps for each card in memory.

#### Scenario: Track first attempt
- **WHEN** user answers card for first time in session
- **THEN** system records attempt number 1 in memory
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

### Requirement: Progress Storage Architecture
The system SHALL maintain progress data in memory using dictionaries with deep copying to prevent mutation.

#### Scenario: Initialize ProgressTracker
- **WHEN** ProgressTracker is created
- **THEN** it initializes empty `_progress` and `_card_progress` dictionaries
- **AND** does not require any directory paths or configuration

#### Scenario: Save with deep copy
- **WHEN** progress is saved
- **THEN** system creates deep copies of Progress and CardProgress objects
- **AND** stores copies in memory dictionaries
- **AND** prevents mutation of original objects affecting stored data

#### Scenario: Load from memory
- **WHEN** progress is loaded by session_id
- **THEN** system retrieves from in-memory dictionaries
- **AND** returns stored Progress and CardProgress data
- **AND** raises FileNotFoundError if session_id not found

### Requirement: Progress Querying
The system SHALL provide queries for in-memory progress data and statistics.

#### Scenario: Get session statistics
- **WHEN** user requests statistics for session "abc-123"
- **THEN** system returns correct_rate, total_cards, completed_cards, session_duration from memory

#### Scenario: Get card history
- **WHEN** user requests history for specific card
- **THEN** system returns all attempts with timestamps and outcomes from memory

#### Scenario: Get deck progress summary
- **WHEN** user requests progress for deck "Spanish Vocabulary"
- **THEN** system aggregates statistics across all in-memory sessions for that deck
- **AND** returns total_cards_studied, average_correct_rate, total_time_spent

### Requirement: Progress Export
The system SHALL allow exporting in-memory progress data in standard formats.

#### Scenario: Export session as JSON
- **WHEN** user exports session progress
- **THEN** system provides complete JSON with all card attempts and statistics from memory

#### Scenario: Export format structure
- **WHEN** progress is exported
- **THEN** JSON includes session metadata, card progress array, and statistics object
- **AND** follows documented schema for external tools

## ADDED Requirements

### Requirement: Progress Lifetime
Progress data SHALL exist only for the duration of the MCP server process.

#### Scenario: Progress availability
- **WHEN** progress is saved
- **THEN** it remains available in memory until the server stops
- **AND** can be queried at any time during server runtime

#### Scenario: Data loss on termination
- **WHEN** the MCP server process terminates
- **THEN** all progress data is permanently lost
- **AND** no recovery is possible

## REMOVED Requirements

### Requirement: JSON Persistence
**Reason**: Incompatible with uvx deployment model where package directory is read-only  
**Migration**: Progress is now ephemeral; export functionality still available for manual backups

#### Previous Scenario: Atomic write with backup
- **WHEN** system saved progress update
- **THEN** wrote to temporary file first with `.json.bak` backup

#### Previous Scenario: Validate on load
- **WHEN** system loaded progress file
- **THEN** validated JSON schema from file

#### Previous Scenario: Corrupted file recovery
- **WHEN** progress file was corrupted
- **THEN** system attempted to load from backup file
