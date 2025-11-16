# Architecture Overview

## Purpose
AI-powered learning system that combines Anki's spaced repetition with AI-driven tutoring via MCP chat interface. This document explains the key architectural decisions and design patterns used in the system.

## Core Design Principles

### 1. Anki as Single Source of Truth
**Decision:** Use Anki Desktop as the authoritative data store for all card data, review history, and scheduling.

**Rationale:**
- Anki already provides robust SQLite-based persistence
- SM-2/FSRS scheduling algorithms are mature and proven
- AnkiWeb sync enables multi-device workflows
- No data duplication or synchronization conflicts
- Simpler architecture with fewer moving parts

**Implementation:**
```
┌─────────────────────────────────────────┐
│  Anki Desktop (Single Source of Truth)  │
│  • Card data & metadata                 │
│  • Review history & statistics          │
│  • Spaced repetition scheduler          │
│  • Due dates, intervals, ease factors   │
│  • SQLite persistence                   │
└─────────────────────────────────────────┘
              ↕ AnkiConnect API
┌─────────────────────────────────────────┐
│  anki-course-tutor (MCP Server)         │
│  • Ephemeral session state              │
│  • Learning flow state machine          │
│  • AI explanation generation            │
│  • MCP tool interfaces                  │
└─────────────────────────────────────────┘
```

**Trade-offs:**
- ✅ No additional persistence layer needed
- ✅ Leverage Anki's mature ecosystem
- ✅ Data survives server restarts automatically
- ❌ Requires Anki Desktop running
- ❌ Session state (current position) is ephemeral

### 2. Ephemeral Session State
**Decision:** Session state (current card, retry queue) is kept in-memory and lost on server restart.

**Rationale:**
- Designed for `uvx` deployment (read-only package directory)
- Sessions are typically short-lived (single learning session)
- Review progress is saved to Anki immediately, so no data loss
- Simpler implementation without file I/O complexity

**Recovery Pattern:**
```python
# After server restart
start_session(deck_name="MyDeck")
# Anki filters out already-reviewed cards automatically
# User continues from where Anki's scheduler says they should
```

### 3. State Machine for Learning Flow
**Decision:** Use explicit state machine pattern for card learning workflow.

**States:**
- `NOT_STARTED` → Initial state
- `PRESENTING_CARD` → Showing question
- `AWAITING_ANSWER` → Waiting for user response
- `AWAITING_REVIEW` → User confirms correctness
- `EXPLAINING` → AI providing explanation (EXPLAIN mode only)
- `SESSION_COMPLETE` → All cards finished

**Benefits:**
- Clear, testable state transitions
- Prevents invalid operations (e.g., answering before question shown)
- Easy to reason about workflow
- Supports different modes (EXPLAIN vs TEST)

### 4. Separation of Concerns

**Component Responsibilities:**

```
mcp_server.py
├─ MCP tool definitions
├─ Request validation
└─ Global state management

learning_engine.py
├─ State machine logic
├─ Card queue management
├─ Answer evaluation orchestration
└─ Anki scheduler integration

ai_tutor.py
├─ Prompt templating
├─ Explanation generation
└─ (TODO: LLM integration)

anki_client.py
├─ AnkiConnect API wrapper
├─ Card import/export
└─ Review submission

session_manager.py
└─ In-memory session persistence

progress_tracker.py
└─ Statistics calculation
```

**Anti-Corruption Layer:**
- `AnkiClient` wraps AnkiConnect API
- Domain models (`Card`, `Session`) are independent of Anki's schema
- Clean separation allows easy mocking in tests

## Key Technical Decisions

### Answer Evaluation Strategy
**Two-phase evaluation with user review:**

1. **Automatic Evaluation:** System suggests correct/incorrect
2. **User Confirmation:** User can override the suggestion

**Rationale:**
- Handles edge cases (typos, alternative answers)
- Builds user trust through transparency
- Allows learning from evaluation process itself

### Retry Queue Pattern
**Priority-based card scheduling:**

1. **New cards first:** Present all unseen cards
2. **Retry queue second:** Re-present incorrectly answered cards

**Implementation:**
```python
_cards: list[Card]           # All cards (position: _current_index)
_retry_queue: deque[str]     # Card IDs to retry
_card_map: dict[str, Card]   # Fast lookup
```

**Benefits:**
- Ensures all cards seen before repetition
- Simple FIFO retry logic
- Persisted in Session.retry_queue for session resumption

### Anki Scheduler Integration
**Binary ease mapping for MVP:**
```python
correct → ease=4 (Easy)
incorrect → ease=1 (Again)
```

**Submission flow:**
```python
async def confirm_evaluation(is_correct: bool):
    # 1. Submit to Anki scheduler
    await self._submit_review_to_anki(card, is_correct)
    
    # 2. Update local state
    self._update_card_progress(is_correct)
    
    # 3. Add to retry queue if incorrect
    if not is_correct:
        self._retry_queue.append(card.id)
```

**Trade-offs:**
- ✅ Reviews immediately reflected in Anki
- ✅ AnkiWeb sync works seamlessly
- ❌ No granular difficulty (Hard/Good/Easy)
- ❌ Fail-fast: Anki connection errors block progress

### Card Type Support
**Unified handling via CardType enum:**
- `BASIC`: Question/answer pairs
- `CLOZE`: Fill-in-the-blank with deletions
- `ALL_IN_ONE`: Flexible multi-format (KPRIM, MC, SC)

**KPRIM Handling:**
- Accepts multiple formats: `1010`, `RFRF`, `TFTF`, `Y N Y N`
- Normalization for comparison: `_normalize_kprim_answer()`
- Partial credit evaluation (0-4 points)

