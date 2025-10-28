"""Session management - create, load, and manage learning sessions in memory."""

import logging
from datetime import datetime
from typing import Any

from anki_course_tutor.models import LearningMode, Session, SessionStatus

logger = logging.getLogger(__name__)


class SessionManager:
    """Manage learning session lifecycle in memory (no persistence)."""

    def __init__(self):
        """Initialize session manager with in-memory storage."""
        self._sessions: dict[str, Session] = {}
        logger.info("SessionManager initialized (in-memory mode)")

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

        # Store in memory
        self._sessions[session_id] = session

        return session

    def save_session(self, session: Session) -> None:
        """Save session to memory.

        Args:
            session: Session to save
        """
        # Update last_updated timestamp
        session.last_updated = datetime.now()
        
        # Store in memory
        self._sessions[session.session_id] = session
        logger.debug(f"Saved session {session.session_id} to memory")

    def load_session(self, session_id: str) -> Session:
        """Load session from memory.

        Args:
            session_id: ID of session to load

        Returns:
            Loaded Session object

        Raises:
            FileNotFoundError: If session not found
        """
        if session_id not in self._sessions:
            raise FileNotFoundError(f"Session {session_id} not found")

        session = self._sessions[session_id]
        logger.debug(f"Loaded session {session_id} from memory")
        return session

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

        # Sort by last_updated (most recent first)
        sorted_sessions = sorted(
            self._sessions.values(),
            key=lambda s: s.last_updated,
            reverse=True,
        )

        for session in sorted_sessions:
            # Apply filters
            if deck_name and session.deck_name != deck_name:
                continue

            if status and session.status != status:
                continue

            # Add metadata
            metadata = {
                "id": session.session_id,
                "deck_name": session.deck_name,
                "status": session.status.value,
                "mode": session.mode.value,
                "chapter": session.chapter,
                "current_index": session.current_card_index,
                "total_cards": len(session.card_ids),
                "created_at": session.created_at.isoformat(),
                "last_updated": session.last_updated.isoformat(),
            }

            sessions.append(metadata)

            if len(sessions) >= limit:
                break

        logger.info(
            f"Found {len(sessions)} sessions"
            + (f" for deck '{deck_name}'" if deck_name else "")
            + (f" with status {status.value}" if status else "")
        )

        return sessions

    def delete_session(self, session_id: str) -> None:
        """Delete a session from memory.

        Args:
            session_id: ID of session to delete

        Raises:
            FileNotFoundError: If session not found
        """
        if session_id not in self._sessions:
            raise FileNotFoundError(f"Session {session_id} not found")

        del self._sessions[session_id]
        logger.info(f"Deleted session {session_id}")

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

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Clean up old completed sessions from memory.

        Args:
            days: Age threshold in days (for in-memory, we just clean completed ones)

        Returns:
            Number of sessions deleted
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=days)
        to_delete = []

        for session_id, session in self._sessions.items():
            # Only delete completed sessions older than cutoff
            if session.status == SessionStatus.COMPLETED and session.last_updated < cutoff:
                to_delete.append(session_id)

        for session_id in to_delete:
            del self._sessions[session_id]
            logger.debug(f"Cleaned up old session {session_id}")

        if to_delete:
            logger.info(f"Cleaned up {len(to_delete)} old sessions")

        return len(to_delete)
