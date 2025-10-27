"""Data models for learning sessions."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class LearningState(Enum):
    """States in the learning flow state machine."""

    NOT_STARTED = "not_started"
    PRESENTING_CARD = "presenting_card"
    AWAITING_ANSWER = "awaiting_answer"
    EVALUATING = "evaluating"
    AWAITING_REVIEW = "awaiting_review"
    EXPLAINING = "explaining"
    SESSION_COMPLETE = "session_complete"


class LearningMode(Enum):
    """Learning modes for AI tutor."""

    EXPLAIN = "explain"  # Provides explanations
    TEST = "test"  # No explanations, just testing


class SessionStatus(Enum):
    """Status of a learning session."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class CardProgress:
    """Progress tracking for a single card in a session."""

    card_id: str
    attempts: int = 0
    correct_count: int = 0
    incorrect_count: int = 0
    last_attempt: datetime | None = None
    status: str = "new"  # new, learning, mastered


@dataclass
class Session:
    """Learning session data."""

    session_id: str
    deck_name: str
    chapter: str = ""
    mode: LearningMode = LearningMode.EXPLAIN
    state: LearningState = LearningState.NOT_STARTED
    status: SessionStatus = SessionStatus.NOT_STARTED
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    card_ids: list[str] = field(default_factory=list)
    current_card_index: int = 0
    card_progress: dict[str, CardProgress] = field(default_factory=dict)
    personality_count: int = 0  # Track personality rotation

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "deck_name": self.deck_name,
            "chapter": self.chapter,
            "mode": self.mode.value,
            "state": self.state.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "card_ids": self.card_ids,
            "current_card_index": self.current_card_index,
            "card_progress": {
                card_id: {
                    "card_id": cp.card_id,
                    "attempts": cp.attempts,
                    "correct_count": cp.correct_count,
                    "incorrect_count": cp.incorrect_count,
                    "last_attempt": cp.last_attempt.isoformat() if cp.last_attempt else None,
                    "status": cp.status,
                }
                for card_id, cp in self.card_progress.items()
            },
            "personality_count": self.personality_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        """Create Session from dictionary."""
        return cls(
            session_id=data["session_id"],
            deck_name=data["deck_name"],
            chapter=data.get("chapter", ""),
            mode=LearningMode(data.get("mode", "explain")),
            state=LearningState(data.get("state", "not_started")),
            status=SessionStatus(data.get("status", "not_started")),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            card_ids=data.get("card_ids", []),
            current_card_index=data.get("current_card_index", 0),
            card_progress={
                card_id: CardProgress(
                    card_id=cp["card_id"],
                    attempts=cp["attempts"],
                    correct_count=cp["correct_count"],
                    incorrect_count=cp["incorrect_count"],
                    last_attempt=datetime.fromisoformat(cp["last_attempt"])
                    if cp["last_attempt"]
                    else None,
                    status=cp.get("status", "new"),
                )
                for card_id, cp in data.get("card_progress", {}).items()
            },
            personality_count=data.get("personality_count", 0),
        )
