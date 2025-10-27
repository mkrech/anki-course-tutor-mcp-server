"""Tests for learning engine."""

import pytest

from anki_course_tutor.learning_engine import AnswerEvaluator, LearningEngine
from anki_course_tutor.models import (
    Card,
    CardType,
    LearningMode,
    LearningState,
    Session,
    SessionStatus,
)


@pytest.fixture
def sample_session():
    """Create sample session."""
    return Session(
        session_id="test-session-1",
        deck_name="TestDeck",
        card_ids=["card-1", "card-2", "card-3"],
        mode=LearningMode.EXPLAIN,
        status=SessionStatus.IN_PROGRESS,
    )


@pytest.fixture
def sample_cards():
    """Create sample cards."""
    return [
        Card(
            id="card-1",
            type=CardType.BASIC,
            question="What is Python?",
            answer="A programming language",
            deck="TestDeck",
        ),
        Card(
            id="card-2",
            type=CardType.CLOZE,
            question="Python was created by [...]",
            answer="Guido van Rossum",
            cloze_text="Python was created by {{c1::Guido van Rossum}}",
            deck="TestDeck",
        ),
        Card(
            id="card-3",
            type=CardType.MULTIPLE_CHOICE,
            question="What is 2+2?",
            answer="4",
            options=["3", "4", "5", "6"],
            deck="TestDeck",
        ),
    ]


@pytest.fixture
def anki_cards():
    """Create sample cards with numeric IDs for Anki integration tests."""
    return [
        Card(
            id="1",  # Numeric ID as string
            type=CardType.BASIC,
            question="What is Python?",
            answer="A programming language",
            deck="TestDeck",
        ),
        Card(
            id="2",
            type=CardType.CLOZE,
            question="Python was created by [...]",
            answer="Guido van Rossum",
            cloze_text="Python was created by {{c1::Guido van Rossum}}",
            deck="TestDeck",
        ),
        Card(
            id="3",
            type=CardType.MULTIPLE_CHOICE,
            question="What is 2+2?",
            answer="4",
            options=["3", "4", "5", "6"],
            deck="TestDeck",
        ),
    ]


class TestAnswerEvaluator:
    """Tests for AnswerEvaluator."""

    def test_evaluate_basic_exact_match(self):
        """Test basic card evaluation with exact match."""
        result = AnswerEvaluator.evaluate_basic("Python", "Python")
        assert result is True

    def test_evaluate_basic_case_insensitive(self):
        """Test basic card evaluation is case-insensitive."""
        result = AnswerEvaluator.evaluate_basic("python", "Python")
        assert result is True

    def test_evaluate_basic_whitespace(self):
        """Test basic card evaluation handles whitespace."""
        result = AnswerEvaluator.evaluate_basic("  Python  ", "Python")
        assert result is True

    def test_evaluate_basic_with_variants(self):
        """Test basic card evaluation with answer variants."""
        result = AnswerEvaluator.evaluate_basic("Python", "Python|programming language")
        assert result is True

        result = AnswerEvaluator.evaluate_basic(
            "programming language", "Python|programming language"
        )
        assert result is True

    def test_evaluate_basic_incorrect(self):
        """Test basic card evaluation with incorrect answer."""
        result = AnswerEvaluator.evaluate_basic("Java", "Python")
        assert result is False

    def test_evaluate_cloze_single(self):
        """Test single cloze card evaluation."""
        result = AnswerEvaluator.evaluate_cloze("Guido van Rossum", "Guido van Rossum")
        assert result is True

        result = AnswerEvaluator.evaluate_cloze("guido van rossum", "Guido van Rossum")
        assert result is True

        result = AnswerEvaluator.evaluate_cloze("wrong", "Guido van Rossum")
        assert result is False

    def test_evaluate_cloze_multiple(self):
        """Test multiple cloze deletions."""
        # Perfect match
        result = AnswerEvaluator.evaluate_cloze("kⁿ-1, 1", "kⁿ-1, 1")
        assert result is True

        # Case insensitive and spacing variations
        result = AnswerEvaluator.evaluate_cloze("k^n-1,1", "kⁿ-1, 1")
        assert result is True  # Different Unicode but same meaning

        result = AnswerEvaluator.evaluate_cloze("k^n-1 , 1 ", "kⁿ-1, 1")
        assert result is True  # Extra spaces

        # Wrong number of parts
        result = AnswerEvaluator.evaluate_cloze("kⁿ-1", "kⁿ-1, 1")
        assert result is False

        result = AnswerEvaluator.evaluate_cloze("kⁿ-1, 1, 2", "kⁿ-1, 1")
        assert result is False

        # Wrong answers
        result = AnswerEvaluator.evaluate_cloze("wrong, 1", "kⁿ-1, 1")
        assert result is False

        result = AnswerEvaluator.evaluate_cloze("kⁿ-1, wrong", "kⁿ-1, 1")
        assert result is False

    def test_evaluate_cloze_three_parts(self):
        """Test cloze with three parts."""
        result = AnswerEvaluator.evaluate_cloze("a, b, c", "a, b, c")
        assert result is True

        result = AnswerEvaluator.evaluate_cloze("A,B,C", "a, b, c")
        assert result is True

        result = AnswerEvaluator.evaluate_cloze("a, b, wrong", "a, b, c")
        assert result is False

    def test_evaluate_cloze_mathematical_expressions(self):
        """Test cloze with mathematical expressions as in the user example."""
        # User's example: Bei der Enumeration [...] Parameter, da [...] summieren müssen.
        result = AnswerEvaluator.evaluate_cloze("kⁿ-1, 1", "kⁿ-1, 1")
        assert result is True

        # User types with normal characters
        result = AnswerEvaluator.evaluate_cloze("k^n-1, 1", "kⁿ-1, 1")
        assert result is True

        # With spaces
        result = AnswerEvaluator.evaluate_cloze("k^n - 1, 1", "kⁿ-1, 1")
        assert result is True

        # Different mathematical notations
        result = AnswerEvaluator.evaluate_cloze("2², 4", "2^2, 4")
        assert result is True

        result = AnswerEvaluator.evaluate_cloze("x³ + y², z", "x^3+y^2, z")
        assert result is True

    def test_evaluate_multiple_choice(self):
        """Test multiple choice evaluation."""
        result = AnswerEvaluator.evaluate_multiple_choice("4", "4")
        assert result is True

        result = AnswerEvaluator.evaluate_multiple_choice("3", "4")
        assert result is False


