"""Progress tracking with in-memory storage and statistics calculation."""

import logging
from datetime import datetime
from typing import Any

from anki_course_tutor.models.progress import Progress, SessionStatistics
from anki_course_tutor.models.session import CardProgress

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Track learning progress in memory."""

    def __init__(self):
        """Initialize progress tracker with in-memory storage."""
        self._progress: dict[str, Progress] = {}
        self._card_progress: dict[str, dict[str, CardProgress]] = {}
        logger.info("Initialized ProgressTracker (in-memory mode)")

    def save(self, progress: Progress, card_progress: dict[str, CardProgress]) -> None:
        """Save progress to memory.

        Args:
            progress: Session progress metadata
            card_progress: Dictionary of card_id -> CardProgress
        """
        progress.last_updated = datetime.now()
        self._progress[progress.session_id] = progress
        self._card_progress[progress.session_id] = card_progress.copy()
        logger.debug(f"Saved progress for session {progress.session_id} to memory")

    def load(self, session_id: str) -> tuple[Progress, dict[str, CardProgress]]:
        """Load progress from memory.

        Args:
            session_id: Session identifier

        Returns:
            Tuple of (Progress, card_progress_dict)

        Raises:
            FileNotFoundError: If progress not found
        """
        if session_id not in self._progress:
            raise FileNotFoundError(f"Progress not found for session: {session_id}")
        
        progress = self._progress[session_id]
        card_progress = self._card_progress.get(session_id, {})
        logger.debug(f"Loaded progress for session {session_id} from memory")
        return progress, card_progress

    def delete(self, session_id: str) -> None:
        """Delete progress from memory."""
        if session_id in self._progress:
            del self._progress[session_id]
        if session_id in self._card_progress:
            del self._card_progress[session_id]
        logger.info(f"Deleted progress for session {session_id}")

    def list_progress_files(self) -> list[str]:
        """List all available progress session IDs."""
        return sorted(self._progress.keys())

    def exists(self, session_id: str) -> bool:
        """Check if progress exists."""
        return session_id in self._progress

    def calculate_statistics(
        self, card_progress: dict[str, CardProgress], session_start: datetime
    ) -> SessionStatistics:
        """Calculate session statistics from card progress."""
        total_cards = len(card_progress)
        completed_cards = sum(1 for cp in card_progress.values() if cp.attempts > 0)
        total_attempts = sum(cp.attempts for cp in card_progress.values())
        correct_attempts = sum(cp.correct_count for cp in card_progress.values())
        incorrect_attempts = sum(cp.incorrect_count for cp in card_progress.values())
        correct_rate = correct_attempts / total_attempts if total_attempts > 0 else 0.0
        session_duration = int((datetime.now() - session_start).total_seconds())

        return SessionStatistics(
            total_cards=total_cards,
            completed_cards=completed_cards,
            correct_rate=correct_rate,
            session_duration_seconds=session_duration,
            total_attempts=total_attempts,
            correct_attempts=correct_attempts,
            incorrect_attempts=incorrect_attempts,
        )

    def get_deck_summary(self, deck_name: str) -> dict[str, Any]:
        """Get aggregated statistics for all sessions of a deck."""
        total_cards_studied = set()
        total_attempts = 0
        total_correct = 0
        total_time = 0
        session_count = 0

        for session_id in self.list_progress_files():
            try:
                progress, card_progress = self.load(session_id)
                if progress.deck_name != deck_name:
                    continue
                session_count += 1
                total_cards_studied.update(card_progress.keys())
                total_attempts += progress.statistics.total_attempts
                total_correct += progress.statistics.correct_attempts
                total_time += progress.statistics.session_duration_seconds
            except Exception as e:
                logger.warning(f"Failed to load session {session_id}: {e}")
                continue

        avg_correct_rate = total_correct / total_attempts if total_attempts > 0 else 0.0

        return {
            "deck_name": deck_name,
            "total_sessions": session_count,
            "total_cards_studied": len(total_cards_studied),
            "total_attempts": total_attempts,
            "total_correct": total_correct,
            "average_correct_rate": avg_correct_rate,
            "total_time_seconds": total_time,
        }

    def export_session(self, session_id: str) -> dict[str, Any]:
        """Export complete session progress as JSON."""
        progress, card_progress = self.load(session_id)

        return {
            "session_metadata": progress.to_dict(),
            "card_progress": [
                {
                    "card_id": cp.card_id,
                    "attempts": cp.attempts,
                    "correct_count": cp.correct_count,
                    "incorrect_count": cp.incorrect_count,
                    "last_attempt": cp.last_attempt.isoformat() if cp.last_attempt else None,
                    "status": cp.status,
                }
                for cp in card_progress.values()
            ],
            "statistics": progress.statistics.__dict__,
        }
