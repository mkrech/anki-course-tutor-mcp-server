"""Tests for Anki integration."""

from unittest.mock import AsyncMock, patch

import pytest

from anki_course_tutor.anki_client import AnkiDeckImporter, CardConverter
from anki_course_tutor.config import AnkiConfig
from anki_course_tutor.models import Card, CardType


class TestCardConverter:
    """Tests for CardConverter."""

    def test_convert_basic_card(self):
        """Test converting Basic note to Card."""
        note = {
            "noteId": 123,
            "modelName": "Basic",
            "fields": {
                "Front": {"value": "What is Python?"},
                "Back": {"value": "A programming language"},
            },
            "tags": ["chapter-1", "programming"],
            "deckName": "Programming",
        }

        card = CardConverter.from_anki_note(note)

        assert card is not None
        assert card.id == "123"
        assert card.type == CardType.BASIC
        assert card.question == "What is Python?"
        assert card.answer == "A programming language"
        assert card.deck == "Programming"
        assert card.chapter == "chapter-1"
        assert "programming" in card.tags

    def test_convert_basic_with_html(self):
        """Test HTML cleaning in Basic cards."""
        note = {
            "noteId": 124,
            "modelName": "Basic",
            "fields": {
                "Front": {"value": "<b>Bold question</b>"},
                "Back": {"value": "<i>Italic answer</i>&nbsp;"},
            },
            "tags": [],
            "deckName": "Test",
        }

        card = CardConverter.from_anki_note(note)

        assert card is not None
        assert card.question == "Bold question"
        assert card.answer == "Italic answer"

    def test_convert_cloze_card(self):
        """Test converting Cloze note to Card."""
        note = {
            "noteId": 125,
            "modelName": "Cloze",
            "fields": {
                "Text": {"value": "Python was created by {{c1::Guido van Rossum}}"},
            },
            "tags": ["chapter-2"],
            "deckName": "History",
        }

        card = CardConverter.from_anki_note(note)

        assert card is not None
        assert card.id == "125"
        assert card.type == CardType.CLOZE
        assert "[...]" in card.question
        assert card.answer == "Guido van Rossum"
        assert card.cloze_text is not None

    def test_convert_multiple_choice_card(self):
        """Test converting Multiple Choice note to Card."""
        note = {
            "noteId": 126,
            "modelName": "Multiple Choice",
            "fields": {
                "Question": {"value": "What is 2+2?"},
                "Option1": {"value": "3"},
                "Option2": {"value": "4"},
                "Option3": {"value": "5"},
                "Option4": {"value": "6"},
                "Answer": {"value": "4"},
            },
            "tags": ["chapter-3", "math"],
            "deckName": "Math",
        }

        card = CardConverter.from_anki_note(note)

        assert card is not None
        assert card.id == "126"
        assert card.type == CardType.MULTIPLE_CHOICE
        assert card.question == "What is 2+2?"
        assert card.answer == "4"
        assert card.options == ["3", "4", "5", "6"]

    def test_convert_unknown_model_fallback(self):
        """Test fallback to Basic for unknown models."""
        note = {
            "noteId": 127,
            "modelName": "CustomModel",
            "fields": {
                "Front": {"value": "Question"},
                "Back": {"value": "Answer"},
            },
            "tags": [],
            "deckName": "Custom",
        }

        card = CardConverter.from_anki_note(note)

        assert card is not None
        assert card.type == CardType.BASIC

    def test_extract_chapter_variations(self):
        """Test chapter extraction from various tag formats."""
        assert CardConverter._extract_chapter(["chapter-1", "test"]) == "chapter-1"
        assert CardConverter._extract_chapter(["chapter_2", "test"]) == "chapter_2"
        assert CardConverter._extract_chapter(["ch3", "test"]) == "ch3"
        assert CardConverter._extract_chapter(["test", "other"]) == ""


