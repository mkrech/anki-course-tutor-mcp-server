"""Learning engine with state machine for card learning flow."""

import logging
from datetime import datetime
from typing import Any

from anki_course_tutor.models import (
    Card,
    CardProgress,
    CardType,
    LearningMode,
    LearningState,
    Session,
)
from anki_course_tutor.scheduler import SimpleLearningScheduler

logger = logging.getLogger(__name__)


class AnswerEvaluator:
    """Evaluate user answers against card answers."""

    @staticmethod
    def evaluate_basic(user_answer: str, correct_answer: str) -> bool:
        """Evaluate Basic card answer.

        Case-insensitive comparison with whitespace normalization.

        Args:
            user_answer: User's answer
            correct_answer: Correct answer from card

        Returns:
            True if answers match
        """
        user_clean = user_answer.strip().lower()
        correct_clean = correct_answer.strip().lower()

        # Exact match
        if user_clean == correct_clean:
            return True

        # Check if answer is contained (for partial matches)
        # Split by common separators
        correct_variants = [
            variant.strip()
            for variant in correct_clean.replace(",", "|")
            .replace(";", "|")
            .replace("/", "|")
            .split("|")
        ]

        return user_clean in correct_variants or any(
            variant == user_clean for variant in correct_variants
        )

    @staticmethod
    def evaluate_cloze(user_answer: str, correct_answer: str) -> bool:
        """Evaluate Cloze card answer.

        Uses same logic as Basic.

        Args:
            user_answer: User's answer
            correct_answer: Correct answer from card

        Returns:
            True if answers match
        """
        return AnswerEvaluator.evaluate_basic(user_answer, correct_answer)

    @staticmethod
    def evaluate_multiple_choice(user_answer: str, correct_answer: str) -> bool:
        """Evaluate Multiple Choice card answer.

        Exact match required after normalization.

        Args:
            user_answer: User's selected option
            correct_answer: Correct option from card

        Returns:
            True if answers match
        """
        return user_answer.strip().lower() == correct_answer.strip().lower()


