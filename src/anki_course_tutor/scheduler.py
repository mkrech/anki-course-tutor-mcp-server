"""Simple learning scheduler for card queuing."""

import logging
from collections import deque

from anki_course_tutor.models import Card

logger = logging.getLogger(__name__)


class SimpleLearningScheduler:
    """Simple scheduler with new and retry queues."""

    def __init__(self, cards: list[Card]):
        """Initialize scheduler with cards.

        Args:
            cards: List of cards to schedule
        """
        self.new_queue: deque[Card] = deque(cards)
        self.retry_queue: deque[Card] = deque()
        self.completed_cards: list[Card] = []

        logger.info(f"Initialized scheduler with {len(cards)} cards")

    def get_next_card(self) -> Card | None:
        """Get the next card to present.

        Priority: new queue first, then retry queue.
        This ensures all cards are seen before retrying incorrect ones.

        Returns:
            Next card or None if all completed
        """
        # New cards have priority
        if self.new_queue:
            card = self.new_queue.popleft()
            logger.debug(f"Retrieved card from new queue: {card.id}")
            return card

        # Then retry cards
        if self.retry_queue:
            card = self.retry_queue.popleft()
            logger.debug(f"Retrieved card from retry queue: {card.id}")
            return card

        # All done
        logger.info("No more cards in queues")
        return None

    def mark_correct(self, card: Card) -> None:
        """Mark card as correctly answered.

        Args:
            card: Card that was answered correctly
        """
        self.completed_cards.append(card)
        logger.debug(f"Card {card.id} marked as correct (completed)")

    def mark_incorrect(self, card: Card) -> None:
        """Mark card as incorrectly answered and add to retry queue.

        Args:
            card: Card that was answered incorrectly
        """
        self.retry_queue.append(card)
        logger.debug(f"Card {card.id} marked as incorrect (added to retry queue)")

    def has_more_cards(self) -> bool:
        """Check if there are more cards to present.

        Returns:
            True if there are cards in either queue
        """
        return len(self.new_queue) > 0 or len(self.retry_queue) > 0

    def get_stats(self) -> dict[str, int]:
        """Get current scheduler statistics.

        Returns:
            Dictionary with queue sizes and completed count
        """
        return {
            "new_cards": len(self.new_queue),
            "retry_cards": len(self.retry_queue),
            "completed_cards": len(self.completed_cards),
            "total_cards": len(self.new_queue) + len(self.retry_queue) + len(self.completed_cards),
        }

    def peek_next(self) -> Card | None:
        """Peek at the next card without removing it.

        Returns:
            Next card or None
        """
        if self.retry_queue:
            return self.retry_queue[0]
        if self.new_queue:
            return self.new_queue[0]
        return None

    def reset(self) -> None:
        """Reset scheduler, moving all cards back to new queue."""
        all_cards = list(self.new_queue) + list(self.retry_queue) + self.completed_cards
        self.new_queue = deque(all_cards)
        self.retry_queue = deque()
        self.completed_cards = []
        logger.info("Scheduler reset")
