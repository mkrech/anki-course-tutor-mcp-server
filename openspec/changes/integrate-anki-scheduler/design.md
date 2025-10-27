# Design: Anki Scheduler Integration

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│              Learning Session Flow                       │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
        ┌─────────────────────────┐
        │   LearningEngine        │
        │  - Present cards        │
        │  - Evaluate answers     │
        │  - Confirm evaluation   │
        └────────┬────────────────┘
                 │
                 │ confirm_evaluation(is_correct)
                 ▼
        ┌─────────────────────────┐
        │  AnkiSchedulerAdapter   │
        │  - Convert to ease      │
        │  - Submit to Anki       │
        └────────┬────────────────┘
                 │
                 │ answer_card(card_id, ease)
                 ▼
        ┌─────────────────────────┐
        │     AnkiClient          │
        │  - answerCards API      │
        │  - Error handling       │
        └────────┬────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │   AnkiConnect API       │
        │  - Update card state    │
        │  - Calculate interval   │
        │  - Write review log     │
        └─────────────────────────┘
                 │
                 ▼
        ┌─────────────────────────┐
        │    Anki Desktop         │
        │  - SM-2 Algorithm       │
        │  - AnkiWeb Sync         │
        └─────────────────────────┘
```

## Key Design Decisions

### 1. Ease Value Mapping

**Question**: How to map user correctness to Anki's 4-point ease scale?

**Decision**: Simple binary mapping for MVP
```python
# User answer evaluation
is_correct = True/False

# Map to Anki ease
ease = 4 if is_correct else 1

# Anki's ease scale:
# 1 = Again (failed, will relearn)
# 2 = Hard (passed but difficult)
# 3 = Good (passed normally)
# 4 = Easy (passed easily)
```

**Rationale**:
- ✅ Simple to implement
- ✅ Clear user feedback (correct vs incorrect)
- ✅ Leverages Anki's relearning logic for incorrect
- ⚠️ Future: Could add "Hard" option for user feedback

### 2. Card ID Mapping

**Question**: How to ensure card IDs match between Tutor and Anki?

**Decision**: Use Anki's card IDs directly from AnkiConnect

```python
# During deck import (already implemented)
cards = await anki_client.find_cards(query=f"deck:{deck_name}")
card_info = await anki_client.cards_info(cards=cards)

# Use Anki's card ID as Card.id
card = Card(
    id=str(card_info['cardId']),  # Anki's native card ID
    ...
)
```

**Rationale**:
- ✅ No mapping layer needed
- ✅ Direct AnkiConnect API calls
- ✅ Already using this in current implementation

### 3. Error Handling Strategy

**Question**: What happens when AnkiConnect is unavailable?

**Decision**: Fail fast with clear error messages (MVP)

```python
try:
    await anki_adapter.submit_review(card_id, is_correct)
except AnkiConnectError as e:
    logger.error(f"Failed to submit review to Anki: {e}")
    return {
        "error": "Anki connection failed",
        "message": "Please ensure Anki Desktop is running with AnkiConnect addon",
        "details": str(e)
    }
```

**Future Enhancement**: Offline queue
- Queue reviews locally when offline
- Submit batch on reconnection
- Out of scope for this change

**Rationale**:
- ✅ Clear user feedback
- ✅ No data loss (session can resume)
- ✅ Simple implementation
- ⚠️ Requires Anki running (acceptable trade-off)

### 4. Session State Simplification

**Question**: What session state is still needed?

**Current State** (with SimpleLearningScheduler):
```python
@dataclass
class Session:
    card_ids: list[str]
    current_card_index: int
    # ... scheduler state
```

**New State** (with Anki scheduler):
```python
@dataclass
class Session:
    card_ids: list[str]  # Still needed for card order
    current_card_index: int  # Track progress in session
    # Anki handles: intervals, due dates, ease factors
```

**Rationale**:
- ✅ Anki is source of truth for scheduling
- ✅ Session only tracks current position
- ✅ Simpler state management

### 5. Scheduler Adapter Interface

**Question**: Should we abstract the scheduler behind an interface?

**Decision**: No abstraction layer for MVP

```python
# Direct usage
class LearningEngine:
    def __init__(self, session, cards, mode, anki_client):
        self.anki_client = anki_client
        # No scheduler object needed