@pytest.mark.asyncio
class TestAnkiDeckImporter:
    """Tests for AnkiDeckImporter."""

    @pytest.fixture
    def config(self):
        """Create test Anki configuration."""
        return AnkiConfig(
            connect_url="http://localhost:8765",
            connect_timeout=5.0,
            retry_attempts=3,
        )

    @pytest.fixture
    def importer(self, config):
        """Create AnkiDeckImporter instance."""
        return AnkiDeckImporter(config)

    async def test_check_connection_success(self, importer):
        """Test successful connection check."""
        with patch.object(importer.client, "check_connection", new_callable=AsyncMock) as mock:
            mock.return_value = None
            result = await importer.check_connection()
            assert result is True
            mock.assert_awaited_once()

    async def test_check_connection_failure(self, importer):
        """Test failed connection check."""
        with patch.object(importer.client, "check_connection", new_callable=AsyncMock) as mock:
            from anki_mcp_server.client import AnkiConnectError

            mock.side_effect = AnkiConnectError("Connection failed")
            result = await importer.check_connection()
            assert result is False

    async def test_list_decks(self, importer):
        """Test listing decks."""
        with patch.object(importer.client, "get_deck_names", new_callable=AsyncMock) as mock:
            mock.return_value = ["Deck1", "Deck2", "Deck3"]
            decks = await importer.list_decks()
            assert len(decks) == 3
            assert "Deck1" in decks

    async def test_import_deck(self, importer):
        """Test importing deck."""
        mock_notes = [
            {
                "noteId": 1,
                "modelName": "Basic",
                "fields": {
                    "Front": {"value": "Q1"},
                    "Back": {"value": "A1"},
                },
                "tags": ["chapter-1"],
            },
            {
                "noteId": 2,
                "modelName": "Basic",
                "fields": {
                    "Front": {"value": "Q2"},
                    "Back": {"value": "A2"},
                },
                "tags": ["chapter-1"],
            },
        ]

        with (
            patch.object(importer.client, "find_notes", new_callable=AsyncMock) as find_mock,
            patch.object(importer.client, "notes_info", new_callable=AsyncMock) as info_mock,
        ):
            find_mock.return_value = [1, 2]
            info_mock.return_value = mock_notes

            cards = await importer.import_deck("TestDeck")

            assert len(cards) == 2
            assert all(isinstance(card, Card) for card in cards)
            assert cards[0].question == "Q1"
            assert cards[1].question == "Q2"

    async def test_import_deck_with_chapter(self, importer):
        """Test importing deck with chapter filter."""
        with (
            patch.object(importer.client, "find_notes", new_callable=AsyncMock) as find_mock,
            patch.object(importer.client, "notes_info", new_callable=AsyncMock) as info_mock,
        ):
            find_mock.return_value = [1]
            info_mock.return_value = [
                {
                    "noteId": 1,
                    "modelName": "Basic",
                    "fields": {
                        "Front": {"value": "Q1"},
                        "Back": {"value": "A1"},
                    },
                    "tags": ["chapter-1"],
                }
            ]

            cards = await importer.import_deck("TestDeck", chapter="chapter-1")

            find_mock.assert_awaited_once()
            call_args = find_mock.call_args[0][0]
            assert "chapter-1" in call_args
            assert len(cards) == 1

    async def test_import_deck_no_notes(self, importer):
        """Test importing deck with no notes."""
        with patch.object(importer.client, "find_notes", new_callable=AsyncMock) as mock:
            mock.return_value = []

            with pytest.raises(ValueError, match="No notes found"):
                await importer.import_deck("EmptyDeck")

    async def test_get_deck_info(self, importer):
        """Test getting deck information."""
        mock_notes = [
            {
                "noteId": 1,
                "tags": ["chapter-1", "test"],
            },
            {
                "noteId": 2,
                "tags": ["chapter-2", "test"],
            },
        ]

        with (
            patch.object(importer.client, "find_notes", new_callable=AsyncMock) as find_mock,
            patch.object(importer.client, "notes_info", new_callable=AsyncMock) as info_mock,
        ):
            find_mock.return_value = [1, 2, 3, 4, 5]
            info_mock.return_value = mock_notes

            info = await importer.get_deck_info("TestDeck")

            assert info["deck_name"] == "TestDeck"
            assert info["total_cards"] == 5
            assert "chapter-1" in info["chapters"]
            assert "chapter-2" in info["chapters"]
