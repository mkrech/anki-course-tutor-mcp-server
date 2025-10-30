# Anki Integration - Delta Spec

## MODIFIED Requirements

### Requirement: Card Review Submission
The system SHALL submit card reviews directly to Anki's scheduler via AnkiConnect API.

#### Scenario: Submit correct answer to Anki
- **WHEN** user confirms a correct answer
- **THEN** system calls `answerCards` API with ease=4
- **AND** Anki updates card interval using SM-2 algorithm
- **AND** review is logged in Anki's revlog

#### Scenario: Submit incorrect answer to Anki
- **WHEN** user confirms an incorrect answer
- **THEN** system calls `answerCards` API with ease=1
- **AND** Anki marks card for relearning
- **AND** review is logged in Anki's revlog

#### Scenario: Handle AnkiConnect unavailable
- **WHEN** AnkiConnect is not accessible
- **THEN** system returns clear error message
- **AND** explains Anki Desktop must be running
- **AND** session can resume when Anki available

### Requirement: Card State Retrieval
The system SHALL retrieve card scheduling state from Anki when needed.

#### Scenario: Get card scheduling info
- **WHEN** system needs card state
- **THEN** system calls `cardsInfo` API
- **AND** retrieves interval, ease factor, due date
- **AND** uses data for display purposes

### Requirement: Review History Access
The system SHALL access review history from Anki for progress tracking.

#### Scenario: Fetch card review history
- **WHEN** system needs review statistics
- **THEN** system calls `getReviewsOfCards` API
- **AND** retrieves historical review data
- **AND** displays in progress tracking

## ADDED Requirements

### Requirement: Ease Value Mapping
The system SHALL map user answer correctness to Anki's ease scale.

#### Scenario: Map correct answer to ease
- **WHEN** user answer is marked correct
- **THEN** system maps to ease=4 (Easy)
- **AND** submits to Anki scheduler

#### Scenario: Map incorrect answer to ease
- **WHEN** user answer is marked incorrect
- **THEN** system maps to ease=1 (Again)
- **AND** triggers Anki's relearning process

### Requirement: AnkiConnect Error Handling
The system SHALL gracefully handle AnkiConnect connection failures.

#### Scenario: Connection timeout
- **WHEN** AnkiConnect request times out
- **THEN** system logs error details
- **AND** returns user-friendly error message
- **AND** preserves session state for retry

#### Scenario: Invalid card ID
- **WHEN** card ID is not found in Anki
- **THEN** system logs error with card details
- **AND** skips card gracefully
- **AND** continues to next card

## Implementation Notes

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
        result = await self.invoke(
            "answerCards",
            answers=[{"cardId": card_id, "ease": ease}]
        )
        return result[0] if result else False
    
    async def get_card_info(self, card_id: int) -> dict:
        """Get card state from Anki.
        
        Args:
            card_id: Anki card ID
            
        Returns:
            Card info dict with interval, factor, etc.
        """
        result = await self.invoke("cardsInfo", cards=[card_id])
        return result[0] if result else {}
    
    async def get_reviews(self, card_ids: list[int]) -> dict:
        """Get review history for cards.
        
        Args:
            card_ids: List of Anki card IDs
            
        Returns:
            Dict mapping card_id to list of reviews
        """
        return await self.invoke("getReviewsOfCards", cards=card_ids)
```

### Configuration

```yaml
# config.yaml
anki:
  url: "http://localhost:8765"
  timeout: 10.0
  scheduler:
    enabled: true
    ease_mapping:
      correct: 4  # Easy
      incorrect: 1  # Again
```

## Testing Requirements

- Unit tests for all new AnkiClient methods
- Mock AnkiConnect responses in tests
- Integration tests for review submission flow
- Error handling tests for connection failures
- Manual testing with real Anki Desktop

## Dependencies

- Anki Desktop with AnkiConnect addon
- AnkiConnect API v6+
- Running Anki instance during learning sessions
