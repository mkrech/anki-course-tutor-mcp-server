"""Tests for learning scheduler."""

import pytest

from anki_course_tutor.models import Card, CardType
from anki_course_tutor.scheduler import SimpleLearningScheduler


@pytest.fixture
def sample_cards():
    """Create sample cards for testing."""
    return [
        Card(
            id="card-1",
            type=CardType.BASIC,
            question="Q1",
            answer="A1",
            deck="TestDeck",
        ),
        Card(
            id="card-2",
            type=CardType.BASIC,
            question="Q2",
            answer="A2",
            deck="TestDeck",
        ),
        Card(
            id="card-3",
            type=CardType.BASIC,
            question="Q3",
            answer="A3",
            deck="TestDeck",
        ),
    ]


class TestSimpleLearningScheduler:
    """Tests for SimpleLearningScheduler."""

    def test_initialization(self, sample_cards):
        """Test scheduler initialization."""
        scheduler = SimpleLearningScheduler(sample_cards)

        assert len(scheduler.new_queue) == 3
        assert len(scheduler.retry_queue) == 0
        assert len(scheduler.completed_cards) == 0

    def test_get_next_card(self, sample_cards):
        """Test getting next card from new queue."""
        scheduler = SimpleLearningScheduler(sample_cards)

        card = scheduler.get_next_card()

        assert card is not None
        assert card.id == "card-1"
        assert len(scheduler.new_queue) == 2

    def test_mark_correct(self, sample_cards):
        """Test marking card as correct."""
        scheduler = SimpleLearningScheduler(sample_cards)
        card = scheduler.get_next_card()

        scheduler.mark_correct(card)

        assert len(scheduler.completed_cards) == 1
        assert scheduler.completed_cards[0].id == "card-1"

    def test_mark_incorrect(self, sample_cards):
        """Test marking card as incorrect."""
        scheduler = SimpleLearningScheduler(sample_cards)
        card = scheduler.get_next_card()

        scheduler.mark_incorrect(card)

        assert len(scheduler.retry_queue) == 1
        assert scheduler.retry_queue[0].id == "card-1"

    def test_retry_queue_priority(self, sample_cards):
        """Test that new queue has priority over retry queue."""
        scheduler = SimpleLearningScheduler(sample_cards)

        # Get first card and mark incorrect
        card1 = scheduler.get_next_card()
        scheduler.mark_incorrect(card1)

        # Next card should be from new queue (card-2), not retry queue
        next_card = scheduler.get_next_card()
        assert next_card.id == "card-2"
        
        # After all new cards, should get retry card
        card3 = scheduler.get_next_card()
        assert card3.id == "card-3"
        
        # Now retry card should come
        retry_card = scheduler.get_next_card()
        assert retry_card.id == "card-1"

    def test_has_more_cards(self, sample_cards):
        """Test checking if more cards available."""
        scheduler = SimpleLearningScheduler(sample_cards)

        assert scheduler.has_more_cards() is True

        # Process all cards
        while scheduler.has_more_cards():
            card = scheduler.get_next_card()
            scheduler.mark_correct(card)

        assert scheduler.has_more_cards() is False

    def test_get_stats(self, sample_cards):
        """Test getting scheduler statistics."""
        scheduler = SimpleLearningScheduler(sample_cards)

        stats = scheduler.get_stats()

        assert stats["new_cards"] == 3
        assert stats["retry_cards"] == 0
        assert stats["completed_cards"] == 0
        assert stats["total_cards"] == 3

        # Process one card
        card = scheduler.get_next_card()
        scheduler.mark_correct(card)

        stats = scheduler.get_stats()
        assert stats["new_cards"] == 2
        assert stats["completed_cards"] == 1

    def test_peek_next(self, sample_cards):
        """Test peeking at next card without removing."""
        scheduler = SimpleLearningScheduler(sample_cards)

        peeked = scheduler.peek_next()
        assert peeked is not None
        assert peeked.id == "card-1"

        # Queue should not change
        assert len(scheduler.new_queue) == 3

        # Get next should return same card
        next_card = scheduler.get_next_card()
        assert next_card.id == "card-1"

    def test_reset(self, sample_cards):
        """Test resetting scheduler."""
        scheduler = SimpleLearningScheduler(sample_cards)

        # Process some cards
        card1 = scheduler.get_next_card()
        scheduler.mark_correct(card1)

        card2 = scheduler.get_next_card()
        scheduler.mark_incorrect(card2)

        # Reset
        scheduler.reset()

        assert len(scheduler.new_queue) == 3
        assert len(scheduler.retry_queue) == 0
        assert len(scheduler.completed_cards) == 0

    def test_empty_scheduler(self):
        """Test scheduler with no cards."""
        scheduler = SimpleLearningScheduler([])

        assert scheduler.has_more_cards() is False
        assert scheduler.get_next_card() is None
        assert scheduler.peek_next() is None

    def test_retry_card_multiple_times(self, sample_cards):
        """Test that card can be retried multiple times."""
        scheduler = SimpleLearningScheduler(sample_cards[:1])

        # Get and mark incorrect 3 times
        for _ in range(3):
            card = scheduler.get_next_card()
            assert card.id == "card-1"
            scheduler.mark_incorrect(card)

        # Should still have card in retry queue
        assert len(scheduler.retry_queue) == 1
        assert scheduler.has_more_cards() is True
