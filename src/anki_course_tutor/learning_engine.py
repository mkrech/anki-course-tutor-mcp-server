"""Learning engine with state machine for card learning flow."""

import logging
from collections import deque
from datetime import datetime
from typing import Any

from anki_course_tutor.ai_tutor import AITutor
from anki_course_tutor.anki_client import AnkiClient
from anki_course_tutor.models import (
    Card,
    CardProgress,
    CardType,
    LearningMode,
    LearningState,
    Session,
)

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
    def _normalize_math_expression(text: str) -> str:
        """Normalize mathematical expressions for comparison.
        
        Converts common mathematical notation variations to a standard form.
        
        Args:
            text: Input text that may contain mathematical expressions
            
        Returns:
            Normalized text
        """
        text = text.strip().lower()
        
        # Replace superscript characters with ^ notation
        superscript_map = {
            '⁰': '^0', '¹': '^1', '²': '^2', '³': '^3', '⁴': '^4', 
            '⁵': '^5', '⁶': '^6', '⁷': '^7', '⁸': '^8', '⁹': '^9',
            'ⁿ': '^n', 'ᵃ': '^a', 'ᵇ': '^b', 'ᶜ': '^c', 'ᵈ': '^d',
            'ᵉ': '^e', 'ᶠ': '^f', 'ᵍ': '^g', 'ʰ': '^h', 'ⁱ': '^i',
            'ʲ': '^j', 'ᵏ': '^k', 'ˡ': '^l', 'ᵐ': '^m', 'ᵒ': '^o',
            'ᵖ': '^p', 'ʳ': '^r', 'ˢ': '^s', 'ᵗ': '^t', 'ᵘ': '^u',
            'ᵛ': '^v', 'ʷ': '^w', 'ˣ': '^x', 'ʸ': '^y', 'ᶻ': '^z'
        }
        
        for superscript, replacement in superscript_map.items():
            text = text.replace(superscript, replacement)
        
        # Normalize common mathematical symbols
        text = text.replace('×', '*')
        text = text.replace('·', '*')
        text = text.replace('÷', '/')
        
        # Remove extra spaces around operators
        import re
        text = re.sub(r'\s*([+\-*/^=<>])\s*', r'\1', text)
        
        return text

    @staticmethod
    def evaluate_cloze(user_answer: str, correct_answer: str) -> bool:
        """Evaluate Cloze card answer.

        Supports multiple cloze deletions separated by commas.
        Normalizes mathematical expressions for better matching.
        
        Examples:
        - Single cloze: user="Paris", correct="Paris" -> True
        - Multiple cloze: user="kⁿ-1, 1", correct="kⁿ-1, 1" -> True
        - Multiple cloze: user="k^n-1,1", correct="kⁿ-1, 1" -> True (normalized)

        Args:
            user_answer: User's answer (may contain multiple answers separated by commas)
            correct_answer: Correct answer from card (may contain multiple answers)

        Returns:
            True if answers match
        """
        # Clean and split both answers by comma
        user_parts = [part.strip() for part in user_answer.split(',')]
        correct_parts = [part.strip() for part in correct_answer.split(',')]
        
        # Must have same number of parts
        if len(user_parts) != len(correct_parts):
            return False
        
        # Evaluate each part with mathematical normalization
        for user_part, correct_part in zip(user_parts, correct_parts):
            # First try basic evaluation
            if AnswerEvaluator.evaluate_basic(user_part, correct_part):
                continue
            
            # If basic fails, try with mathematical normalization
            user_normalized = AnswerEvaluator._normalize_math_expression(user_part)
            correct_normalized = AnswerEvaluator._normalize_math_expression(correct_part)
            
            if user_normalized != correct_normalized:
                return False
        
        return True

    @staticmethod
    def evaluate_all_in_one(
        user_answer: str, correct_answer: str, variant_type: str | None = None
    ) -> bool:
        """Evaluate All-in-One card answer.

        Supports KPRIM (partial credit), MC (multiple options), SC (single option).

        Args:
            user_answer: User's answer(s)
            correct_answer: Correct answer from card
            variant_type: AllInOne variant (KPRIM, MC, SC)

        Returns:
            True if answer is correct (for KPRIM: >=3 correct points)
        """
        if not variant_type:
            variant_type = "MC"

        # For KPRIM: user_answer format is "T/F,T/F,T/F,T/F" or similar
        # Score: 1 point per correct answer (max 4)
        if variant_type.upper() == "KPRIM":
            user_parts = [p.strip().upper() for p in user_answer.split(",")]
            correct_parts = [p.strip().upper() for p in correct_answer.split(",")]

            if len(user_parts) != len(correct_parts):
                return False

            correct_count = sum(1 for u, c in zip(user_parts, correct_parts) if u == c)
            # KPRIM: need >= 3 correct for pass (0-4 points, 3+ is pass)
            return correct_count >= 3

        # For MC/SC: use same logic as Multiple Choice
        return user_answer.strip().lower() == correct_answer.strip().lower()


