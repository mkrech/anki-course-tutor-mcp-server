"""Anki integration - deck importing and card conversion."""

import logging
import re
from typing import Any

import httpx

from anki_course_tutor.config import AnkiConfig
from anki_course_tutor.models import Card, CardType

logger = logging.getLogger(__name__)


class AnkiConnectError(Exception):
    """Error communicating with AnkiConnect."""

    pass


class AnkiClient:
    """Simple AnkiConnect client."""

    def __init__(self, url: str = "http://localhost:8765"):
        """Initialize AnkiConnect client.

        Args:
            url: AnkiConnect API URL
        """
        self.url = url

    async def invoke(self, action: str, **params) -> Any:
        """Invoke AnkiConnect action.

        Args:
            action: AnkiConnect action name
            **params: Action parameters

        Returns:
            Action result

        Raises:
            AnkiConnectError: If request fails
        """
        payload = {"action": action, "version": 6, "params": params}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.url, json=payload, timeout=10.0)
                response.raise_for_status()
                result = response.json()

                if "error" in result and result["error"] is not None:
                    raise AnkiConnectError(f"AnkiConnect error: {result['error']}")

                return result.get("result")

            except httpx.HTTPError as e:
                raise AnkiConnectError(f"HTTP error: {e}") from e

    async def check_connection(self) -> bool:
        """Check if AnkiConnect is available.
        
        Returns:
            True if connection successful
        """
        try:
            await self.invoke("version")
            return True
        except AnkiConnectError:
            return False

    async def get_deck_names(self) -> list[str]:
        """Get list of deck names.
        
        Returns:
            List of deck names
        """
        return await self.invoke("deckNames")

    async def find_notes(self, query: str) -> list[int]:
        """Find notes matching query.
        
        Args:
            query: Search query
            
        Returns:
            List of note IDs
        """
        return await self.invoke("findNotes", query=query)

    async def notes_info(self, note_ids: list[int]) -> list[dict[str, Any]]:
        """Get information about notes.
        
        Args:
            note_ids: List of note IDs
            
        Returns:
            List of note information dictionaries
        """
        return await self.invoke("notesInfo", notes=note_ids)

    async def answer_card(self, card_id: int, ease: int) -> None:
        """Submit answer for a card to Anki's scheduler.
        
        Args:
            card_id: Anki card ID
            ease: Ease button pressed (1=Again, 2=Hard, 3=Good, 4=Easy)
            
        Raises:
            AnkiConnectError: If submission fails
            ValueError: If ease value is invalid
        """
        if ease not in (1, 2, 3, 4):
            raise ValueError(f"Invalid ease value: {ease}. Must be 1-4.")
        
        # answerCards expects answers as list of dicts with cardId and ease
        await self.invoke("answerCards", answers=[{"cardId": card_id, "ease": ease}])

    async def get_card_info(self, card_id: int) -> dict[str, Any]:
        """Get detailed information about a card.
        
        Args:
            card_id: Anki card ID
            
        Returns:
            Dictionary with card information (due, interval, ease factor, etc.)
            
        Raises:
            AnkiConnectError: If request fails
        """
        result = await self.invoke("cardsInfo", cards=[card_id])
        if not result:
            raise AnkiConnectError(f"No information found for card {card_id}")
        return result[0]

    async def get_reviews_of_cards(self, card_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
        """Get review history for multiple cards.
        
        Args:
            card_ids: List of Anki card IDs
            
        Returns:
            Dictionary mapping card ID to list of review records
            Each review record contains: id, usn, ease, ivl, lastIvl, factor, time, type
            
        Raises:
            AnkiConnectError: If request fails
        """
        # AnkiConnect returns format: "card_id": [[id, usn, ease, ivl, lastIvl, factor, time, type], ...]
        result = await self.invoke("getReviewsOfCards", cards=card_ids)
        
        # Convert to more readable format
        reviews_map = {}
        for card_id_str, review_arrays in result.items():
            card_id = int(card_id_str)
            reviews = []
            for review_array in review_arrays:
                if len(review_array) >= 8:
                    reviews.append({
                        "id": review_array[0],
                        "usn": review_array[1],
                        "ease": review_array[2],
                        "interval": review_array[3],
                        "last_interval": review_array[4],
                        "ease_factor": review_array[5],
                        "time_ms": review_array[6],
                        "type": review_array[7],
                    })
            reviews_map[card_id] = reviews
        
        return reviews_map


class CardConverter:
    """Convert Anki notes to unified Card model."""

    @staticmethod
    def from_anki_note(note: dict[str, Any]) -> Card | None:
        """Convert Anki note to Card based on note type.

        Args:
            note: Anki note dictionary with fields, modelName, tags, etc.

        Returns:
            Card object or None if conversion fails
        """
        try:
            model_name = note.get("modelName", "")
            note_id = str(note.get("noteId", ""))
            fields = note.get("fields", {})
            tags = note.get("tags", [])

            # Extract deck name from note (if available)
            deck = ""
            if "deckName" in note:
                deck = note["deckName"]

            # Determine card type and convert
            if model_name == "Basic":
                return CardConverter._convert_basic(note_id, fields, deck, tags)
            elif model_name == "Cloze":
                return CardConverter._convert_cloze(note_id, fields, deck, tags)
            elif "Multiple Choice" in model_name or "MC" in model_name:
                return CardConverter._convert_multiple_choice(note_id, fields, deck, tags)
            else:
                # Try to convert as Basic (fallback)
                logger.warning(f"Unknown model type '{model_name}', attempting Basic conversion")
                return CardConverter._convert_basic(note_id, fields, deck, tags)

        except Exception as e:
            logger.error(f"Failed to convert note {note.get('noteId')}: {e}")
            return None

    @staticmethod
    def _convert_basic(note_id: str, fields: dict[str, Any], deck: str, tags: list[str]) -> Card:
        """Convert Basic note type to Card."""
        front = fields.get("Front", {}).get("value", "")
        back = fields.get("Back", {}).get("value", "")

        # Clean HTML tags
        front = CardConverter._clean_html(front)
        back = CardConverter._clean_html(back)

        # Extract chapter from tags
        chapter = CardConverter._extract_chapter(tags)

        return Card(
            id=note_id,
            type=CardType.BASIC,
            question=front,
            answer=back,
            deck=deck,
            chapter=chapter,
            tags=tags,
        )

    @staticmethod
    def _convert_cloze(note_id: str, fields: dict[str, Any], deck: str, tags: list[str]) -> Card:
        """Convert Cloze note type to Card."""
        text = fields.get("Text", {}).get("value", "")
        cloze_text = text

        # Clean HTML
        text = CardConverter._clean_html(text)

        # Extract first cloze deletion for question
        # Pattern: {{c1::answer}}
        cloze_pattern = r"\{\{c(\d+)::([^}]+)\}\}"
        matches = list(re.finditer(cloze_pattern, text))

        if not matches:
            logger.warning(f"No cloze deletions found in note {note_id}")
            question = text
            answer = ""
        else:
            # Use first cloze as the question
            first_match = matches[0]
            answer = first_match.group(2)
            # Replace cloze with [...] for question
            question = re.sub(r"\{\{c\d+::([^}]+)\}\}", "[...]", text, count=1)

        chapter = CardConverter._extract_chapter(tags)

        return Card(
            id=note_id,
            type=CardType.CLOZE,
            question=question,
            answer=answer,
            deck=deck,
            chapter=chapter,
            cloze_text=cloze_text,
            tags=tags,
        )

    @staticmethod
    def _convert_multiple_choice(
        note_id: str, fields: dict[str, Any], deck: str, tags: list[str]
    ) -> Card:
        """Convert Multiple Choice note type to Card."""
        question = fields.get("Question", {}).get("value", "")
        option1 = fields.get("Option1", {}).get("value", "")
        option2 = fields.get("Option2", {}).get("value", "")
        option3 = fields.get("Option3", {}).get("value", "")
        option4 = fields.get("Option4", {}).get("value", "")
        answer = fields.get("Answer", {}).get("value", "")

        # Clean HTML
        question = CardConverter._clean_html(question)
        option1 = CardConverter._clean_html(option1)
        option2 = CardConverter._clean_html(option2)
        option3 = CardConverter._clean_html(option3)
        option4 = CardConverter._clean_html(option4)
        answer = CardConverter._clean_html(answer)

        options = [opt for opt in [option1, option2, option3, option4] if opt]

        chapter = CardConverter._extract_chapter(tags)

        return Card(
            id=note_id,
            type=CardType.MULTIPLE_CHOICE,
            question=question,
            answer=answer,
            deck=deck,
            chapter=chapter,
            options=options,
            tags=tags,
        )

    @staticmethod
    def _clean_html(text: str) -> str:
        """Remove HTML tags from text."""
        # Simple HTML tag removal
        text = re.sub(r"<[^>]+>", "", text)
        # Decode common HTML entities
        text = text.replace("&nbsp;", " ")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")
        return text.strip()

    @staticmethod
    def _extract_chapter(tags: list[str]) -> str:
        """Extract chapter from tags.

        Looks for tags like 'chapter-1', 'chapter_1', or 'ch1'.
        """
        for tag in tags:
            tag_lower = tag.lower()
            if tag_lower.startswith("chapter"):
                return tag
            if tag_lower.startswith("ch") and len(tag_lower) > 2:
                return tag
        return ""


class AnkiDeckImporter:
    """Import cards from Anki decks via AnkiConnect."""

    def __init__(self, config: AnkiConfig):
        """Initialize importer with configuration.

        Args:
            config: Anki configuration with connection settings
        """
        self.config = config
        self.client = AnkiClient(url=config.connect_url)

    async def check_connection(self) -> bool:
        """Verify Anki is running and AnkiConnect is available.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            await self.client.check_connection()
            logger.info("Successfully connected to Anki")
            return True
        except AnkiConnectError as e:
            logger.error(f"Failed to connect to Anki: {e}")
            return False

    async def list_decks(self) -> list[str]:
        """List all available Anki decks.

        Returns:
            List of deck names

        Raises:
            AnkiConnectError: If connection fails
        """
        try:
            decks = await self.client.get_deck_names()
            logger.info(f"Found {len(decks)} decks")
            return decks
        except AnkiConnectError as e:
            logger.error(f"Failed to list decks: {e}")
            raise

    async def import_deck(self, deck_name: str, chapter: str = "") -> list[Card]:
        """Import cards from Anki deck.

        Args:
            deck_name: Name of the deck to import
            chapter: Optional chapter filter (filters by tag)

        Returns:
            List of Card objects

        Raises:
            AnkiConnectError: If connection fails
            ValueError: If deck not found
        """
        logger.info(f"Importing deck '{deck_name}'" + (f" chapter '{chapter}'" if chapter else ""))

        try:
            # Build query
            query = f'"deck:{deck_name}"'
            if chapter:
                query += f' "tag:{chapter}"'

            # Find notes
            note_ids = await self.client.find_notes(query)

            if not note_ids:
                raise ValueError(
                    f"No notes found in deck '{deck_name}'"
                    + (f" with chapter '{chapter}'" if chapter else "")
                )

            logger.info(f"Found {len(note_ids)} notes")

            # Get note info
            notes_info = await self.client.notes_info(note_ids)

            # Convert to cards
            cards = []
            for note in notes_info:
                # Add deck name to note for converter
                note["deckName"] = deck_name
                card = CardConverter.from_anki_note(note)
                if card:
                    cards.append(card)

            logger.info(f"Successfully imported {len(cards)} cards")
            return cards

        except AnkiConnectError as e:
            logger.error(f"Failed to import deck: {e}")
            raise

    async def get_deck_info(self, deck_name: str) -> dict[str, Any]:
        """Get information about a deck.

        Args:
            deck_name: Name of the deck

        Returns:
            Dictionary with deck information (card count, chapters, etc.)
        """
        try:
            query = f'"deck:{deck_name}"'
            note_ids = await self.client.find_notes(query)

            # Get notes to analyze
            notes_info = await self.client.notes_info(note_ids[:100])  # Sample first 100

            # Extract chapters from tags
            chapters = set()
            for note in notes_info:
                tags = note.get("tags", [])
                chapter = CardConverter._extract_chapter(tags)
                if chapter:
                    chapters.add(chapter)

            return {
                "deck_name": deck_name,
                "total_cards": len(note_ids),
                "chapters": sorted(chapters),
            }

        except AnkiConnectError as e:
            logger.error(f"Failed to get deck info: {e}")
            raise
