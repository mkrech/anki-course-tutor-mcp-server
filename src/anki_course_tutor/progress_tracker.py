"""Progress tracking with JSON persistence and statistics calculation."""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from anki_course_tutor.models.progress import Progress, SessionStatistics
from anki_course_tutor.models.session import CardProgress

logger = logging.getLogger(__name__)


class ProgressTracker:
    """Track and persist learning progress with statistics."""

    def __init__(self, progress_dir: Path | str = "data/progress"):
        """Initialize progress tracker.

        Args:
            progress_dir: Directory for progress JSON files
        """
        self.progress_dir = Path(progress_dir)
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initialized ProgressTracker with directory: {self.progress_dir}")

    def save(self, progress: Progress, card_progress: dict[str, CardProgress]) -> None:
        """Save progress to JSON with atomic write and backup.

        Args:
            progress: Session progress metadata
            card_progress: Dictionary of card_id -> CardProgress
        """
        file_path = self._get_progress_file(progress.session_id)
        backup_path = self._get_backup_file(progress.session_id)
        temp_path = file_path.with_suffix(".tmp")

        # Update timestamp
        progress.last_updated = datetime.now()

        # Build complete data structure
        data = {
            **progress.to_dict(),
            "cards": {
                card_id: {
                    "card_id": cp.card_id,
                    "attempts": cp.attempts,
                    "correct_count": cp.correct_count,
                    "incorrect_count": cp.incorrect_count,
                    "last_attempt": cp.last_attempt.isoformat() if cp.last_attempt else None,
                    "status": cp.status,
                }
                for card_id, cp in card_progress.items()
            },
        }

        try:
            # Create backup if file exists
            if file_path.exists():
                shutil.copy2(file_path, backup_path)
                logger.debug(f"Created backup: {backup_path}")

            # Write to temporary file
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_path.replace(file_path)
            logger.info(f"Saved progress for session {progress.session_id}")

        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()
            raise

    def load(self, session_id: str) -> tuple[Progress, dict[str, CardProgress]]:
        """Load progress from JSON with validation.

        Args:
            session_id: Session identifier

        Returns:
            Tuple of (Progress, card_progress_dict)

        Raises:
            FileNotFoundError: If progress file doesn't exist
            ValueError: If validation fails
        """
        file_path = self._get_progress_file(session_id)
        backup_path = self._get_backup_file(session_id)

        # Try loading from main file first
        try:
            data = self._load_and_validate(file_path)
        except Exception as e:
            logger.warning(f"Failed to load from main file: {e}")

            # Try backup
            if backup_path.exists():
                logger.info("Attempting to load from backup")
                try:
                    data = self._load_and_validate(backup_path)
                    # Restore from backup
                    shutil.copy2(backup_path, file_path)
                    logger.info("Restored from backup successfully")
                except Exception as backup_e:
                    logger.error(f"Failed to load from backup: {backup_e}")
                    raise ValueError("Both main and backup files are corrupted") from e
            else:
                raise FileNotFoundError(f"Progress file not found: {file_path}") from e

        # Parse progress
        progress = Progress.from_dict(data)

        # Parse card progress
        card_progress = {}
        cards_data = data.get("cards", {})
        for card_id, cp_data in cards_data.items():
            card_progress[card_id] = CardProgress(
                card_id=cp_data["card_id"],
                attempts=cp_data.get("attempts", 0),
                correct_count=cp_data.get("correct_count", 0),
                incorrect_count=cp_data.get("incorrect_count", 0),
                last_attempt=(
                    datetime.fromisoformat(cp_data["last_attempt"])
                    if cp_data.get("last_attempt")
                    else None
                ),
                status=cp_data.get("status", "new"),
            )

        logger.info(f"Loaded progress for session {session_id} with {len(card_progress)} cards")
        return progress, card_progress

    def _load_and_validate(self, file_path: Path) -> dict[str, Any]:
        """Load and validate JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Validated JSON data

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If validation fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        # Validate required fields
        required_fields = ["session_id", "deck_name"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Validate structure
        if "statistics" not in data:
            logger.warning("Missing statistics field, using defaults")
            data["statistics"] = {}

        if "cards" not in data:
            logger.warning("Missing cards field, using empty dict")
            data["cards"] = {}

        return data

    def delete(self, session_id: str) -> None:
        """Delete progress file and backup.

        Args:
            session_id: Session identifier
        """
        file_path = self._get_progress_file(session_id)
        backup_path = self._get_backup_file(session_id)

        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted progress file: {file_path}")

        if backup_path.exists():
            backup_path.unlink()
            logger.debug(f"Deleted backup file: {backup_path}")

    def list_progress_files(self) -> list[str]:
        """List all available progress session IDs.

        Returns:
            List of session IDs
        """
        session_ids = []
        for file_path in self.progress_dir.glob("*.json"):
            if not file_path.name.endswith(".backup.json"):
                session_id = file_path.stem
                session_ids.append(session_id)

        logger.debug(f"Found {len(session_ids)} progress files")
        return sorted(session_ids)

    def exists(self, session_id: str) -> bool:
        """Check if progress file exists.

        Args:
            session_id: Session identifier

        Returns:
            True if progress file exists
        """
        return self._get_progress_file(session_id).exists()

    def calculate_statistics(
        self, card_progress: dict[str, CardProgress], session_start: datetime
    ) -> SessionStatistics:
        """Calculate session statistics from card progress.

        Args:
            card_progress: Dictionary of card progress
            session_start: Session start timestamp

        Returns:
            Calculated statistics
        """
        total_cards = len(card_progress)
        completed_cards = sum(1 for cp in card_progress.values() if cp.attempts > 0)

        total_attempts = sum(cp.attempts for cp in card_progress.values())
        correct_attempts = sum(cp.correct_count for cp in card_progress.values())
        incorrect_attempts = sum(cp.incorrect_count for cp in card_progress.values())

        # Calculate correct rate
        correct_rate = correct_attempts / total_attempts if total_attempts > 0 else 0.0

        # Calculate duration
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
        """Get aggregated statistics for all sessions of a deck.

        Args:
            deck_name: Deck name to summarize

        Returns:
            Dictionary with aggregated statistics
        """
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
        """Export complete session progress as JSON.

        Args:
            session_id: Session identifier

        Returns:
            Complete progress data
        """
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

    def _get_progress_file(self, session_id: str) -> Path:
        """Get progress file path for session.

        Args:
            session_id: Session identifier

        Returns:
            Path to progress file
        """
        return self.progress_dir / f"{session_id}.json"

    def _get_backup_file(self, session_id: str) -> Path:
        """Get backup file path for session.

        Args:
            session_id: Session identifier

        Returns:
            Path to backup file
        """
        return self.progress_dir / f"{session_id}.backup.json"