class LearningEngine:
    """Main learning engine with state machine."""

    def __init__(
        self, 
        session: Session, 
        cards: list[Card], 
        mode: LearningMode,
        anki_client: AnkiClient | None = None
    ):
        """Initialize learning engine.

        Args:
            session: Learning session
            cards: List of cards to learn
            mode: Learning mode (EXPLAIN or TEST)
            anki_client: Optional AnkiConnect client for scheduler integration
        """
        self.session = session
        self._cards = cards  # All cards (sorted once at start)
        # Note: session.current_card_index is the index of the CURRENT card being presented
        # We want to continue from that card, so _current_index starts there
        self._current_index = session.current_card_index  # Position in _cards
        self._retry_queue: deque[str] = deque(session.retry_queue)  # Card IDs to retry
        self._card_map: dict[str, Card] = {card.id: card for card in cards}  # Fast lookup
        self.mode = mode
        self.anki_client = anki_client
        self.current_card: Card | None = None
        self.current_user_answer: str | None = None
        self.automatic_evaluation: bool | None = None
        self.evaluator = AnswerEvaluator()
        self.ai_tutor = AITutor()

        logger.info(
            f"Initialized learning engine for session {session.session_id} "
            f"with {len(cards)} cards in {mode.value} mode"
            + (", Anki scheduler enabled" if anki_client else ", local card ordering")
        )
    
    def _sync_session_state(self) -> None:
        """Synchronize session state with internal state.
        
        session.current_card_index tracks the index of the CURRENT card being presented,
        while _current_index tracks the next card to fetch.
        """
        if self.current_card:
            # Find current card's index in the cards list
            for i, card in enumerate(self._cards):
                if card.id == self.current_card.id:
                    self.session.current_card_index = i
                    return
        # If no current card or not found, use _current_index as fallback
        self.session.current_card_index = self._current_index

    async def _submit_review_to_anki(self, card: Card, is_correct: bool) -> None:
        """Submit review to Anki's scheduler.
        
        Args:
            card: Card that was reviewed
            is_correct: Whether the answer was correct
            
        Raises:
            Exception: If AnkiConnect submission fails
        """
        if not self.anki_client:
            logger.debug("No AnkiClient configured, skipping Anki review submission")
            return
        
        # Map correctness to Anki ease value
        # MVP: Binary mapping - correct=4 (Easy), incorrect=1 (Again)
        ease = 4 if is_correct else 1
        
        try:
            # Card ID must be an integer - convert from string if needed
            card_id = int(card.id)
            await self.anki_client.answer_card(card_id=card_id, ease=ease)
            logger.info(
                f"Submitted review to Anki: card_id={card_id}, "
                f"ease={ease} ({'correct' if is_correct else 'incorrect'})"
            )
        except ValueError as e:
            logger.error(f"Invalid card ID '{card.id}': {e}")
            raise Exception(f"Cannot submit review: Invalid card ID '{card.id}'") from e
        except Exception as e:
            logger.error(f"Failed to submit review to Anki for card {card.id}: {e}")
            raise Exception(
                f"Failed to submit review to Anki. "
                f"Please ensure Anki is running with AnkiConnect enabled."
            ) from e

    def _get_next_card_internal(self) -> Card | None:
        """Get the next card to present.
        
        Priority: new cards first, then retry queue.
        This ensures all cards are seen before retrying incorrect ones.
        
        Returns:
            Next card or None if all completed
        """
        # Priority 1: New cards (not yet seen)
        if self._current_index < len(self._cards):
            card = self._cards[self._current_index]
            self._current_index += 1
            # Note: Do NOT update session.current_card_index here
            # It will be synced when session is saved
            logger.debug(f"Retrieved new card: {card.id} (index {self._current_index}/{len(self._cards)})")
            return card
        
        # Priority 2: Retry queue (incorrectly answered cards)
        if self._retry_queue:
            card_id = self._retry_queue.popleft()
            card = self._card_map.get(card_id)
            if card:
                logger.debug(f"Retrieved card from retry queue: {card_id}")
                return card
            else:
                logger.warning(f"Card {card_id} in retry queue not found in card map")
                # Continue to next card
                return self._get_next_card_internal()
        
        # All done
        logger.info("No more cards in queues")
        return None

    def start(self) -> dict[str, Any]:
        """Start the learning session.

        Returns:
            Dictionary with first card presentation
        """
        self.session.state = LearningState.PRESENTING_CARD
        self.current_card = self._get_next_card_internal()
        
        # Sync session state for persistence
        self._sync_session_state()

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
            return {"error": f"Cannot submit answer in state {self.session.state.value}"}

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

        # Simple evaluation message
        if self.automatic_evaluation:
            message = f"CORRECT! The answer is '{self.current_card.answer}'. → Is this evaluation correct? (yes/no)"
        else:
            message = f"INCORRECT. The correct answer is '{self.current_card.answer}'. → Is this evaluation correct? (yes/no)"

        return {
            "state": "awaiting_review",
            "automatic_evaluation": self.automatic_evaluation,
            "correct_answer": self.current_card.answer,
            "message": message,
        }

    async def confirm_evaluation(self, is_correct: bool) -> dict[str, Any]:
        """User confirms or overrides the automatic evaluation.

        Args:
            is_correct: True if user confirms answer is correct

        Returns:
            Dictionary with next action (explanation or next card)
        """
        if self.session.state != LearningState.AWAITING_REVIEW:
            return {"error": f"Cannot confirm evaluation in state {self.session.state.value}"}

        if not self.current_card:
            return {"error": "No current card"}

        # Submit review to Anki scheduler (if enabled)
        try:
            await self._submit_review_to_anki(self.current_card, is_correct)
        except Exception as e:
            logger.error(f"Failed to submit review to Anki: {e}")
            # Return error to user - fail fast per design decision
            return {
                "error": str(e),
                "state": "error",
                "card_id": self.current_card.id,
            }

        # Update card progress
        self._update_card_progress(is_correct)

        # Update retry queue if incorrect
        if is_correct:
            logger.debug(f"Card {self.current_card.id} marked as correct (completed)")
        else:
            self._retry_queue.append(self.current_card.id)
            self.session.retry_queue.append(self.current_card.id)  # Persist
            logger.debug(f"Card {self.current_card.id} marked as incorrect (added to retry queue)")

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
                "message": f"The correct answer is '{previous_answer}'. Let me explain why...",
            }

        # In TEST mode or correct answer, move to next card but show result
        next_card_result = self._next_card()

        # Add result information for user feedback
        next_card_result["previous_result"] = "correct" if is_correct else "incorrect"
        next_card_result["previous_card_id"] = previous_card_id
        if not is_correct:
            next_card_result["previous_correct_answer"] = previous_answer

        return next_card_result

    async def get_explanation(self) -> dict[str, Any]:
        """Request AI explanation for incorrect answer.

        Returns:
            Dictionary with AI-generated explanation
        """
        if self.session.state != LearningState.EXPLAINING:
            return {"error": f"Cannot get explanation in state {self.session.state.value}"}

        if not self.current_card:
            return {"error": "No current card"}

        if not self.current_user_answer:
            return {"error": "No user answer recorded"}

        # Generate AI explanation
        result = await self.ai_tutor.generate_explanation(
            card=self.current_card,
            user_answer=self.current_user_answer,
            correct_answer=self.current_card.answer,
            mode=self.mode,
        )

        logger.info(
            f"Generated explanation for card {self.current_card.id}"
        )

        return {
            "state": "explaining",
            "card_id": self.current_card.id,
            "explanation": result["explanation"],
            "message": "Ready to continue. Call next_card_after_explanation.",
        }

    def next_card_after_explanation(self) -> dict[str, Any]:
        """Move to next card after explanation.

        Returns:
            Dictionary with next card or completion
        """
        if self.session.state != LearningState.EXPLAINING:
            return {"error": f"Cannot move to next card from state {self.session.state.value}"}

        return self._next_card()

    def _present_card(self) -> dict[str, Any]:
        """Present current card to user.

        Returns:
            Dictionary with card presentation
        """
        if not self.current_card:
            return {"error": "No card to present"}

        self.session.state = LearningState.AWAITING_ANSWER

        result = {
            "state": "awaiting_answer",
            "card_id": self.current_card.id,
            "card_type": self.current_card.type.value,
            "question": self.current_card.question,
            "message": "Here's your next question:",
        }

        # Add options for AllInOne/MC cards
        if self.current_card.type == CardType.ALL_IN_ONE and self.current_card.all_in_one_type == "MC" and self.current_card.fields:
            # Extract options from fields - support multiple naming conventions
            # Q_1, Q_2... or Option1, Option2... or Q1, Q2... etc
            options = []
            for k, v in sorted(self.current_card.fields.items()):
                # Match Q_X, QX, OptionX, etc. patterns
                if (k.startswith("Q_") or k.startswith("Q") or k.startswith("Option")) and any(c.isdigit() for c in k):
                    options.append(v)
            
            if options:
                result["options"] = options

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
        elif card_type == CardType.ALL_IN_ONE:
            return self.evaluator.evaluate_all_in_one(
                user_answer, correct_answer, self.current_card.all_in_one_type
            )

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
        self.current_card = self._get_next_card_internal()
        self.current_user_answer = None
        self.automatic_evaluation = None
        
        # Sync session state for persistence
        self._sync_session_state()

        if not self.current_card:
            self.session.state = LearningState.SESSION_COMPLETE
            stats = self._get_stats()
            logger.info("Learning session completed")
            return {
                "state": "session_complete",
                "message": "All cards completed! Great work! 🎉 Call end_session to finish.",
                "stats": stats,
            }

        self.session.state = LearningState.PRESENTING_CARD
        logger.info(f"Moving to next card {self.current_card.id}")
        return self._present_card()

    def _get_stats(self) -> dict[str, int]:
        """Get current learning statistics.
        
        Returns:
            Dictionary with queue sizes and completion stats
        """
        # Calculate from session progress
        completed_count = sum(
            1 for cp in self.session.card_progress.values()
            if cp.correct_count > 0
        )
        
        return {
            "new_cards": len(self._cards) - self._current_index,  # Remaining new cards
            "retry_cards": len(self._retry_queue),  # Cards in retry queue
            "completed_cards": completed_count,  # Cards answered correctly at least once
            "total_cards": len(self._cards),
        }

    def get_current_state(self) -> dict[str, Any]:
        """Get current state information.

        Returns:
            Dictionary with current state details
        """
        stats = self._get_stats()

        return {
            "state": self.session.state.value,
            "current_card_id": self.current_card.id if self.current_card else None,
            "stats": stats,
            "mode": self.mode.value,
        }
