## Context

Building an AI-powered learning system that combines Anki's spaced repetition with engaging tutoring. This is a greenfield project requiring careful architecture to separate concerns while maintaining a simple, extensible design for MVP.

**Stakeholders**: Students using Anki decks for learning, educators creating learning materials.

**Constraints**:
- Must use Python 3.13 with uv/ruff tooling
- Chat-based interface via MCP (no GUI)
- Local data storage (JSON/YAML)
- Dependency on existing anki-mcp-server for Anki integration
- FastMCP for model-agnostic AI integration

## Goals / Non-Goals

**Goals**:
- Seamless import of existing Anki decks
- Persistent learning sessions with progress tracking
- Engaging AI tutor with personality rotation
- Simple spaced repetition (retry incorrect cards)
- Clean separation between learning logic and AI/Anki integration
- Chat-based interaction via MCP tools

**Non-Goals**:
- Complex spaced repetition algorithms (SM-2, FSRS)
- Standalone GUI or web interface (MVP scope)
- Multi-user support or cloud sync
- Advanced analytics or reporting
- Direct Anki database manipulation

## Decisions

### Decision 1: Package Structure
Use standard Python package with `src/` layout mirroring anki-mcp-server:

```
anki-course-tutor-mcp-server/
├── pyproject.toml
├── config.yaml                   # Configuration file
├── src/
│   └── anki_course_tutor/
│       ├── __init__.py
│       ├── __main__.py           # MCP server entry point
│       ├── config.py             # YAML configuration loader
│       ├── server.py             # MCP server and tools
│       ├── session.py            # Session management
│       ├── learning.py           # Learning loop logic
│       ├── tutor.py              # AI tutor integration
│       ├── progress.py           # Progress tracking
│       ├── anki_client.py        # Wrapper for anki-mcp-server
│       └── models/
│           ├── card.py           # Card abstractions
│           ├── session.py        # Session data models
│           └── progress.py       # Progress data models
├── data/                         # Local data storage
│   ├── sessions/                 # Session state
│   └── progress/                 # Learning progress
└── tests/
```

**Why**: 
- Follows modern Python packaging conventions
- Clear module separation by concern
- Data models separated for type safety
- Consistent with anki-mcp-server architecture

**Alternatives considered**:
- Flat structure: Rejected due to complexity
- Monolithic file: Rejected for maintainability

### Decision 2: YAML Configuration
Use YAML for runtime configuration to allow users to customize behavior without code changes.

**Why**:
- User-friendly syntax (easier than JSON for humans)
- Supports comments for documentation
- Standard for configuration files
- Easy to extend

**Configuration Structure**:
```yaml
# config.yaml
anki:
  connect_url: "http://localhost:8765"
  connect_timeout: 30
  retry_attempts: 3

tutor:
  personalities:
    - type: "normal"
      weight: 3
    - type: "pirate"
      weight: 1
  
  modes:
    explain:
      enabled: true
      max_sentences: 5
    test:
      enabled: true
      show_correct_answer: true

learning:
  simple_srs:
    retry_incorrect: true
    shuffle_cards: false
  
  evaluation:
    case_sensitive: false
    whitespace_sensitive: false
    require_user_review: true

storage:
  data_dir: "./data"
  sessions_dir: "./data/sessions"
  progress_dir: "./data/progress"
  backup_enabled: true

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

**Implementation**:
```python
from dataclasses import dataclass
import yaml
from pathlib import Path

@dataclass
class AnkiConfig:
    connect_url: str
    connect_timeout: int
    retry_attempts: int

@dataclass
class TutorConfig:
    personalities: list[dict]
    modes: dict

@dataclass
class Config:
    anki: AnkiConfig
    tutor: TutorConfig
    learning: dict
    storage: dict
    logging: dict

class ConfigLoader:
    @staticmethod
    def load(config_path: Path = Path("config.yaml")) -> Config:
        """Load and validate YAML configuration."""
        with open(config_path) as f:
            data = yaml.safe_load(f)
        return Config(
            anki=AnkiConfig(**data["anki"]),
            tutor=TutorConfig(**data["tutor"]),
            learning=data["learning"],
            storage=data["storage"],
            logging=data["logging"]
        )
