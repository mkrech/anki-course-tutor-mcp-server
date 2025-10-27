## ADDED Requirements

### Requirement: Deck Import via AnkiConnect
The system SHALL import cards from Anki decks using the anki-mcp-server client.

#### Scenario: Import full deck
- **WHEN** user imports deck "Spanish Vocabulary"
- **THEN** system uses AnkiClient to query all notes in deck
- **AND** converts each note to Card model
- **AND** returns list of cards ready for learning

#### Scenario: Import deck with chapter filter
- **WHEN** user imports deck with chapter tag "chapter-1"
- **THEN** system queries notes with tag filter
- **AND** returns only cards matching chapter

#### Scenario: AnkiConnect unavailable
- **WHEN** Anki is not running or AnkiConnect not installed
- **THEN** system returns error "Cannot connect to Anki"
- **AND** suggests checking Anki status

### Requirement: Deck Listing
The system SHALL list available Anki decks for selection.

#### Scenario: List all decks
- **WHEN** user requests available decks
- **THEN** system calls AnkiClient.get_deck_names()
- **AND** returns list of deck names

#### Scenario: Empty deck list
- **WHEN** Anki has no decks
- **THEN** system returns empty list
- **AND** suggests creating decks in Anki

### Requirement: Note Type Handling
The system SHALL handle different Anki note types with appropriate converters.

#### Scenario: Detect Basic note type
- **WHEN** system imports note with modelName "Basic"
- **THEN** uses BasicCardConverter
- **AND** extracts Front and Back fields

#### Scenario: Detect Cloze note type
- **WHEN** system imports note with modelName "Cloze"
- **THEN** uses ClozeCardConverter
- **AND** parses cloze deletions

#### Scenario: Detect custom note type
- **WHEN** system imports note with custom modelName
- **THEN** attempts to map fields to Basic template
- **AND** logs warning about custom type

#### Scenario: Missing required fields
- **WHEN** note lacks expected fields (e.g., Basic without Back)
- **THEN** system skips card with error log
- **AND** continues importing remaining cards

### Requirement: AnkiClient Wrapper
The system SHALL wrap anki-mcp-server client for domain-specific operations.

#### Scenario: Connection health check
- **WHEN** system starts or user initiates import
- **THEN** calls AnkiClient.check_connection()
- **AND** verifies Anki is reachable before proceeding

#### Scenario: Reuse client instance
- **WHEN** multiple import operations occur
- **THEN** system reuses same AnkiClient instance
- **AND** maintains connection pooling

### Requirement: Error Handling
The system SHALL handle Anki integration errors gracefully without crashing.

#### Scenario: Network timeout
- **WHEN** AnkiConnect request times out
- **THEN** system retries up to 3 times
- **AND** returns error if all retries fail

#### Scenario: Malformed note data
- **WHEN** Anki returns unexpected note structure
- **THEN** system logs detailed error
- **AND** skips problematic note
- **AND** continues processing remaining notes

#### Scenario: Deck not found
- **WHEN** user requests non-existent deck
- **THEN** system returns clear error message
- **AND** lists available deck names for correction
