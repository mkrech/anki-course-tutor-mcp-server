# Session Management - Delta Spec

## MODIFIED Requirements

### Requirement: Session Initialization
The system SHALL initialize sessions with AnkiClient for scheduler integration.

#### Scenario: Create session with Anki integration
- **WHEN** creating new learning session
- **THEN** system initializes session with deck and cards
- **AND** passes AnkiClient to LearningEngine
- **AND** verifies AnkiConnect is available
- **AND** starts session if connection successful

#### Scenario: Session creation with Anki offline
- **WHEN** creating session
- **AND** AnkiConnect is not available
- **THEN** system returns error
- **AND** explains Anki Desktop requirement
- **AND** does not create session

### Requirement: Session State Management
The system SHALL simplify session state by delegating scheduling to Anki.

#### Scenario: Track session progress
- **WHEN** user progresses through cards
- **THEN** system tracks current card index
- **AND** maintains card list order
- **AND** delegates interval/due management to Anki
- **AND** does not persist scheduling state locally

## REMOVED Requirements

### Requirement: ~~Local Scheduler State Persistence~~
~~The system SHALL persist scheduler state in session data.~~

**Rationale**: Anki is source of truth for scheduling, no local state needed.

## ADDED Requirements

### Requirement: AnkiClient Dependency Management
The system SHALL manage AnkiClient lifecycle in sessions.

#### Scenario: Initialize session with AnkiClient
- **WHEN** SessionManager creates session
- **THEN** system creates or reuses AnkiClient instance
- **AND** passes to LearningEngine
- **AND** ensures connection available

#### Scenario: Handle AnkiClient errors
- **WHEN** AnkiClient operation fails
- **THEN** system logs error with session context
- **AND** preserves session for retry
- **AND** does not corrupt session data

### Requirement: Session Resume with Anki State
The system SHALL resume sessions using Anki's scheduling state.

#### Scenario: Resume paused session
- **WHEN** user resumes session
- **THEN** system loads session data
- **AND** verifies cards still exist in Anki
- **AND** continues from last position
- **AND** Anki scheduling reflects all reviews

## Implementation Notes

### SessionManager Changes

```python
class SessionManager:
    def __init__(self, storage_dir: str, anki_client: AnkiClient = None):
        self.storage_dir = Path(storage_dir)
        self.anki_client = anki_client  # NEW: Optional AnkiClient
        
    def create_session(
        self,
        deck_name: str,
        card_ids: list[str],
        mode: str = "explain",
        chapter: str = ""
    ) -> Session:
        """Create new learning session."""
        session = Session(
            session_id=str(uuid.uuid4()),
            deck_name=deck_name,
            card_ids=card_ids,
            mode=LearningMode(mode),
            status=SessionStatus.IN_PROGRESS,
            # REMOVED: scheduler state
        )
        self.save_session(session)
        return session
```

### MCP Server Integration

```python
# mcp_server.py
@mcp.tool()
async def start_session(deck_name: str, chapter: str = "", mode: str = "explain"):
    """Start learning session."""
    global _active_session, _learning_engine, _anki_importer
    
    # Verify Anki available
    if not await _anki_importer.check_connection():
        return {
            "error": "anki_not_available",
            "message": "Anki Desktop is not running or AnkiConnect is not installed.",
            "instructions": "Please start Anki Desktop and ensure AnkiConnect addon is installed."
        }
    
    # Import cards
    cards = await _anki_importer.import_deck(deck_name, chapter)
    
    # Create session with AnkiClient
    session = _session_manager.create_session(
        deck_name=deck_name,
        card_ids=[c.id for c in cards],
        mode=mode,
        chapter=chapter
    )
    
    # Initialize engine with AnkiClient
    _learning_engine = LearningEngine(
        session=session,
        cards=cards,
        mode=LearningMode(mode),
        anki_client=_anki_importer  # Pass AnkiClient
    )
    
    return _learning_engine.start()
```

### Session Model Simplification

```python
@dataclass
class Session:
    session_id: str
    deck_name: str
    chapter: str
    mode: LearningMode
    state: LearningState
    status: SessionStatus
    created_at: datetime
    last_updated: datetime
    card_ids: list[str]
    current_card_index: int = 0  # Simple progress tracking
    card_progress: dict[str, CardProgress] = field(default_factory=dict)
    personality_count: int = 0
    
    # REMOVED: scheduler state, intervals, due dates
    # Anki is source of truth for these
```

## Testing Requirements

- Update SessionManager tests for AnkiClient integration
- Test session creation with/without Anki available
- Test session resume flow
- Mock AnkiClient in unit tests
- Integration tests for complete session lifecycle

## Breaking Changes

- SessionManager constructor signature changed
- Session data structure simplified
- Existing session files may not load correctly (acceptable)

## Migration Notes

- No automatic migration needed
- Users can start new sessions
- Old sessions can be archived/deleted
- Document new setup requirements

## Dependencies

- AnkiClient instance must be provided to SessionManager
- Anki Desktop must be running for session operations
- AnkiConnect addon must be installed
