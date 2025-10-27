# Card Learning - Delta Spec

## MODIFIED Requirements

### Requirement: Answer Evaluation and Confirmation
The system SHALL submit confirmed evaluations directly to Anki's scheduler.

#### Scenario: Correct answer confirmed and submitted
- **WHEN** user confirms correct evaluation
- **THEN** system submits review to Anki with ease=4
- **AND** Anki updates card scheduling
- **AND** system proceeds to next card
- **AND** shows previous result feedback

#### Scenario: Incorrect answer confirmed and submitted
- **WHEN** user confirms incorrect evaluation
- **AND** learning mode is EXPLAIN
- **THEN** system submits review to Anki with ease=1
- **AND** Anki marks card for relearning
- **AND** system enters EXPLAINING state
- **AND** requests explanation

#### Scenario: Review submission fails
- **WHEN** user confirms evaluation
- **AND** AnkiConnect is unavailable
- **THEN** system logs error
- **AND** returns error message to user
- **AND** preserves session state
- **AND** allows retry or continue

## REMOVED Requirements

### Requirement: Local Scheduling Logic
~~The system SHALL use SimpleLearningScheduler for card scheduling.~~

**Rationale**: Replaced by Anki's native scheduler via AnkiConnect API.

#### Scenario: ~~New card scheduling~~
- **REMOVED**: Local queue management replaced by Anki

#### Scenario: ~~Retry queue management~~
- **REMOVED**: Anki handles relearning automatically

#### Scenario: ~~Card completion tracking~~
- **MODIFIED**: Simplified to session progress only, Anki handles intervals

## ADDED Requirements

### Requirement: Anki Scheduler Integration
The system SHALL integrate with Anki's scheduler for all card reviews.

#### Scenario: Submit review after confirmation
- **WHEN** user confirms answer evaluation
- **THEN** system determines ease value (4 for correct, 1 for incorrect)
- **AND** calls AnkiClient.answer_card(card_id, ease)
- **AND** logs success or error
- **AND** proceeds with learning flow

#### Scenario: Handle scheduler errors gracefully
- **WHEN** Anki scheduler submission fails
- **THEN** system catches AnkiConnectError
- **AND** logs error with context
- **AND** returns user-friendly error message
- **AND** does not crash session

### Requirement: Card ID Management
The system SHALL use Anki's card IDs for all scheduling operations.

#### Scenario: Use Anki card ID
- **WHEN** system loads cards from Anki
- **THEN** system stores Anki's cardId as Card.id
- **AND** uses integer card ID for scheduling APIs
- **AND** maintains ID consistency throughout session

## Implementation Notes

### LearningEngine Changes

```python
class LearningEngine:
    def __init__(self, session, cards, mode, anki_client):
        self.session = session
        self.cards = cards
        self.mode = mode
        self.anki_client = anki_client  # NEW: Add AnkiClient
        # REMOVED: self.scheduler = SimpleLearningScheduler(cards)
        
    async def confirm_evaluation(self, is_correct: bool) -> dict:
        """Confirm evaluation and submit to Anki."""
        # ... existing validation ...
        
        # Update card progress (local tracking)
        self._update_card_progress(is_correct)
        
        # NEW: Submit to Anki scheduler
        ease = 4 if is_correct else 1
        try:
            await self.anki_client.answer_card(
                card_id=int(self.current_card.id),
                ease=ease
            )
            logger.info(
                f"Submitted review to Anki: card={self.current_card.id}, "
                f"ease={ease}, correct={is_correct}"
            )
        except AnkiConnectError as e:
            logger.error(f"Failed to submit review to Anki: {e}")
            return {
                "error": "anki_connection_failed",
                "message": "Could not submit review to Anki. "
                          "Please ensure Anki Desktop is running with AnkiConnect.",
                "details": str(e)
            }
        
        # Continue with existing flow
        if not is_correct and self.mode == LearningMode.EXPLAIN:
            # ... explaining state ...
        else:
            # ... next card ...
```

### Card Navigation Simplification

```python
# OLD: Complex scheduler state
def _next_card(self):
    card = self.scheduler.get_next_card()
    # ... queue management ...

# NEW: Simple iteration
def _next_card(self):
    self.current_card_index += 1
    if self.current_card_index < len(self.cards):
        self.current_card = self.cards[self.current_card_index]
        return self._present_card()
    else:
        return {"state": "session_complete"}
```

## Testing Requirements

- Update LearningEngine unit tests for Anki integration
- Mock AnkiClient in tests
- Test error handling for AnkiConnect failures
- Verify ease mapping (correct→4, incorrect→1)
- Integration tests for full learning flow
- Test session state preservation on error

## Breaking Changes

- `LearningEngine.__init__` now requires `anki_client` parameter
- Session state simplified (no local scheduler state)
- Old sessions may not resume correctly (acceptable for alpha)

## Migration Notes

- Existing in-progress sessions will need to restart
- No data migration needed (sessions are ephemeral)
- Documentation update required for setup

## Dependencies

- AnkiClient with scheduling methods
- Anki Desktop running during sessions
- AnkiConnect addon installed and configured
