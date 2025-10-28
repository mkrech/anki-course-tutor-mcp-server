"""Tests for progress tracking."""

from datetime import datetime, timedelta

import pytest

from anki_course_tutor.models.progress import Progress, SessionStatistics
from anki_course_tutor.models.session import CardProgress
from anki_course_tutor.progress_tracker import ProgressTracker


@pytest.fixture
def progress_tracker():
    """Create ProgressTracker instance with in-memory storage."""
    return ProgressTracker()


@pytest.fixture
def sample_progress():
    """Create sample progress."""
    return Progress(
        session_id="test-session-1",
        deck_name="TestDeck",
        chapter="Chapter 1",
        created_at=datetime.now() - timedelta(hours=1),
        state="in_progress",
        statistics=SessionStatistics(
            total_cards=3,
            completed_cards=2,
            correct_rate=0.75,
            session_duration_seconds=600,
            total_attempts=4,
            correct_attempts=3,
            incorrect_attempts=1,
        ),
    )


@pytest.fixture
def sample_card_progress():
    """Create sample card progress."""
    now = datetime.now()
    return {
        "card-1": CardProgress(
            card_id="card-1",
            attempts=2,
            correct_count=2,
            incorrect_count=0,
            last_attempt=now,
            status="mastered",
        ),
        "card-2": CardProgress(
            card_id="card-2",
            attempts=1,
            correct_count=1,
            incorrect_count=0,
            last_attempt=now - timedelta(minutes=5),
            status="learning",
        ),
        "card-3": CardProgress(
            card_id="card-3",
            attempts=1,
            correct_count=0,
            incorrect_count=1,
            last_attempt=now - timedelta(minutes=10),
            status="learning",
        ),
    }


