"""AI Tutor for generating context-aware explanations."""

import logging
import re
from typing import Any

from anki_course_tutor.models.card import Card
from anki_course_tutor.models.session import LearningMode

logger = logging.getLogger(__name__)


class AITutor:
    """AI tutor for generating contextual explanations."""

    # Prompt template
    PROMPT_TEMPLATE = """You are a helpful tutor explaining why an answer was incorrect.

Card Question: {question}
Correct Answer: {correct_answer}
User's Answer: {user_answer}
Card Type: {card_type}
Deck: {deck_name}

Provide a clear, concise explanation (MAX 5 SENTENCES) about:
1. Why the correct answer is right
2. Why the user's answer was wrong (if applicable)
3. How to remember this for next time

Be encouraging and supportive. Keep it brief and educational."""

    def __init__(self):
        """Initialize AI tutor."""
        logger.info("Initialized AITutor")

    async def generate_explanation(
        self,
        card: Card,
        user_answer: str,
        correct_answer: str,
        mode: LearningMode,
    ) -> dict[str, Any]:
        """Generate AI explanation for incorrect answer.

        Args:
            card: The card being explained
            user_answer: What the user answered
            correct_answer: The correct answer
            mode: Learning mode (EXPLAIN or TEST)

        Returns:
            Dictionary with explanation and metadata
        """
        # TEST mode should not generate explanations
        if mode == LearningMode.TEST:
            logger.warning("generate_explanation called in TEST mode, skipping")
            return {
                "explanation": "",
                "count": 0,
            }

        # Format prompt with card context
        prompt = self.PROMPT_TEMPLATE.format(
            question=card.question,
            correct_answer=correct_answer,
            user_answer=user_answer,
            card_type=card.type.value,
            deck_name=card.deck,
        )

        logger.debug("Generated explanation prompt")

        # TODO: FastMCP integration for actual LLM call
        # For now, return placeholder
        explanation = self._generate_placeholder_explanation(
            card.question, correct_answer, user_answer
        )

        # Ensure max 5 sentences
        explanation = self._limit_sentences(explanation, max_sentences=5)

        return {
            "explanation": explanation,
            "count": 1,
            "prompt": prompt,  # For debugging/testing
        }

    def _generate_placeholder_explanation(
        self, question: str, correct_answer: str, user_answer: str
    ) -> str:
        """Generate placeholder explanation until FastMCP is integrated.

        Args:
            question: Card question
            correct_answer: Correct answer
            user_answer: User's answer

        Returns:
            Placeholder explanation text
        """
        return (
            f"The correct answer is '{correct_answer}'. "
            f"You answered '{user_answer}', which is incorrect. "
            f"To remember this, try associating it with something familiar. "
            f"Don't worry, learning takes practice! "
            f"You'll get it next time."
        )

    def _limit_sentences(self, text: str, max_sentences: int = 5) -> str:
        """Limit text to maximum number of sentences.

        Args:
            text: Input text
            max_sentences: Maximum number of sentences to keep

        Returns:
            Truncated text with ellipsis if needed
        """
        # Split by sentence endings (., !, ?)
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())

        if len(sentences) <= max_sentences:
            return text

        # Take first N sentences and add ellipsis
        limited = " ".join(sentences[:max_sentences])
        logger.debug(f"Truncated explanation from {len(sentences)} to {max_sentences} sentences")
        return limited + "..."
