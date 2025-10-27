"""Session management - create, load, save, and list learning sessions."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from anki_course_tutor.config import StorageConfig
from anki_course_tutor.models import LearningMode, Session, SessionStatus

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage learning session lifecycle and persistence."""

    def __init__(self, config: StorageConfig):
        """Initialize session manager with storage configuration.

        Args:
            config: Storage configuration with session directory path
        """
        self.config = config
        self.session_dir = Path(config.sessions_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def create_session(
        self,
        deck_name: str,
        card_ids: list[str],
        mode: str = "explain",
        chapter: str = "",
    ) -> Session:
        """Create a new learning session.

        Args:
            deck_name: Name of the Anki deck
            card_ids: List of card IDs in the session
            mode: Learning mode (explain or test)
            chapter: Optional chapter filter

        Returns:
            New Session object
        """
        # Generate unique session ID
        import uuid

        session_id = str(uuid.uuid4())

        # Convert mode string to enum
        learning_mode = LearningMode.EXPLAIN if mode == "explain" else LearningMode.TEST

        session = Session(
            session_id=session_id,
            deck_name=deck_name,
            card_ids=card_ids,
            mode=learning_mode,
            chapter=chapter,
            status=SessionStatus.IN_PROGRESS,
        )

        logger.info(
            f"Created session {session.session_id} for deck '{deck_name}' "
            f"with {len(card_ids)} cards (mode: {mode})"
        )

        # Save immediately
        self.save_session(session)

        return session

    def save_session(self, session: Session) -> None:
        """Save session to JSON file.

        Args:
            session: Session to save

        Raises:
            IOError: If save fails
        """
        session_file = self._get_session_file(session.session_id)

        try:
            # Update last_updated timestamp
            session.last_updated = datetime.now()

            # Convert to dict
            session_dict = session.to_dict()

            # Atomic write with backup
            if session_file.exists() and self.config.backup_enabled:
                backup_file = session_file.with_suffix(".json.bak")
                session_file.rename(backup_file)

            # Write new file
            with open(session_file, "w", encoding="utf-8") as f:
                json.dump(session_dict, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved session {session.session_id} to {session_file}")

        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")
            # Restore from backup if available
            if self.config.backup_enabled:
                backup_file = session_file.with_suffix(".json.bak")
                if backup_file.exists():
                    backup_file.rename(session_file)
                    logger.info("Restored session from backup")
            raise OSError(f"Failed to save session: {e}") from e

    def load_session(self, session_id: str) -> Session:
        """Load session from JSON file.

        Args:
            session_id: ID of session to load

        Returns:
            Loaded Session object

        Raises:
            FileNotFoundError: If session file not found
            ValueError: If session data is invalid
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            raise FileNotFoundError(f"Session {session_id} not found")

        try:
            with open(session_file, encoding="utf-8") as f:
                session_dict = json.load(f)

            session = Session.from_dict(session_dict)
            logger.debug(f"Loaded session {session_id}")
            return session

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in session {session_id}: {e}")
            raise ValueError(f"Invalid session data: {e}") from e
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            raise

    def list_sessions(
        self,
        deck_name: str | None = None,
        status: SessionStatus | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List sessions with optional filtering.

        Args:
            deck_name: Filter by deck name (optional)
            status: Filter by status (optional)
            limit: Maximum number of sessions to return

        Returns:
            List of session metadata dictionaries
        """
        sessions = []

        for session_file in sorted(
            self.session_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            if session_file.suffix == ".bak":
                continue

            try:
                with open(session_file, encoding="utf-8") as f:
                    session_dict = json.load(f)

                # Apply filters
                if deck_name and session_dict.get("deck_name") != deck_name:
                    continue

                if status and session_dict.get("status") != status.value:
                    continue

                # Add metadata
                metadata = {
                    "id": session_dict["session_id"],
                    "deck_name": session_dict["deck_name"],
                    "status": session_dict["status"],
                    "mode": session_dict["mode"],
                    "chapter": session_dict.get("chapter", ""),
                    "current_index": session_dict["current_card_index"],
                    "total_cards": len(session_dict["card_ids"]),
                    "created_at": session_dict["created_at"],
                    "last_updated": session_dict["last_updated"],
                }

                sessions.append(metadata)

                if len(sessions) >= limit:
                    break

            except Exception as e:
                logger.warning(f"Failed to read session {session_file.name}: {e}")
                continue

        logger.info(
            f"Found {len(sessions)} sessions"
            + (f" for deck '{deck_name}'" if deck_name else "")
            + (f" with status {status.value}" if status else "")
        )

        return sessions

    def delete_session(self, session_id: str) -> None:
        """Delete a session file.

        Args:
            session_id: ID of session to delete

        Raises:
            FileNotFoundError: If session file not found
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            raise FileNotFoundError(f"Session {session_id} not found")

        try:
            session_file.unlink()
            logger.info(f"Deleted session {session_id}")

            # Also delete backup if exists
            backup_file = session_file.with_suffix(".json.bak")
            if backup_file.exists():
                backup_file.unlink()

        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise

    def resume_session(self, session_id: str) -> Session:
        """Resume a session and validate it can continue.

        Args:
            session_id: ID of session to resume

        Returns:
            Loaded Session object

        Raises:
            ValueError: If session cannot be resumed
        """
        session = self.load_session(session_id)

        # Check if session can be resumed
        if session.status == SessionStatus.COMPLETED:
            raise ValueError(f"Session {session_id} is already completed")

        # Update status to IN_PROGRESS if it was PAUSED
        if session.status == SessionStatus.PAUSED:
            session.status = SessionStatus.IN_PROGRESS
            self.save_session(session)

        logger.info(
            f"Resumed session {session_id} (card {session.current_card_index + 1}/"
            f"{len(session.card_ids)})"
        )

        return session

    def pause_session(self, session_id: str) -> None:
        """Pause an active session.

        Args:
            session_id: ID of session to pause

        Raises:
            ValueError: If session cannot be paused
        """
        session = self.load_session(session_id)

        if session.status != SessionStatus.IN_PROGRESS:
            raise ValueError("Only active sessions can be paused")

        session.status = SessionStatus.PAUSED
        self.save_session(session)

        logger.info(f"Paused session {session_id}")

    def _get_session_file(self, session_id: str) -> Path:
        """Get path to session file.

        Args:
            session_id: Session ID

        Returns:
            Path to session file
        """
        return self.session_dir / f"{session_id}.json"

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Delete sessions older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of sessions deleted
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for session_file in self.session_dir.glob("*.json"):
            if session_file.suffix == ".bak":
                continue

            try:
                # Check file modification time
                mtime = datetime.fromtimestamp(session_file.stat().st_mtime)

                if mtime < cutoff:
                    # Load to check status
                    with open(session_file, encoding="utf-8") as f:
                        session_dict = json.load(f)

                    # Only delete completed sessions
                    status = session_dict.get("status")
                    if status == SessionStatus.COMPLETED.value:
                        session_file.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted old session {session_file.stem}")

            except Exception as e:
                logger.warning(f"Failed to process session {session_file.name}: {e}")
                continue

        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old sessions")

        return deleted_count