class LearningEngine:
    """Main learning engine with state machine."""

    def __init__(self, session: Session, cards: list[Card], mode: LearningMode):
        """Initialize learning engine.

        Args:
            session: Learning session
            cards: List of cards to learn
            mode: Learning mode (EXPLAIN or TEST)
        """
        self.session = session
        self.scheduler = SimpleLearningScheduler(cards)
        self.mode = mode
        self.current_card: Card | None = None
        self.current_user_answer: str | None = None
        self.automatic_evaluation: bool | None = None
        self.evaluator = AnswerEvaluator()

        logger.info(
            f"Initialized learning engine for session {session.session_id} "
            f"with {len(cards)} cards in {mode.value} mode"
        )

    def start(self) -> dict[str, Any]:
        """Start the learning session.

        Returns:
            Dictionary with first card presentation
        """
        self.session.state = LearningState.PRESENTING_CARD
        self.current_card = self.scheduler.get_next_card()

        if not self.current_card:
            self.session.state = LearningState.SESSION_COMPLETE
            return {"state": "session_complete", "message": "No cards to learn"}

        logger.info(f"Started learning session, presenting card {self.current_card.id}")

        return self._present_card()

    def submit_answer(self, user_answer: str) -> dict[str, Any]:
        """Submit an answer and get automatic evaluation.

        Args:
            user_answer: User's answer

        Returns:
            Dictionary with evaluation result for user review
        """
        if self.session.state != LearningState.AWAITING_ANSWER:
            return {
                "error": f"Cannot submit answer in state {self.session.state.value}"
            }

        if not self.current_card:
            return {"error": "No current card"}

        self.current_user_answer = user_answer
        self.session.state = LearningState.EVALUATING

        # Perform automatic evaluation
        self.automatic_evaluation = self._evaluate_answer(user_answer)

        self.session.state = LearningState.AWAITING_REVIEW

        logger.info(
            f"Card {self.current_card.id}: user answered, "
            f"automatic evaluation={self.automatic_evaluation}"
        )

        return {
            "state": "awaiting_review",
            "automatic_evaluation": self.automatic_evaluation,
            "correct_answer": self.current_card.answer,
            "message": (
                f"I think this is {'CORRECT' if self.automatic_evaluation else 'INCORRECT'}. "
                f"The answer is '{self.current_card.answer}'. "
                f"Do you agree? (confirm with 'correct' or 'incorrect')"
            ),
        }

    def confirm_evaluation(self, is_correct: bool) -> dict[str, Any]:
        """User confirms or overrides the automatic evaluation.

        Args:
            is_correct: True if user confirms answer is correct

        Returns:
            Dictionary with next action (explanation or next card)
        """
        if self.session.state != LearningState.AWAITING_REVIEW:
            return {
                "error": f"Cannot confirm evaluation in state {self.session.state.value}"
            }

        if not self.current_card:
            return {"error": "No current card"}

        # Update card progress
        self._update_card_progress(is_correct)

        # Mark in scheduler - this updates the queues immediately
        if is_correct:
            self.scheduler.mark_correct(self.current_card)
        else:
            self.scheduler.mark_incorrect(self.current_card)

        logger.info(
            f"Card {self.current_card.id}: user confirmed {is_correct}, "
            f"automatic was {self.automatic_evaluation}"
        )

        # Store card info before potentially moving to next
        previous_card_id = self.current_card.id
        previous_answer = self.current_card.answer

        # In EXPLAIN mode, show explanation if incorrect (but keep current card for context)
        if not is_correct and self.mode == LearningMode.EXPLAIN:
            self.session.state = LearningState.EXPLAINING
            return {
                "state": "explaining",
                "result": "incorrect",
                "card_id": self.current_card.id,
                "correct_answer": previous_answer,
                "message": "Ready for explanation. Request explanation to continue.",
            }

        # In TEST mode or correct answer, move to next card but show result
        next_card_result = self._next_card()
        
        # Add result information for user feedback
        next_card_result["previous_result"] = "correct" if is_correct else "incorrect"
        next_card_result["previous_card_id"] = previous_card_id
        if not is_correct:
            next_card_result["previous_correct_answer"] = previous_answer
        
        return next_card_result

    def get_explanation(self) -> dict[str, Any]:
        """Request explanation (to be filled by AI tutor).

        Returns:
            Dictionary with explanation placeholder
        """
        if self.session.state != LearningState.EXPLAINING:
            return {
                "error": f"Cannot get explanation in state {self.session.state.value}"
            }

        if not self.current_card:
            return {"error": "No current card"}

        # This will be enhanced by AI tutor
        return {
            "state": "explaining",
            "card_question": self.current_card.question,
            "card_answer": self.current_card.answer,
            "message": "Explanation will be provided by AI tutor",
        }

    def next_card_after_explanation(self) -> dict[str, Any]:
        """Move to next card after explanation.

        Returns:
            Dictionary with next card or completion
        """
        if self.session.state != LearningState.EXPLAINING:
            return {
                "error": f"Cannot move to next card from state {self.session.state.value}"
            }

        return self._next_card()

    def _present_card(self) -> dict[str, Any]:
        """Present current card to user.

        Returns:
            Dictionary with card presentation
        """
        if not self.current_card:
            return {"error": "No card to present"}

        self.session.state = LearningState.AWAITING_ANSWER
        self.session.current_card_index += 1

        result = {
            "state": "awaiting_answer",
            "card_id": self.current_card.id,
            "card_type": self.current_card.type.value,
            "question": self.current_card.question,
        }

        # Add options for multiple choice
        if self.current_card.type == CardType.MULTIPLE_CHOICE and self.current_card.options:
            result["options"] = self.current_card.options

        return result

    def _evaluate_answer(self, user_answer: str) -> bool:
        """Automatically evaluate user answer.

        Args:
            user_answer: User's answer

        Returns:
            True if answer is correct
        """
        if not self.current_card:
            return False

        card_type = self.current_card.type
        correct_answer = self.current_card.answer

        if card_type == CardType.BASIC:
            return self.evaluator.evaluate_basic(user_answer, correct_answer)
        elif card_type == CardType.CLOZE:
            return self.evaluator.evaluate_cloze(user_answer, correct_answer)
        elif card_type == CardType.MULTIPLE_CHOICE:
            return self.evaluator.evaluate_multiple_choice(user_answer, correct_answer)

        return False

    def _update_card_progress(self, is_correct: bool) -> None:
        """Update progress tracking for current card.

        Args:
            is_correct: Whether answer was correct
        """
        if not self.current_card:
            return

        card_id = self.current_card.id

        # Get or create progress
        if card_id not in self.session.card_progress:
            self.session.card_progress[card_id] = CardProgress(card_id=card_id)

        progress = self.session.card_progress[card_id]
        progress.attempts += 1
        progress.last_attempt = datetime.now()

        if is_correct:
            progress.correct_count += 1
            if progress.correct_count >= 2:  # Simple mastery rule
                progress.status = "mastered"
            else:
                progress.status = "learning"
        else:
            progress.incorrect_count += 1
            progress.status = "learning"

        logger.debug(
            f"Updated progress for card {card_id}: "
            f"{progress.attempts} attempts, {progress.correct_count} correct"
        )

    def _next_card(self) -> dict[str, Any]:
        """Move to next card.

        Returns:
            Dictionary with next card presentation or completion
        """
        self.current_card = self.scheduler.get_next_card()
        self.current_user_answer = None
        self.automatic_evaluation = None

        if not self.current_card:
            self.session.state = LearningState.SESSION_COMPLETE
            stats = self.scheduler.get_stats()
            logger.info("Learning session completed")
            return {
                "state": "session_complete",
                "message": "All cards completed!",
                "stats": stats,
            }

        self.session.state = LearningState.PRESENTING_CARD
        return self._present_card()

    def get_current_state(self) -> dict[str, Any]:
        """Get current state information.

        Returns:
            Dictionary with current state details
        """
        stats = self.scheduler.get_stats()

        return {
            "state": self.session.state.value,
            "current_card_id": self.current_card.id if self.current_card else None,
            "stats": stats,
            "mode": self.mode.value,
        }