**Mathematical Expression Normalization:**
- Superscript conversion: `k²` → `k^2`
- Operator normalization: `×` → `*`, `÷` → `/`
- Whitespace handling around operators

## MCP Integration

### Tool Organization
**11 MCP tools organized by workflow stage:**

**Session Management:**
- `list_decks()` - Discover available decks
- `start_session()` - Begin new learning session
- `resume_session()` - Continue existing session
- `end_session()` - Complete and save progress

**Learning Flow:**
- `get_next_card()` - Retrieve next card to study
- `submit_answer()` - Provide answer for evaluation
- `confirm_evaluation()` - Confirm/override correctness

**AI Assistance:**
- `get_explanation()` - Request AI explanation
- `next_card_after_explanation()` - Continue after explanation

**Monitoring:**
- `get_session_stats()` - View progress statistics
- `list_sessions()` - Browse saved sessions

### Resource Endpoints
- `deck://list` - Available decks
- `session://active` - Current session info

## AI Tutor Design

### Current Implementation
**Placeholder explanations:**
```python
async def generate_explanation(...):
    # Prompt is prepared but not sent to LLM
    prompt = self.PROMPT_TEMPLATE.format(...)
    
    # Returns generic placeholder
    explanation = self._generate_placeholder_explanation(...)
    
    return {"explanation": explanation, "prompt": prompt}
```

### Future LLM Integration (TODO)
**Option 1: Context-based (recommended)**
```python
# Pass Context through layers
@mcp.tool()
async def get_explanation(ctx: Context):
    result = await _learning_engine.get_explanation(ctx)

async def get_explanation(self, ctx: Context):
    result = await self.ai_tutor.generate_explanation(..., ctx=ctx)

async def generate_explanation(self, ..., ctx: Context):
    response = await ctx.request_sampling(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    return {"explanation": response.content}
```

**Option 2: Direct in MCP tool (simpler for MVP)**
```python
@mcp.tool()
async def get_explanation(ctx: Context):
    prompt = AITutor.PROMPT_TEMPLATE.format(...)
    response = await ctx.request_sampling(...)
    return {"explanation": response.content}
```

## Testing Strategy

### Test Coverage: 74% (102 tests)
**Areas well-covered:**
- Core learning flow state transitions
- Answer evaluation logic (all card types)
- Anki scheduler integration
- Session management lifecycle

**Areas for improvement:**
- Error handling edge cases
- Concurrent session scenarios
- AnkiConnect failure recovery
- Card type edge cases (complex KPRIM)

### Test Organization
```
tests/
├── test_ai_tutor.py          # Prompt generation, placeholders
├── test_anki_client.py       # AnkiConnect integration
├── test_learning_engine.py   # State machine, core logic
├── test_mcp_server.py        # Tool interfaces
├── test_progress_tracker.py  # Statistics calculation
├── test_session_manager.py   # Session lifecycle
└── test_e2e.py              # Full workflow scenarios
```

## Configuration

### Key Settings
```yaml
anki:
  connect_url: "http://localhost:8765"
  use_anki_scheduler: true  # Enable/disable Anki integration
  
tutor:
  max_explanation_sentences: 5
  
learning:
  mode: "explain"  # or "test"
```

## Deployment Model

### uvx Deployment (Primary)
```bash
uvx --from git+https://github.com/mkrech/anki-course-tutor-mcp-server anki-course-tutor
```

**Characteristics:**
- Read-only package directory
- No writable data directories
- Process lifecycle tied to MCP session
- In-memory state only

### Development
```bash
uv sync
uv run anki-course-tutor
```

## Known Limitations & Future Work

### Current Limitations
1. **AI Explanations:** Placeholder text, not real LLM-generated
2. **Ease Granularity:** Binary (correct/incorrect), no Hard/Good/Easy
3. **Session Recovery:** Cannot resume after server restart (by design)
4. **Error Recovery:** Anki connection failures are fail-fast
5. **Undo:** No way to undo last answer evaluation

### Enhancement Opportunities
1. **LLM Integration:** Real AI-generated explanations
2. **Flexible Ease:** User-selectable difficulty levels
3. **Undo Function:** Revert last card evaluation
4. **Batch Reviews:** Submit multiple reviews to Anki at once
5. **Study Presets:** Configurable session templates
6. **Internationalization:** Multi-language support

## Performance Considerations

### Efficient Card Loading
- Cards loaded once per session from Anki
- In-memory lookup via `_card_map: dict[str, Card]`
- O(1) card retrieval by ID

### Review Submission
- Immediate submission to Anki (no batching)
- Trade-off: Simpler code vs more network calls
- Future: Consider batching for large sessions

### Memory Usage
- All session cards held in memory
- Acceptable for typical deck sizes (< 1000 cards)
- Potential optimization: Lazy loading for huge decks

## Security Considerations

### AnkiConnect Access
- Localhost-only by default (http://localhost:8765)
- No authentication on AnkiConnect API
- Trust model: Local machine access

### MCP Authorization
- Relies on MCP client (Claude Desktop) auth
- No additional auth layer in anki-course-tutor
- Sessions are per-user via MCP context

## Monitoring & Observability

### Logging
```python
logger.info()   # Session lifecycle, card flow
logger.debug()  # Detailed state transitions
logger.error()  # Failures, exceptions
logger.warning() # Unexpected but recoverable states
```

### Statistics
- Session-level: correct rate, attempt count, duration
- Card-level: attempts per card, time spent
- Aggregation: via ProgressTracker

## Related Documentation
- [README.md](../README.md) - User-facing documentation
- [openspec/project.md](../openspec/project.md) - Project conventions
- [openspec/specs/](../openspec/specs/) - Detailed specifications
- [CHANGELOG.md](../CHANGELOG.md) - Change history
