"""Tests for progress tracking."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from anki_course_tutor.models.progress import Progress, SessionStatistics
from anki_course_tutor.models.session import CardProgress
from anki_course_tutor.progress_tracker import ProgressTracker


@pytest.fixture
def temp_progress_dir():
    """Create temporary directory for progress files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


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

    def test_initialization(self, temp_progress_dir):
        """Test tracker initialization."""
        tracker = ProgressTracker(temp_progress_dir)
        assert tracker.progress_dir == temp_progress_dir
        assert tracker.progress_dir.exists()

    def test_save_and_load(self, temp_progress_dir, sample_progress, sample_card_progress):
        """Test saving and loading progress."""
        tracker = ProgressTracker(temp_progress_dir)

        # Save
        tracker.save(sample_progress, sample_card_progress)

        # Verify file exists
        assert tracker.exists("test-session-1")

        # Load
        loaded_progress, loaded_cards = tracker.load("test-session-1")

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

    def test_atomic_write_with_backup(
        self, temp_progress_dir, sample_progress, sample_card_progress
    ):
        """Test atomic write creates backup."""
        tracker = ProgressTracker(temp_progress_dir)

        # First save
        tracker.save(sample_progress, sample_card_progress)
        file_path = tracker._get_progress_file("test-session-1")
        backup_path = tracker._get_backup_file("test-session-1")

        # Backup should not exist yet
        assert not backup_path.exists()

        # Second save should create backup
        sample_progress.statistics.completed_cards = 3
        tracker.save(sample_progress, sample_card_progress)

        # Backup should now exist
        assert backup_path.exists()

        # Verify backup contains old data
        with open(backup_path) as f:
            backup_data = json.load(f)
        assert backup_data["statistics"]["completed_cards"] == 2  # Old value

        # Main file has new data
        with open(file_path) as f:
            main_data = json.load(f)
        assert main_data["statistics"]["completed_cards"] == 3  # New value

    def test_load_from_backup_on_corruption(
        self, temp_progress_dir, sample_progress, sample_card_progress
    ):
        """Test loading from backup when main file is corrupted."""
        tracker = ProgressTracker(temp_progress_dir)

        # Save twice to create backup
        tracker.save(sample_progress, sample_card_progress)
        sample_progress.statistics.completed_cards = 3
        tracker.save(sample_progress, sample_card_progress)

        # Corrupt main file
        file_path = tracker._get_progress_file("test-session-1")
        with open(file_path, "w") as f:
            f.write("CORRUPTED DATA {{{")

        # Load should use backup
        loaded_progress, _ = tracker.load("test-session-1")
        assert loaded_progress.session_id == "test-session-1"

        # Main file should be restored from backup
        assert file_path.exists()

    def test_load_nonexistent_file(self, temp_progress_dir):
        """Test loading nonexistent file raises error."""
        tracker = ProgressTracker(temp_progress_dir)

        with pytest.raises(FileNotFoundError):
            tracker.load("nonexistent-session")

    def test_validation_missing_required_field(self, temp_progress_dir):
        """Test validation fails with missing required fields."""
        tracker = ProgressTracker(temp_progress_dir)
        file_path = tracker._get_progress_file("invalid-session")

        # Create invalid JSON (missing session_id)
        with open(file_path, "w") as f:
            json.dump({"deck_name": "TestDeck"}, f)

        # Should raise FileNotFoundError since validation fails and no backup exists
        with pytest.raises(FileNotFoundError):
            tracker.load("invalid-session")

    def test_validation_missing_optional_fields(
        self, temp_progress_dir, sample_progress, sample_card_progress
    ):
        """Test validation handles missing optional fields gracefully."""
        tracker = ProgressTracker(temp_progress_dir)
        file_path = tracker._get_progress_file("test-session-1")

        # Create minimal valid JSON
        minimal_data = {
            "session_id": "test-session-1",
            "deck_name": "TestDeck",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
        }
        with open(file_path, "w") as f:
            json.dump(minimal_data, f)

        # Should load with defaults
        progress, cards = tracker.load("test-session-1")
        assert progress.session_id == "test-session-1"
        assert len(cards) == 0  # No cards
        assert progress.statistics.total_cards == 0

    def test_delete_progress(self, temp_progress_dir, sample_progress, sample_card_progress):
        """Test deleting progress files."""
        tracker = ProgressTracker(temp_progress_dir)

        # Save to create files
        tracker.save(sample_progress, sample_card_progress)
        sample_progress.statistics.completed_cards = 3
        tracker.save(sample_progress, sample_card_progress)  # Create backup

        # Verify files exist
        assert tracker.exists("test-session-1")
        assert tracker._get_backup_file("test-session-1").exists()

        # Delete
        tracker.delete("test-session-1")

        # Verify files deleted
        assert not tracker.exists("test-session-1")
        assert not tracker._get_backup_file("test-session-1").exists()

    def test_list_progress_files(self, temp_progress_dir, sample_progress, sample_card_progress):
        """Test listing progress files."""
        tracker = ProgressTracker(temp_progress_dir)

        # Create multiple sessions
        for i in range(3):
            sample_progress.session_id = f"session-{i}"
            tracker.save(sample_progress, sample_card_progress)

        # List
        session_ids = tracker.list_progress_files()
        assert len(session_ids) == 3
        assert "session-0" in session_ids
        assert "session-1" in session_ids
        assert "session-2" in session_ids

        # Should not include backup files
        assert not any(".backup" in sid for sid in session_ids)

    def test_calculate_statistics(self, temp_progress_dir, sample_card_progress):
        """Test statistics calculation."""
        tracker = ProgressTracker(temp_progress_dir)
        session_start = datetime.now() - timedelta(minutes=10)

        stats = tracker.calculate_statistics(sample_card_progress, session_start)

        assert stats.total_cards == 3
        assert stats.completed_cards == 3  # All have attempts
        assert stats.total_attempts == 4  # 2 + 1 + 1
        assert stats.correct_attempts == 3  # 2 + 1 + 0
        assert stats.incorrect_attempts == 1  # 0 + 0 + 1
        assert stats.correct_rate == 0.75  # 3/4
        assert stats.session_duration_seconds >= 590  # ~10 minutes

    def test_calculate_statistics_no_attempts(self, temp_progress_dir):
        """Test statistics with no attempts."""
        tracker = ProgressTracker(temp_progress_dir)
        card_progress = {
            "card-1": CardProgress(card_id="card-1", attempts=0),
        }
        session_start = datetime.now()

        stats = tracker.calculate_statistics(card_progress, session_start)

        assert stats.total_cards == 1
        assert stats.completed_cards == 0
        assert stats.total_attempts == 0
        assert stats.correct_rate == 0.0  # No division by zero

    def test_get_deck_summary(self, temp_progress_dir, sample_progress, sample_card_progress):
        """Test aggregated deck statistics."""
        tracker = ProgressTracker(temp_progress_dir)

        # Create multiple sessions for same deck
        for i in range(3):
            sample_progress.session_id = f"session-{i}"
            sample_progress.deck_name = "TestDeck"
            sample_progress.statistics.total_attempts = 10
            sample_progress.statistics.correct_attempts = 8
            tracker.save(sample_progress, sample_card_progress)

        # Get summary
        summary = tracker.get_deck_summary("TestDeck")

        assert summary["deck_name"] == "TestDeck"
        assert summary["total_sessions"] == 3
        assert summary["total_cards_studied"] == 3  # Unique cards
        assert summary["total_attempts"] == 30  # 10 * 3
        assert summary["total_correct"] == 24  # 8 * 3
        assert summary["average_correct_rate"] == 0.8  # 24/30

    def test_get_deck_summary_empty(self, temp_progress_dir):
        """Test deck summary with no sessions."""
        tracker = ProgressTracker(temp_progress_dir)

        summary = tracker.get_deck_summary("NonexistentDeck")

        assert summary["total_sessions"] == 0
        assert summary["total_cards_studied"] == 0
        assert summary["average_correct_rate"] == 0.0

    def test_export_session(self, temp_progress_dir, sample_progress, sample_card_progress):
        """Test exporting session data."""
        tracker = ProgressTracker(temp_progress_dir)
        tracker.save(sample_progress, sample_card_progress)

        # Export
        export_data = tracker.export_session("test-session-1")

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

    def test_card_status_tracking(self, temp_progress_dir):
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

        tracker = ProgressTracker(temp_progress_dir)
        progress = Progress(session_id="test-status", deck_name="TestDeck")
        tracker.save(progress, card_progress)

        # Load and verify
        _, loaded_cards = tracker.load("test-status")
        assert loaded_cards["card-new"].status == "new"
        assert loaded_cards["card-learning"].status == "learning"
        assert loaded_cards["card-mastered"].status == "mastered"

    def test_timestamp_persistence(self, temp_progress_dir, sample_card_progress):
        """Test that timestamps are preserved across save/load."""
        tracker = ProgressTracker(temp_progress_dir)
        progress = Progress(session_id="test-timestamp", deck_name="TestDeck")

        original_time = sample_card_progress["card-1"].last_attempt
        tracker.save(progress, sample_card_progress)

        # Load and compare
        _, loaded_cards = tracker.load("test-timestamp")
        loaded_time = loaded_cards["card-1"].last_attempt

        # Should be equal (within microsecond precision)
        assert abs((loaded_time - original_time).total_seconds()) < 0.001

    def test_multiple_deck_summary(self, temp_progress_dir, sample_progress, sample_card_progress):
        """Test deck summary filters by deck name."""
        tracker = ProgressTracker(temp_progress_dir)

        # Create sessions for different decks
        sample_progress.session_id = "session-deck-a"
        sample_progress.deck_name = "DeckA"
        tracker.save(sample_progress, sample_card_progress)

        sample_progress.session_id = "session-deck-b"
        sample_progress.deck_name = "DeckB"
        tracker.save(sample_progress, sample_card_progress)

        # Get summary for DeckA only
        summary_a = tracker.get_deck_summary("DeckA")
        assert summary_a["total_sessions"] == 1
        assert summary_a["deck_name"] == "DeckA"

        # Get summary for DeckB only
        summary_b = tracker.get_deck_summary("DeckB")
        assert summary_b["total_sessions"] == 1
        assert summary_b["deck_name"] == "DeckB"
