"""AI Tutor with personality rotation and context-aware explanations."""

import logging
import re
from enum import Enum
from typing import Any

from anki_course_tutor.models.card import Card
from anki_course_tutor.models.session import LearningMode

logger = logging.getLogger(__name__)


class Personality(Enum):
    """Tutor personality types."""

    NORMAL = "normal"
    PIRATE = "pirate"


class PersonalityRotation:
    """Manages rotation between tutor personalities (3 normal : 1 pirate)."""

    def __init__(self, current_count: int = 0):
        """Initialize personality rotation.

        Args:
            current_count: Current explanation count from session
        """
        self.count = current_count
        logger.debug(f"Initialized PersonalityRotation with count={current_count}")

    def get_next_personality(self) -> Personality:
        """Get next personality based on rotation pattern.

        Rotation: Normal, Normal, Normal, Pirate, repeat...

        Returns:
            Next personality to use
        """
        # Increment count
        self.count += 1

        # Every 4th explanation is pirate (positions 4, 8, 12, ...)
        if self.count % 4 == 0:
            personality = Personality.PIRATE
            logger.info(f"Explanation #{self.count}: Using PIRATE personality")
        else:
            personality = Personality.NORMAL
            logger.debug(f"Explanation #{self.count}: Using NORMAL personality")

        return personality

    def get_current_count(self) -> int:
        """Get current explanation count.

        Returns:
            Number of explanations generated in this session
        """
        return self.count


class AITutor:
    """AI tutor for generating contextual explanations with personality."""

    # Prompt templates
    NORMAL_PROMPT_TEMPLATE = """You are a helpful tutor explaining why an answer was incorrect.

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

    PIRATE_PROMPT_TEMPLATE = """Ahoy matey! Ye be a friendly pirate tutor helpin' a sailor learn.

Card Question: {question}
Correct Answer: {correct_answer}
User's Answer: {user_answer}
Card Type: {card_type}
Deck: {deck_name}

Explain in PIRATE SPEECH (MAX 5 SENTENCES) why:
1. The correct answer be the right treasure
2. The user's answer went astray
3. How to remember this on yer next voyage

Be encouraging and supportive, ye scallywag! Keep it brief and fun!"""

    def __init__(self, session_personality_count: int = 0):
        """Initialize AI tutor.

        Args:
            session_personality_count: Current explanation count from session
        """
        self.rotation = PersonalityRotation(session_personality_count)
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
                "personality": Personality.NORMAL.value,
                "count": self.rotation.get_current_count(),
            }

        # Get next personality
        personality = self.rotation.get_next_personality()

        # Select prompt template
        if personality == Personality.PIRATE:
            prompt_template = self.PIRATE_PROMPT_TEMPLATE
        else:
            prompt_template = self.NORMAL_PROMPT_TEMPLATE

        # Format prompt with card context
        prompt = prompt_template.format(
            question=card.question,
            correct_answer=correct_answer,
            user_answer=user_answer,
            card_type=card.type.value,
            deck_name=card.deck,
        )

        logger.debug(f"Generated prompt for {personality.value} personality")

        # TODO: FastMCP integration for actual LLM call
        # For now, return placeholder
        explanation = self._generate_placeholder_explanation(
            personality, card.question, correct_answer, user_answer
        )

        # Ensure max 5 sentences
        explanation = self._limit_sentences(explanation, max_sentences=5)

        return {
            "explanation": explanation,
            "personality": personality.value,
            "count": self.rotation.get_current_count(),
            "prompt": prompt,  # For debugging/testing
        }

    def _generate_placeholder_explanation(
        self, personality: Personality, question: str, correct_answer: str, user_answer: str
    ) -> str:
        """Generate placeholder explanation until FastMCP is integrated.

        Args:
            personality: Personality to use
            question: Card question
            correct_answer: Correct answer
            user_answer: User's answer

        Returns:
            Placeholder explanation text
        """
        if personality == Personality.PIRATE:
            return (
                f"Ahoy! The correct answer be '{correct_answer}', matey! "
                f"Ye answered '{user_answer}', which be off course. "
                f"Remember this treasure: {correct_answer}. "
                f"Practice makes perfect, ye scallywag! "
                f"Next time ye'll get it right, I be certain!"
            )
        else:
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

    def get_current_count(self) -> int:
        """Get current explanation count for session persistence.

        Returns:
            Number of explanations generated
        """
        return self.rotation.get_current_count()
