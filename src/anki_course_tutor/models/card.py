"""Data models for cards."""

from dataclasses import dataclass
from enum import Enum


class CardType(Enum):
    """Types of flashcards."""

    BASIC = "basic"
    CLOZE = "cloze"
    ALL_IN_ONE = "all_in_one"


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
    fields: dict[str, str] | None = None  # For AllInOne cards
    all_in_one_type: str | None = None  # KPRIM, MC, SC

    def __post_init__(self):
        """Validate card data."""
        if self.type == CardType.CLOZE and not self.cloze_text:
            raise ValueError("Cloze cards must have cloze_text")
        if self.type == CardType.ALL_IN_ONE and not self.fields:
            raise ValueError("AllInOne cards must have fields")