class TestLearningEngine:
    """Tests for LearningEngine."""

    def test_initialization(self, sample_session, sample_cards):
        """Test learning engine initialization."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.EXPLAIN)

        assert engine.session == sample_session
        assert engine.mode == LearningMode.EXPLAIN
        assert len(engine._cards) == 3

    def test_start_session(self, sample_session, sample_cards):
        """Test starting a learning session."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.EXPLAIN)

        result = engine.start()

        assert result["state"] == "awaiting_answer"
        assert result["card_id"] == "card-1"
        assert "question" in result
        assert engine.session.state == LearningState.AWAITING_ANSWER

    def test_start_empty_session(self, sample_session):
        """Test starting session with no cards."""
        engine = LearningEngine(sample_session, [], LearningMode.EXPLAIN)

        result = engine.start()

        assert result["state"] == "session_complete"
        assert engine.session.state == LearningState.SESSION_COMPLETE

    def test_submit_answer_correct(self, sample_session, sample_cards):
        """Test submitting a correct answer."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.EXPLAIN)
        engine.start()

        result = engine.submit_answer("A programming language")

        assert result["state"] == "awaiting_review"
        assert result["automatic_evaluation"] is True
        assert engine.session.state == LearningState.AWAITING_REVIEW

    def test_submit_answer_incorrect(self, sample_session, sample_cards):
        """Test submitting an incorrect answer."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.EXPLAIN)
        engine.start()

        result = engine.submit_answer("Wrong answer")

        assert result["state"] == "awaiting_review"
        assert result["automatic_evaluation"] is False
        assert engine.session.state == LearningState.AWAITING_REVIEW

    async def test_confirm_evaluation_correct(self, sample_session, sample_cards):
        """Test confirming a correct evaluation."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.EXPLAIN)
        engine.start()

        first_card_id = engine.current_card.id

        engine.submit_answer("A programming language")

        result = await engine.confirm_evaluation(is_correct=True)

        # Should move to next card
        assert result["state"] == "awaiting_answer"
        assert result["card_id"] == "card-2"
        
        # Check stats to verify completion
        stats = engine._get_stats()
        assert stats["completed_cards"] == 1

        # Should show result
        assert result["previous_result"] == "correct"
        assert result["previous_card_id"] == first_card_id

    async def test_confirm_evaluation_incorrect_explain_mode(self, sample_session, sample_cards):
        """Test confirming incorrect in EXPLAIN mode."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.EXPLAIN)
        engine.start()

        # Record first card
        first_card_id = engine.current_card.id

        engine.submit_answer("Wrong answer")

        result = await engine.confirm_evaluation(is_correct=False)

        # Should enter explaining state
        assert result["state"] == "explaining"
        assert engine.session.state == LearningState.EXPLAINING
        # Current card should still be the same (for explanation context)
        assert engine.current_card.id == first_card_id
        assert result["card_id"] == first_card_id
        # But card is already in retry queue
        stats = engine._get_stats()
        assert stats["retry_cards"] == 1

    async def test_confirm_evaluation_incorrect_test_mode(self, sample_session, sample_cards):
        """Test confirming incorrect in TEST mode shows result."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.TEST)
        engine.start()

        # Record card ID before answer
        first_card_id = engine.current_card.id
        first_card_answer = engine.current_card.answer

        engine.submit_answer("Wrong answer")
        result = await engine.confirm_evaluation(is_correct=False)

        # Should move to next card and show result
        assert result["state"] == "awaiting_answer"
        assert result["card_id"] != first_card_id  # Moved to next card

        # Should show result of previous card
        assert result["previous_result"] == "incorrect"
        assert result["previous_card_id"] == first_card_id
        assert result["previous_correct_answer"] == first_card_answer

    async def test_user_override_evaluation(self, sample_session, sample_cards):
        """Test user overriding automatic evaluation."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.EXPLAIN)
        engine.start()

        # Submit correct answer but user says it's wrong
        engine.submit_answer("A programming language")
        result = await engine.confirm_evaluation(is_correct=False)

        # Should respect user's decision
        assert result["state"] == "explaining"
        stats = engine._get_stats()
        assert stats["retry_cards"] == 1

    @pytest.mark.asyncio
    async def test_get_explanation(self, sample_session, sample_cards):
        """Test getting explanation."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.EXPLAIN)
        engine.start()
        engine.submit_answer("Wrong")
        await engine.confirm_evaluation(is_correct=False)

        result = await engine.get_explanation()

        assert result["state"] == "explaining"
        assert "explanation" in result
        assert result["card_id"] == sample_cards[0].id

    @pytest.mark.asyncio
    async def test_next_card_after_explanation(self, sample_session, sample_cards):
        """Test moving to next card after explanation."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.EXPLAIN)
        engine.start()

        # Record first card ID
        first_card_id = engine.current_card.id

        engine.submit_answer("Wrong")
        await engine.confirm_evaluation(is_correct=False)

        # In EXPLAIN mode with incorrect answer, card is in retry queue
        # but current_card is still set for explanation context
        assert engine.session.state == LearningState.EXPLAINING
        assert engine.current_card.id == first_card_id

        await engine.get_explanation()

        result = engine.next_card_after_explanation()

        # After explanation, should move to next new card
        assert result["state"] == "awaiting_answer"
        # Now should have moved to second card (first is in retry queue)
        assert result["card_id"] != first_card_id

    async def test_complete_session(self, sample_session, sample_cards):
        """Test completing all cards."""
        engine = LearningEngine(sample_session, sample_cards[:1], LearningMode.TEST)
        engine.start()
        engine.submit_answer("A programming language")

        result = await engine.confirm_evaluation(is_correct=True)

        assert result["state"] == "session_complete"
        assert engine.session.state == LearningState.SESSION_COMPLETE
        assert "stats" in result

    def test_multiple_choice_card(self, sample_session, sample_cards):
        """Test presenting multiple choice card."""
        mc_card = sample_cards[2]
        engine = LearningEngine(sample_session, [mc_card], LearningMode.EXPLAIN)

        result = engine.start()

        assert result["card_type"] == "multiple_choice"
        assert "options" in result
        assert len(result["options"]) == 4

    async def test_card_progress_tracking(self, sample_session, sample_cards):
        """Test that card progress is tracked."""
        engine = LearningEngine(sample_session, sample_cards[:1], LearningMode.EXPLAIN)
        engine.start()
        engine.submit_answer("A programming language")
        await engine.confirm_evaluation(is_correct=True)

        # Check progress was recorded
        assert "card-1" in engine.session.card_progress
        progress = engine.session.card_progress["card-1"]
        assert progress.attempts == 1
        assert progress.correct_count == 1
        assert progress.incorrect_count == 0

    async def test_retry_incorrect_card(self, sample_session, sample_cards):
        """Test that incorrect cards are retried after all new cards."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.TEST)
        engine.start()

        # Answer first card incorrectly
        first_card_id = engine.current_card.id
        engine.submit_answer("Wrong")
        await engine.confirm_evaluation(is_correct=False)

        # Card is now in retry queue, but we continue with new cards first
        stats = engine._get_stats()
        assert stats["retry_cards"] == 1

        # Answer second card correctly
        engine.submit_answer("Guido van Rossum")
        await engine.confirm_evaluation(is_correct=True)

        # Answer third card correctly
        engine.submit_answer("4")
        result = await engine.confirm_evaluation(is_correct=True)

        # After all new cards, retry queue should present first card again
        assert result["state"] == "awaiting_answer"
        assert result["card_id"] == first_card_id  # Back to first card for retry

    def test_get_current_state(self, sample_session, sample_cards):
        """Test getting current state."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.EXPLAIN)
        engine.start()

        state = engine.get_current_state()

        assert state["state"] == "awaiting_answer"
        assert state["current_card_id"] == "card-1"
        assert state["mode"] == "explain"
        assert "stats" in state

    async def test_invalid_state_transitions(self, sample_session, sample_cards):
        """Test that invalid state transitions are rejected."""
        engine = LearningEngine(sample_session, sample_cards, LearningMode.EXPLAIN)

        # Try to submit answer before starting
        result = engine.submit_answer("Test")
        assert "error" in result

        # Start properly
        engine.start()

        # Try to confirm before submitting
        result = await engine.confirm_evaluation(True)
        assert "error" in result