```

**Alternatives considered**:
- Environment variables only: Rejected - too many settings
- JSON config: Rejected - less human-friendly than YAML
- TOML config: Considered but YAML more familiar to users

### Decision 3: Anki Integration Strategy
Reuse existing anki-mcp-server as a library dependency rather than duplicating AnkiConnect logic.

**Why**:
- DRY principle - avoid code duplication
- Benefit from proven AnkiConnect wrapper
- Focus on learning logic rather than Anki API
- Consistent error handling

**Implementation**:
```python
from anki_mcp_server.client import AnkiClient, AnkiConnectError

class AnkiDeckImporter:
    def __init__(self):
        self.client = AnkiClient()
    
    async def import_deck(self, deck_name: str) -> list[Card]:
        """Import cards from Anki deck."""
        note_ids = await self.client.find_notes(f'"deck:{deck_name}"')
        notes_info = await self.client.get_notes_info(note_ids)
        return [self._note_to_card(note) for note in notes_info]
```

### Decision 4: AI Tutor Architecture
Use FastMCP for model-agnostic AI integration with personality system as a rotation layer.

**Why**:
- Model flexibility (works with any MCP-compatible AI)
- Personality rotation is presentation concern, not AI concern
- Simple stateful rotation counter
- Easy to extend personalities without changing AI logic

**Implementation**:
```python
class AITutor:
    def __init__(self, mode: LearningMode):
        self.mode = mode
        self.personality_rotation = PersonalityRotation()
    
    async def get_explanation(self, card: Card, user_answer: str) -> str:
        """Get AI explanation based on current mode and personality."""
        if self.mode == LearningMode.TEST:
            return ""  # No explanations in test mode
        
        personality = self.personality_rotation.next()
        prompt = self._build_prompt(card, user_answer, personality)
        response = await self._call_mcp(prompt)
        return self._limit_sentences(response, max_sentences=5)

class PersonalityRotation:
    """3 normal : 1 pirate rotation."""
    def __init__(self):
        self.count = 0
        self.personalities = [
            Personality.NORMAL,
            Personality.NORMAL, 
            Personality.NORMAL,
            Personality.PIRATE
        ]
    
    def next(self) -> Personality:
        personality = self.personalities[self.count % len(self.personalities)]
        self.count += 1
        return personality
```

### Decision 4: AI Tutor Architecture
Use FastMCP for model-agnostic AI integration with personality system as a rotation layer.

**Why**:
- Model flexibility (works with any MCP-compatible AI)
- Personality rotation is presentation concern, not AI concern
- Simple stateful rotation counter
- Easy to extend personalities without changing AI logic

**Implementation**:
```python
class AITutor:
    def __init__(self, mode: LearningMode, config: TutorConfig):
        self.mode = mode
        self.config = config
        self.personality_rotation = PersonalityRotation(config.personalities)
    
    async def get_explanation(self, card: Card, user_answer: str) -> str:
        """Get AI explanation based on current mode and personality."""
        if self.mode == LearningMode.TEST:
            return ""  # No explanations in test mode
        
        personality = self.personality_rotation.next()
        prompt = self._build_prompt(card, user_answer, personality)
        response = await self._call_mcp(prompt)
        return self._limit_sentences(response, max_sentences=self.config.modes["explain"]["max_sentences"])

class PersonalityRotation:
    """Configurable personality rotation from YAML."""
    def __init__(self, personalities: list[dict]):
        self.count = 0
        self.personalities = []
        for p in personalities:
            # Repeat each personality by its weight
            self.personalities.extend([p["type"]] * p["weight"])
    
    def next(self) -> Personality:
        personality = self.personalities[self.count % len(self.personalities)]
        self.count += 1
        return Personality(personality)
```

### Decision 5: Learning Loop State Machine
Implement learning as a state machine with clear states and transitions.

**Why**:
- Explicit state management prevents bugs
- Easy to save/resume sessions
- Clear mental model for testing
- Extensible for future features

**States**:
```python
class LearningState(Enum):
    NOT_STARTED = "not_started"
    PRESENTING_CARD = "presenting_card"
    AWAITING_ANSWER = "awaiting_answer"
    EVALUATING = "evaluating"
    AWAITING_REVIEW = "awaiting_review"      # NEW: User confirms/overrides
    EXPLAINING = "explaining"
    SESSION_COMPLETE = "session_complete"
```

**Flow**:
```
NOT_STARTED → PRESENTING_CARD → AWAITING_ANSWER → EVALUATING 
                    ↑                                   ↓
                    |                          AWAITING_REVIEW
                    |                           ↓           ↓
                    |                      EXPLAINING   (confirmed)
                    |                           ↓           ↓
                    ←───────────────────────────────────────┘
                                (next card or SESSION_COMPLETE)
