"""Data models for progress tracking."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SessionStatistics:
    """Statistics for a learning session."""

    total_cards: int = 0
    completed_cards: int = 0
    correct_rate: float = 0.0
    session_duration_seconds: int = 0
    total_attempts: int = 0
    correct_attempts: int = 0
    incorrect_attempts: int = 0


@dataclass
class Progress:
    """Progress tracking for a session."""

    session_id: str
    deck_name: str
    chapter: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    state: str = "in_progress"
    statistics: SessionStatistics = field(default_factory=SessionStatistics)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "deck_name": self.deck_name,
            "chapter": self.chapter,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "state": self.state,
            "statistics": {
                "total_cards": self.statistics.total_cards,
                "completed_cards": self.statistics.completed_cards,
                "correct_rate": self.statistics.correct_rate,
                "session_duration_seconds": self.statistics.session_duration_seconds,
                "total_attempts": self.statistics.total_attempts,
                "correct_attempts": self.statistics.correct_attempts,
                "incorrect_attempts": self.statistics.incorrect_attempts,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Progress":
        """Create Progress from dictionary."""
        stats_data = data.get("statistics", {})
        return cls(
            session_id=data["session_id"],
            deck_name=data["deck_name"],
            chapter=data.get("chapter", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            state=data.get("state", "in_progress"),
            statistics=SessionStatistics(
                total_cards=stats_data.get("total_cards", 0),
                completed_cards=stats_data.get("completed_cards", 0),
                correct_rate=stats_data.get("correct_rate", 0.0),
                session_duration_seconds=stats_data.get("session_duration_seconds", 0),
                total_attempts=stats_data.get("total_attempts", 0),
                correct_attempts=stats_data.get("correct_attempts", 0),
                incorrect_attempts=stats_data.get("incorrect_attempts", 0),
            ),
        )
