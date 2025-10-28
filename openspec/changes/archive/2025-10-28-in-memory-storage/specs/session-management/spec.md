## MODIFIED Requirements

### Requirement: Session Persistence
The system SHALL maintain session state in memory and provide access during the server runtime.

#### Scenario: Save session state
- **WHEN** user answers a card during an active session
- **THEN** system saves updated session state to in-memory storage
- **AND** includes card progress, timestamps, and statistics

#### Scenario: Resume session
- **WHEN** user requests to resume session with ID "abc-123"
- **THEN** system loads session state from in-memory storage
- **AND** restores learning position and progress
- **AND** continues from next unanswered card

#### Scenario: Session not found
- **WHEN** user attempts to resume non-existent session
- **THEN** system returns error "Session not found"
- **AND** lists available sessions in memory

#### Scenario: Server restart
- **WHEN** MCP server is restarted
- **THEN** all session data is lost
- **AND** users must create new sessions

## ADDED Requirements

### Requirement: In-Memory Storage Architecture
The `SessionManager` SHALL use dictionary-based in-memory storage without file system persistence.

#### Scenario: Initialize SessionManager
- **WHEN** SessionManager is created
- **THEN** it initializes an empty `dict[str, Session]` for storage
- **AND** does not require any directory paths or configuration

#### Scenario: Session isolation
- **WHEN** multiple sessions are created with different session IDs
- **THEN** each session is stored independently in the dictionary
- **AND** modifications to one session do not affect others

### Requirement: Session Lifetime
Sessions SHALL exist only for the duration of the MCP server process.

#### Scenario: Session availability
- **WHEN** a session is created
- **THEN** it remains available in memory until the server stops
- **AND** can be accessed or resumed at any time during server runtime

#### Scenario: Data loss on termination
- **WHEN** the MCP server process terminates
- **THEN** all session data is permanently lost
- **AND** no recovery is possible

## REMOVED Requirements

### Requirement: JSON File Persistence
**Reason**: Incompatible with uvx deployment model where package directory is read-only  
**Migration**: Sessions are now ephemeral; users must complete sessions within a single server runtime

#### Previous Scenario: Save to JSON file
- **WHEN** session state changes
- **THEN** system wrote to `data/sessions/{session_id}.json`

#### Previous Scenario: Load from JSON file
- **WHEN** resuming session
- **THEN** system read from `data/sessions/{session_id}.json`

### Requirement: Backup Files
**Reason**: No longer needed without file persistence  
**Migration**: Deep copy prevents object mutation issues in memory

#### Previous Scenario: Atomic writes with backup
- **WHEN** saving session
- **THEN** system created `.json.bak` backup file