```

### Decision 6: Progress Persistence Format
Use JSON files for progress tracking with human-readable structure.

**Why**:
- Simple to implement and debug
- Human-readable for transparency
- No database dependency
- Easy migration path to DB later

**Schema**:
```json
{
  "session_id": "uuid",
  "deck_name": "Spanish Vocabulary",
  "chapter": "Chapter 1",
  "created_at": "2025-10-27T10:00:00Z",
  "last_updated": "2025-10-27T10:30:00Z",
  "state": "in_progress",
  "cards": [
    {
      "card_id": "note_123",
      "attempts": 2,
      "correct_count": 1,
      "incorrect_count": 1,
      "last_attempt": "2025-10-27T10:25:00Z",
      "status": "learning"
    }
  ],
  "statistics": {
    "total_cards": 20,
    "completed_cards": 15,
    "correct_rate": 0.75,
    "session_duration_seconds": 1800
  }
}
```

### Decision 7: Card Type Abstraction
Create unified Card interface that normalizes different Anki note types.

**Why**:
- Learning loop doesn't need to know card type details
- Type-specific logic isolated in converters
- Easy to add new card types
- Consistent evaluation logic

**Implementation**:
```python
@dataclass
class Card:
    id: str
    type: CardType
    question: str
    answer: str
    options: list[str] | None = None  # For multiple choice
    cloze_text: str | None = None     # For cloze cards
    deck: str = ""
    chapter: str = ""

class CardConverter:
    @staticmethod
    def from_anki_note(note: dict) -> Card:
        """Convert Anki note to Card based on note type."""
        if note["modelName"] == "Basic":
            return CardConverter._basic_to_card(note)
        elif note["modelName"] == "Cloze":
            return CardConverter._cloze_to_card(note)
        # ... more types
```

### Decision 8: Simple Spaced Repetition for MVP
Track correct/incorrect per card and retry incorrect cards at session end.

**Why**:
- Simple to implement and understand
- Sufficient for MVP validation
- Clear upgrade path to SM-2/FSRS later
- Aligns with 4-week timeline

**Implementation**:
```python
class SimpleLearningScheduler:
    def __init__(self, cards: list[Card]):
        self.new_cards = deque(cards)
        self.incorrect_cards = deque()
        self.correct_cards = []
    
    def get_next_card(self) -> Card | None:
        """Get next card to review."""
        if self.new_cards:
            return self.new_cards.popleft()
        elif self.incorrect_cards:
            return self.incorrect_cards.popleft()
        return None
    
    def mark_correct(self, card: Card):
        self.correct_cards.append(card)
    
    def mark_incorrect(self, card: Card):
        self.incorrect_cards.append(card)
```

## Risks / Trade-offs

### Risk: AnkiConnect dependency
**Mitigation**: Graceful degradation - allow loading from APKG files if AnkiConnect unavailable.

### Risk: AI tutor response quality
**Mitigation**: Strict prompt engineering with examples, sentence limiting, and validation.

### Risk: Session state corruption
**Mitigation**: Atomic JSON writes, backup before update, validation on load.

### Trade-off: Simple vs. sophisticated spaced repetition
**Decision**: Start simple (retry incorrect cards) for MVP, upgrade to SM-2 in post-MVP phase.
**Rationale**: Focus on core learning experience and AI integration first.

### Trade-off: Chat-based (MCP) vs. Standalone GUI
**Decision**: Chat-based via MCP tools for MVP
**Rationale**: Natural conversation flow, integrates with existing AI chat interfaces (Claude Desktop, etc.), validates core learning logic without UI development overhead.

## Migration Plan

N/A - New project with no existing users.

Future migration considerations:
- JSON to SQLite: Design progress schema to be database-compatible
- Simple to advanced SRS: Keep scheduler interface stable

## Open Questions

1. **Card ordering within chapter**: Random, sequential, or user-defined?
   - **Proposed**: Sequential for MVP (matches typical deck order)

2. **Session resume behavior**: Start from last card or allow restart?
   - **Proposed**: Resume from last card, with manual restart option

3. **Multiple choice options**: Generate from similar cards or require pre-defined?
   - **Proposed**: Require pre-defined for MVP (avoid incorrect option generation)

4. **Personality customization**: Allow users to modify personalities or add new ones?
   - **Proposed**: Fixed personalities for MVP, config file for post-MVP

5. **Explanation caching**: Cache AI explanations to save API calls?
   - **Proposed**: No caching for MVP (explanations should be contextual to user's answer)
