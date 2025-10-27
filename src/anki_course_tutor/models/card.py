"""Data models for cards."""

from dataclasses import dataclass
from enum import Enum


class CardType(Enum):
    """Types of flashcards."""

    BASIC = "basic"
    CLOZE = "cloze"
    MULTIPLE_CHOICE = "multiple_choice"


@dataclass
class Card:
    """Unified card model for all card types."""

    id: str
    type: CardType
    question: str
    answer: str
    deck: str = ""
    chapter: str = ""
    options: list[str] | None = None  # For multiple choice
    cloze_text: str | None = None  # For cloze cards
    tags: list[str] | None = None

    def __post_init__(self):
        """Validate card data."""
        if self.type == CardType.MULTIPLE_CHOICE and not self.options:
            raise ValueError("Multiple choice cards must have options")
        if self.type == CardType.CLOZE and not self.cloze_text:
            raise ValueError("Cloze cards must have cloze_text")