```

**Rationale**:
- ✅ YAGNI - no need for multiple scheduler implementations
- ✅ Simpler code
- ✅ Direct AnkiClient usage
- ⚠️ Future: Could add interface if needed

### 6. Card Timer Management

**Question**: Should we track review time?

**Decision**: Let Anki handle timing

AnkiConnect's `answerCards` API expects cards to have timer started:
```python
card.start_timer()  # Done by Anki
scheduler.answerCard(card, ease)
```

**Implementation**:
```python
# We'll rely on AnkiConnect to handle this
# No explicit timer tracking in Tutor
```

**Rationale**:
- ✅ Anki already tracks review time
- ✅ Review time visible in Anki stats
- ✅ One less thing to manage

## API Contract

### AnkiClient Extensions

```python
class AnkiClient:
    async def answer_card(self, card_id: int, ease: int) -> bool:
        """Submit card answer to Anki scheduler.
        
        Args:
            card_id: Anki card ID
            ease: 1-4 (Again, Hard, Good, Easy)
            
        Returns:
            True if successful
            
        Raises:
            AnkiConnectError: If submission fails
        """
        
    async def get_card_info(self, card_id: int) -> dict:
        """Get card state from Anki.
        
        Returns:
            {
                'cardId': int,
                'interval': int,  # days
                'factor': int,    # ease * 10
                'type': int,      # 0=new, 1=learning, 2=review
                'queue': int,     # card queue
                'due': int,       # due date
                ...
            }
        """
```

### LearningEngine Integration

```python
class LearningEngine:
    async def confirm_evaluation(self, is_correct: bool) -> dict:
        """Confirm evaluation and submit to Anki."""
        # ... existing evaluation logic
        
        # NEW: Submit to Anki
        ease = 4 if is_correct else 1
        try:
            await self.anki_client.answer_card(
                card_id=int(self.current_card.id),
                ease=ease
            )
        except AnkiConnectError as e:
            return {"error": f"Failed to submit review: {e}"}
        
        # Continue with next card...
```

## Data Flow

### Review Submission Flow

```
User Answer
    │
    ▼
LearningEngine.submit_answer()
    │
    ▼
LearningEngine.confirm_evaluation(is_correct)
    │
    ├─ Map: is_correct → ease (1 or 4)
    │
    ▼
AnkiClient.answer_card(card_id, ease)
    │
    ├─ POST /api/answerCards
    │  {
    │    "action": "answerCards",
    │    "params": {
    │      "answers": [{"cardId": 123, "ease": 4}]
    │    }
    │  }
    │
    ▼
Anki Desktop (via AnkiConnect)
    │
    ├─ SM-2 Algorithm calculates new interval
    ├─ Update card state (due, interval, factor)
    ├─ Write to review log (revlog table)
    │
    ▼
Review logged in Anki
    │
    ├─ Visible in Anki Desktop stats
    ├─ Syncs to AnkiWeb
    └─ Available on mobile apps
```

## Testing Strategy

### Unit Tests
```python
@pytest.mark.asyncio
async def test_answer_card_correct():
    """Test submitting correct answer to Anki."""
    client = AnkiClient()
    with patch.object(client, 'invoke') as mock:
        mock.return_value = [True]
        result = await client.answer_card(123, ease=4)
        assert result is True
        mock.assert_called_once_with(
            "answerCards",
            answers=[{"cardId": 123, "ease": 4}]
        )
```

### Integration Tests
```python
@pytest.mark.asyncio
async def test_review_submits_to_anki(anki_mock):
    """Test that reviews are submitted to Anki."""
    engine = LearningEngine(session, cards, mode, anki_client)
    engine.start()
    engine.submit_answer("correct answer")
    
    await engine.confirm_evaluation(is_correct=True)
    
    # Verify Anki was called
    anki_mock.answer_card.assert_called_once_with(
        card_id=123,
        ease=4
    )
```

### Manual Testing
1. Start Anki Desktop with AnkiConnect
2. Import deck via Tutor
3. Answer cards in Tutor
4. Check Anki Desktop stats → reviews should appear
5. Sync to AnkiWeb → check sync works
6. Check mobile app → reviews should sync

## Rollout Plan

### Phase 1: Implementation (This Change)
- Implement AnkiClient scheduling methods
- Integrate with LearningEngine
- Update tests
- Documentation

### Phase 2: Production Validation
- Deploy to production
- Monitor error rates
- Gather user feedback
- Verify AnkiWeb sync

### Phase 3: Future Enhancements (Out of Scope)
- Offline review queue
- Custom ease mapping (Good/Hard options)
- Bulk review import
- Advanced scheduling options

## Alternatives Considered

### Alternative 1: Keep SimpleLearningScheduler as Fallback
**Pros**: Offline support  
**Cons**: Complexity, data sync issues  
**Decision**: Rejected - YAGNI, adds complexity

### Alternative 2: Implement Our Own SM-2
**Pros**: Full control, offline capable  
**Cons**: Reinventing wheel, no AnkiWeb sync  
**Decision**: Rejected - Anki's is proven

### Alternative 3: Hybrid (Queue + Sync)
**Pros**: Best of both worlds  
**Cons**: Complex, MVP overkill  
**Decision**: Future enhancement

## Open Questions

None - all design decisions finalized.
