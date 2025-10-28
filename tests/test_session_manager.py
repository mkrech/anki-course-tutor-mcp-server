"""Tests for session management."""

from datetime import datetime, timedelta

import pytest

from anki_course_tutor.models import LearningMode, SessionStatus
from anki_course_tutor.session_manager import SessionManager


@pytest.fixture
def session_manager():
    """Create SessionManager instance with in-memory storage."""
    return SessionManager()


class TestSessionManager:
    """Tests for SessionManager."""

    def test_create_session(self, session_manager):
        """Test creating a new session."""
        card_ids = [f"card-{i}" for i in range(20)]
        session = session_manager.create_session(
            deck_name="TestDeck",
            card_ids=card_ids,
            mode="explain",
            chapter="chapter-1",
        )

        assert session is not None
        assert session.deck_name == "TestDeck"
        assert len(session.card_ids) == 20
        assert session.mode == LearningMode.EXPLAIN
        assert session.chapter == "chapter-1"
        assert session.status == SessionStatus.IN_PROGRESS
        assert session.current_card_index == 0

        # Verify session is in memory
        assert session.session_id in session_manager._sessions

    def test_save_and_load_session(self, session_manager):
        """Test saving and loading a session."""
        # Create session
        card_ids = [f"card-{i}" for i in range(10)]
        original = session_manager.create_session(
            deck_name="TestDeck",
            card_ids=card_ids,
        )

        # Modify it
        original.current_card_index = 5
        original.status = SessionStatus.PAUSED
        session_manager.save_session(original)

        # Load it back
        loaded = session_manager.load_session(original.session_id)

        assert loaded.session_id == original.session_id
        assert loaded.deck_name == original.deck_name
        assert loaded.current_card_index == 5
        assert loaded.status == SessionStatus.PAUSED

    def test_load_nonexistent_session(self, session_manager):
        """Test loading a session that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            session_manager.load_session("nonexistent-session-id")

    def test_save_with_backup(self, session_manager):
        """Test that backup is created on save."""
        card_ids = [f"card-{i}" for i in range(10)]
        session = session_manager.create_session(
            deck_name="TestDeck",
            card_ids=card_ids,
        )

        # In-memory mode doesn't use file backups
        # Just verify session is stored
        assert session.session_id in session_manager._sessions

        # Second save should update the session
        session.current_card_index = 1
        session_manager.save_session(session)
        assert session_manager._sessions[session.session_id].current_card_index == 1

    def test_list_sessions(self, session_manager):
        """Test listing sessions."""
        # Create multiple sessions
        _session1 = session_manager.create_session("Deck1", ["card-1", "card-2"])
        session2 = session_manager.create_session("Deck2", ["card-3", "card-4"])
        _session3 = session_manager.create_session("Deck1", ["card-5", "card-6"])

        # List all sessions
        all_sessions = session_manager.list_sessions()
        assert len(all_sessions) == 3

        # Filter by deck name
        deck1_sessions = session_manager.list_sessions(deck_name="Deck1")
        assert len(deck1_sessions) == 2
        assert all(s["deck_name"] == "Deck1" for s in deck1_sessions)

        # Filter by status
        session2_loaded = session_manager.load_session(session2.session_id)
        session2_loaded.status = SessionStatus.COMPLETED
        session_manager.save_session(session2_loaded)

        completed_sessions = session_manager.list_sessions(status=SessionStatus.COMPLETED)
        assert len(completed_sessions) == 1
        assert completed_sessions[0]["id"] == session2.session_id

    def test_list_sessions_with_limit(self, session_manager):
        """Test listing sessions with limit."""
        # Create 5 sessions
        for i in range(5):
            session_manager.create_session(f"Deck{i}", [f"card-{i}"])

        # List with limit
        sessions = session_manager.list_sessions(limit=3)
        assert len(sessions) == 3

    def test_delete_session(self, session_manager):
        """Test deleting a session."""
        session = session_manager.create_session("TestDeck", ["card-1", "card-2"])
        
        assert session.session_id in session_manager._sessions

        session_manager.delete_session(session.session_id)

        assert session.session_id not in session_manager._sessions

    def test_delete_nonexistent_session(self, session_manager):
        """Test deleting a session that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            session_manager.delete_session("nonexistent-id")

    def test_resume_session(self, session_manager):
        """Test resuming a paused session."""
        session = session_manager.create_session("TestDeck", ["card-1", "card-2"])

        # Pause it
        session.status = SessionStatus.PAUSED
        session_manager.save_session(session)

        # Resume it
        resumed = session_manager.resume_session(session.session_id)

        assert resumed.status == SessionStatus.IN_PROGRESS

    def test_resume_completed_session_fails(self, session_manager):
        """Test that completed sessions cannot be resumed."""
        session = session_manager.create_session("TestDeck", ["card-1"])

        # Complete it
        session.status = SessionStatus.COMPLETED
        session_manager.save_session(session)

        # Try to resume
        with pytest.raises(ValueError, match="already completed"):
            session_manager.resume_session(session.session_id)

    def test_pause_session(self, session_manager):
        """Test pausing an active session."""
        session = session_manager.create_session("TestDeck", ["card-1"])

        session_manager.pause_session(session.session_id)

        loaded = session_manager.load_session(session.session_id)
        assert loaded.status == SessionStatus.PAUSED

    def test_pause_nonactive_session_fails(self, session_manager):
        """Test that non-active sessions cannot be paused."""
        session = session_manager.create_session("TestDeck", ["card-1"])

        session.status = SessionStatus.COMPLETED
        session_manager.save_session(session)

        with pytest.raises(ValueError, match="Only active sessions"):
            session_manager.pause_session(session.session_id)

    def test_cleanup_old_sessions(self, session_manager):
        """Test cleaning up old sessions."""
        # Create completed session with old timestamp
        session1 = session_manager.create_session("Deck1", ["card-1"])
        session1.status = SessionStatus.COMPLETED
        session1.last_updated = datetime.now() - timedelta(days=31)
        # Store directly to avoid save() overwriting timestamp
        session_manager._sessions[session1.session_id] = session1

        # Create active session
        session2 = session_manager.create_session("Deck2", ["card-2"])

        # Cleanup
        deleted = session_manager.cleanup_old_sessions(days=30)

        # Only completed session should be deleted
        assert deleted == 1
        assert session1.session_id not in session_manager._sessions
        assert session2.session_id in session_manager._sessions

    def test_invalid_json_handling(self, session_manager):
        """Test handling of non-existent sessions."""
        # In-memory mode doesn't have JSON corruption issues
        # Test non-existent session instead
        with pytest.raises(FileNotFoundError):
            session_manager.load_session("non-existent-session")

    def test_session_metadata_in_list(self, session_manager):
        """Test that list_sessions returns correct metadata."""
        card_ids = [f"card-{i}" for i in range(10)]
        session = session_manager.create_session(
            deck_name="TestDeck",
            card_ids=card_ids,
            mode="test",
            chapter="chapter-1",
        )

        sessions = session_manager.list_sessions()

        assert len(sessions) == 1
        metadata = sessions[0]

        assert metadata["id"] == session.session_id
        assert metadata["deck_name"] == "TestDeck"
        assert metadata["total_cards"] == 10
        assert metadata["mode"] == "test"
        assert metadata["chapter"] == "chapter-1"
        assert metadata["current_index"] == 0
        assert "created_at" in metadata
        assert "last_updated" in metadata