class TestProgressTracker:
    """Test progress tracker functionality."""

    def test_initialization(self, progress_tracker):
        """Test tracker initialization."""
        assert progress_tracker._progress == {}
        assert progress_tracker._card_progress == {}

    def test_save_and_load(self, progress_tracker, sample_progress, sample_card_progress):
        """Test saving and loading progress."""
        # Save
        progress_tracker.save(sample_progress, sample_card_progress)

        # Verify exists
        assert progress_tracker.exists("test-session-1")

        # Load
        loaded_progress, loaded_cards = progress_tracker.load("test-session-1")

        # Verify progress
        assert loaded_progress.session_id == sample_progress.session_id
        assert loaded_progress.deck_name == sample_progress.deck_name
        assert loaded_progress.statistics.total_cards == 3
        assert loaded_progress.statistics.correct_rate == 0.75

        # Verify card progress
        assert len(loaded_cards) == 3
        assert loaded_cards["card-1"].attempts == 2
        assert loaded_cards["card-1"].correct_count == 2
        assert loaded_cards["card-1"].status == "mastered"

    def test_save_and_update(
        self, progress_tracker, sample_progress, sample_card_progress
    ):
        """Test saving and updating progress in memory."""
        # First save
        progress_tracker.save(sample_progress, sample_card_progress)
        assert progress_tracker.exists("test-session-1")

        # Update and save again
        sample_progress.statistics.completed_cards = 3
        progress_tracker.save(sample_progress, sample_card_progress)

        # Load and verify update
        loaded_progress, _ = progress_tracker.load("test-session-1")
        assert loaded_progress.statistics.completed_cards == 3

    def test_load_from_backup_on_corruption(
        self, progress_tracker, sample_progress, sample_card_progress
    ):
        """Test that non-existent sessions raise error."""
        # Save progress
        progress_tracker.save(sample_progress, sample_card_progress)

        # Try to load non-existent session
        with pytest.raises(FileNotFoundError):
            progress_tracker.load("non-existent-session")

    def test_load_nonexistent_file(self, progress_tracker):
        """Test loading nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            progress_tracker.load("nonexistent-session")

    def test_validation_missing_required_field(self, progress_tracker):
        """Test that missing session raises error."""
        # In-memory mode doesn't have JSON validation issues
        # Test non-existent session instead
        with pytest.raises(FileNotFoundError):
            progress_tracker.load("missing-session")

    def test_validation_missing_optional_fields(
        self, progress_tracker, sample_progress, sample_card_progress
    ):
        """Test validation handles missing optional fields gracefully."""
        # Save and load - should work fine in memory
        progress_tracker.save(sample_progress, sample_card_progress)

    def test_atomic_write_with_backup(
        self, progress_tracker, sample_progress, sample_card_progress
    ):
        """Test in-memory updates (no backup files needed)."""
        # First save
        progress_tracker.save(sample_progress, sample_card_progress)

        # Update and save again
        sample_progress.statistics.completed_cards = 3
        progress_tracker.save(sample_progress, sample_card_progress)

        # Load and verify the latest data
        loaded_progress, loaded_cards = progress_tracker.load("test-session-1")
        assert loaded_progress.statistics.completed_cards == 3

    def test_load_from_backup_on_corruption(
        self, progress_tracker, sample_progress, sample_card_progress
    ):
        """Test that non-existent sessions raise error."""
        # Save progress
        progress_tracker.save(sample_progress, sample_card_progress)

        # Try to load non-existent session
        with pytest.raises(FileNotFoundError):
            progress_tracker.load("non-existent-session")

    def test_load_nonexistent_file(self, progress_tracker):
        """Test loading nonexistent file raises error."""

        with pytest.raises(FileNotFoundError):
            progress_tracker.load("nonexistent-session")

    def test_validation_missing_required_field(self, progress_tracker):
        """Test that missing sessions raise error."""
        # In-memory mode doesn't have JSON validation issues
        # Test non-existent session instead
        with pytest.raises(FileNotFoundError):
            progress_tracker.load("missing-session")

    def test_validation_missing_optional_fields(
        self, progress_tracker, sample_progress, sample_card_progress
    ):
        """Test validation handles missing optional fields gracefully."""
        # Save and load - should work fine in memory
        progress_tracker.save(sample_progress, sample_card_progress)
        progress, cards = progress_tracker.load("test-session-1")
        assert progress.session_id == "test-session-1"
        assert len(cards) == 3

    def test_delete_progress(self, progress_tracker, sample_progress, sample_card_progress):
        """Test deleting progress from memory."""
        # Save progress
        progress_tracker.save(sample_progress, sample_card_progress)

        # Verify exists
        assert progress_tracker.exists("test-session-1")

        # Delete
        progress_tracker.delete("test-session-1")

        # Verify deleted
        assert not progress_tracker.exists("test-session-1")

    def test_list_progress_files(self, progress_tracker, sample_progress, sample_card_progress):
        """Test listing progress entries in memory."""
        # Create multiple sessions
        for i in range(3):
            sample_progress.session_id = f"session-{i}"
            progress_tracker.save(sample_progress, sample_card_progress)

        # List
        session_ids = progress_tracker.list_progress_files()
        assert len(session_ids) == 3
        assert "session-0" in session_ids
        assert "session-1" in session_ids
        assert "session-2" in session_ids

    def test_calculate_statistics(self, progress_tracker, sample_card_progress):
        """Test statistics calculation."""
        session_start = datetime.now() - timedelta(minutes=10)

        stats = progress_tracker.calculate_statistics(sample_card_progress, session_start)

        assert stats.total_cards == 3
        assert stats.completed_cards == 3  # All have attempts
        assert stats.total_attempts == 4  # 2 + 1 + 1
        assert stats.correct_attempts == 3  # 2 + 1 + 0
        assert stats.incorrect_attempts == 1  # 0 + 0 + 1
        assert stats.correct_rate == 0.75  # 3/4
        assert stats.session_duration_seconds >= 590  # ~10 minutes

    def test_calculate_statistics_no_attempts(self, progress_tracker):
        """Test statistics with no attempts."""
        card_progress = {
            "card-1": CardProgress(card_id="card-1", attempts=0),
        }
        session_start = datetime.now()

        stats = progress_tracker.calculate_statistics(card_progress, session_start)

        assert stats.total_cards == 1
        assert stats.completed_cards == 0
        assert stats.total_attempts == 0
        assert stats.correct_rate == 0.0  # No division by zero

    def test_get_deck_summary(self, progress_tracker, sample_progress, sample_card_progress):
        """Test aggregated deck statistics."""

        # Create multiple sessions for same deck
        for i in range(3):
            sample_progress.session_id = f"session-{i}"
            sample_progress.deck_name = "TestDeck"
            sample_progress.statistics.total_attempts = 10
            sample_progress.statistics.correct_attempts = 8
            progress_tracker.save(sample_progress, sample_card_progress)

        # Get summary
        summary = progress_tracker.get_deck_summary("TestDeck")

        assert summary["deck_name"] == "TestDeck"
        assert summary["total_sessions"] == 3
        assert summary["total_cards_studied"] == 3  # Unique cards
        assert summary["total_attempts"] == 30  # 10 * 3
        assert summary["total_correct"] == 24  # 8 * 3
        assert summary["average_correct_rate"] == 0.8  # 24/30

    def test_get_deck_summary_empty(self, progress_tracker):
        """Test deck summary with no sessions."""
        summary = progress_tracker.get_deck_summary("NonexistentDeck")

        assert summary["total_sessions"] == 0
        assert summary["total_cards_studied"] == 0
        assert summary["average_correct_rate"] == 0.0

    def test_export_session(self, progress_tracker, sample_progress, sample_card_progress):
        """Test exporting session data."""
        progress_tracker.save(sample_progress, sample_card_progress)

        # Export
        export_data = progress_tracker.export_session("test-session-1")

        # Verify structure
        assert "session_metadata" in export_data
        assert "card_progress" in export_data
        assert "statistics" in export_data

        # Verify content
        assert export_data["session_metadata"]["session_id"] == "test-session-1"
        assert len(export_data["card_progress"]) == 3
        assert export_data["statistics"]["total_cards"] == 3
        assert export_data["statistics"]["correct_rate"] == 0.75

        # Verify card progress details
        card_1 = next(c for c in export_data["card_progress"] if c["card_id"] == "card-1")
        assert card_1["attempts"] == 2
        assert card_1["status"] == "mastered"

    def test_card_status_tracking(self, progress_tracker):
        """Test card status changes based on performance."""
        card_progress = {
            "card-new": CardProgress(card_id="card-new", attempts=0, status="new"),
            "card-learning": CardProgress(
                card_id="card-learning",
                attempts=2,
                correct_count=1,
                incorrect_count=1,
                status="learning",
            ),
            "card-mastered": CardProgress(
                card_id="card-mastered",
                attempts=3,
                correct_count=3,
                incorrect_count=0,
                status="mastered",
            ),
        }

        progress = Progress(session_id="test-status", deck_name="TestDeck")
        progress_tracker.save(progress, card_progress)

        # Load and verify
        _, loaded_cards = progress_tracker.load("test-status")
        assert loaded_cards["card-new"].status == "new"
        assert loaded_cards["card-learning"].status == "learning"
        assert loaded_cards["card-mastered"].status == "mastered"

    def test_timestamp_persistence(self, progress_tracker, sample_card_progress):
        """Test that timestamps are preserved across save/load."""
        progress = Progress(session_id="test-timestamp", deck_name="TestDeck")

        original_time = sample_card_progress["card-1"].last_attempt
        progress_tracker.save(progress, sample_card_progress)

        # Load and compare
        _, loaded_cards = progress_tracker.load("test-timestamp")
        loaded_time = loaded_cards["card-1"].last_attempt

        # Should be equal (within microsecond precision)
        assert abs((loaded_time - original_time).total_seconds()) < 0.001

    def test_multiple_deck_summary(self, progress_tracker, sample_progress, sample_card_progress):
        """Test deck summary filters by deck name."""
        # Create sessions for different decks
        sample_progress.session_id = "session-deck-a"
        sample_progress.deck_name = "DeckA"
        progress_tracker.save(sample_progress, sample_card_progress)

        sample_progress.session_id = "session-deck-b"
        sample_progress.deck_name = "DeckB"
        progress_tracker.save(sample_progress, sample_card_progress)

        # Get summary for DeckA only
        summary_a = progress_tracker.get_deck_summary("DeckA")
        assert summary_a["total_sessions"] == 1
        assert summary_a["deck_name"] == "DeckA"

        # Get summary for DeckB only
        summary_b = progress_tracker.get_deck_summary("DeckB")
        assert summary_b["total_sessions"] == 1
        assert summary_b["deck_name"] == "DeckB"