@pytest.mark.asyncio
class TestAnkiSchedulerIntegration:
    """Tests for Anki scheduler integration."""

    async def test_confirm_evaluation_submits_to_anki_correct(
        self, sample_session, anki_cards
    ):
        """Test that correct answer submits ease=4 to Anki."""
        from unittest.mock import AsyncMock

        mock_anki_client = AsyncMock()
        engine = LearningEngine(
            sample_session, anki_cards, LearningMode.EXPLAIN, anki_client=mock_anki_client
        )
        engine.start()
        engine.submit_answer("A programming language")

        result = await engine.confirm_evaluation(is_correct=True)

        # Should have called answer_card with ease=4
        mock_anki_client.answer_card.assert_awaited_once_with(card_id=1, ease=4)
        assert result["state"] == "awaiting_answer"

    async def test_confirm_evaluation_submits_to_anki_incorrect(
        self, sample_session, anki_cards
    ):
        """Test that incorrect answer submits ease=1 to Anki."""
        from unittest.mock import AsyncMock

        mock_anki_client = AsyncMock()
        engine = LearningEngine(
            sample_session, anki_cards, LearningMode.EXPLAIN, anki_client=mock_anki_client
        )
        engine.start()
        engine.submit_answer("Wrong answer")

        result = await engine.confirm_evaluation(is_correct=False)

        # Should have called answer_card with ease=1
        mock_anki_client.answer_card.assert_awaited_once_with(card_id=1, ease=1)
        assert result["state"] == "explaining"

    async def test_confirm_evaluation_without_anki_client(
        self, sample_session, anki_cards
    ):
        """Test that learning works without AnkiClient (local mode)."""
        engine = LearningEngine(
            sample_session, anki_cards, LearningMode.TEST, anki_client=None
        )
        engine.start()
        engine.submit_answer("A programming language")

        result = await engine.confirm_evaluation(is_correct=True)

        # Should work normally without Anki
        assert result["state"] == "awaiting_answer"
        assert result["previous_result"] == "correct"

    async def test_anki_submission_failure(self, sample_session, anki_cards):
        """Test that Anki submission failure returns error."""
        from unittest.mock import AsyncMock

        mock_anki_client = AsyncMock()
        mock_anki_client.answer_card.side_effect = Exception("Connection failed")

        engine = LearningEngine(
            sample_session, anki_cards, LearningMode.EXPLAIN, anki_client=mock_anki_client
        )
        engine.start()
        engine.submit_answer("A programming language")

        result = await engine.confirm_evaluation(is_correct=True)

        # Should return error
        assert "error" in result
        assert result["state"] == "error"
        assert "Anki" in result["error"]

    async def test_invalid_card_id_fails(self, sample_session):
        """Test that non-integer card ID fails gracefully."""
        from unittest.mock import AsyncMock
        from anki_course_tutor.models import Card, CardType

        mock_anki_client = AsyncMock()

        # Create card with invalid (non-numeric) ID
        invalid_card = Card(
            id="not-a-number",
            type=CardType.BASIC,
            question="Test",
            answer="Answer",
            deck="Test",
        )

        engine = LearningEngine(
            sample_session, [invalid_card], LearningMode.TEST, anki_client=mock_anki_client
        )
        engine.start()
        engine.submit_answer("Answer")

        result = await engine.confirm_evaluation(is_correct=True)

        # Should return error about invalid card ID
        assert "error" in result
        assert "Invalid card ID" in result["error"]
