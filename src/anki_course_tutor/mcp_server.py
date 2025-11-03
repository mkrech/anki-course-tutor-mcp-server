"""MCP server with tools for Anki learning."""

import logging
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from anki_course_tutor.anki_client import AnkiClient, AnkiDeckImporter
from anki_course_tutor.config import AnkiConfig, StorageConfig
from anki_course_tutor.learning_engine import LearningEngine
from anki_course_tutor.models import LearningMode, LearningState, SessionStatus
from anki_course_tutor.progress_tracker import ProgressTracker
from anki_course_tutor.session_manager import SessionManager

logger = logging.getLogger(__name__)

# Global state for active session
_active_session = None
_learning_engine = None
_session_manager = None
_progress_tracker = None
_anki_importer = None
_anki_client = None  # NEW: Global AnkiClient for scheduler integration


def initialize_managers(
    anki_url: str = "http://localhost:8765",
    use_anki_scheduler: bool = True,
) -> None:
    """Initialize global managers.

    Args:
        anki_url: AnkiConnect URL
        use_anki_scheduler: Enable Anki scheduler integration
    """
    global _session_manager, _progress_tracker, _anki_importer, _anki_client

    # Create Anki config
    anki_config = AnkiConfig(
        connect_url=anki_url,
        connect_timeout=30,
        retry_attempts=3,
        use_anki_scheduler=use_anki_scheduler,
    )

    _session_manager = SessionManager()
    _progress_tracker = ProgressTracker()
    _anki_importer = AnkiDeckImporter(anki_config)
    
    # Initialize AnkiClient for scheduler integration if enabled
    if use_anki_scheduler:
        _anki_client = AnkiClient(url=anki_url)
        logger.info("Anki scheduler integration enabled")
    else:
        _anki_client = None
        logger.info("Anki scheduler integration disabled (local-only mode)")

    logger.info("Initialized managers for MCP server (in-memory mode)")



# Create MCP server
mcp = FastMCP("Anki Course Tutor")


@mcp.tool()
async def list_decks() -> dict[str, Any]:
    """List all available Anki decks.

    Returns:
        Dictionary with deck names and info
    """
    if not _anki_importer:
        return {"error": "Server not initialized. Call initialize_managers first."}

    try:
        # Check connection
        if not await _anki_importer.check_connection():
            return {
                "error": "Cannot connect to Anki. Please ensure Anki is running with AnkiConnect."
            }

        decks = await _anki_importer.list_decks()
        logger.info(f"Listed {len(decks)} decks")

        return {"decks": decks, "count": len(decks)}

    except Exception as e:
        logger.error(f"Failed to list decks: {e}")
        return {"error": str(e)}


@mcp.tool()
async def start_session(deck_name: str, chapter: str = "", mode: str = "explain") -> dict[str, Any]:
    """Start a new learning session with a deck.

    Args:
        deck_name: Name of the Anki deck to use
        chapter: Optional chapter filter
        mode: Learning mode - "explain" (with AI explanations) or "test" (no explanations)

    Returns:
        Dictionary with session info and first card
    """
    global _active_session, _learning_engine

    if not _session_manager or not _anki_importer:
        return {"error": "Server not initialized"}

    try:
        # Validate mode
        if mode not in ["explain", "test"]:
            return {"error": "Mode must be 'explain' or 'test'"}

        learning_mode = LearningMode.EXPLAIN if mode == "explain" else LearningMode.TEST

        # Import cards from Anki
        cards = await _anki_importer.import_deck(deck_name, chapter)
        if not cards:
            return {"error": f"No cards found in deck '{deck_name}'"}

        # DEBUG: Log card types
        logger.info(f"Imported {len(cards)} cards:")
        card_types_info = []
        for card in cards[:5]:  # Log first 5
            info_str = f"Card {card.id}: type={card.type.value}, all_in_one_type={card.all_in_one_type}"
            logger.info(f"  - {info_str}")
            card_types_info.append(info_str)

        # Create session
        session = _session_manager.create_session(deck_name, chapter, learning_mode)
        session.card_ids = [card.id for card in cards]
                # Save session
        _session_manager.save_session(session)

        # Initialize learning engine with optional AnkiClient
        _learning_engine = LearningEngine(session, cards, learning_mode, anki_client=_anki_client)
        _active_session = session

        logger.info(f"Started session {session.session_id} with {len(cards)} cards in {mode} mode")

        return {
            "session_id": session.session_id,
            "deck_name": deck_name,
            "chapter": chapter,
            "mode": mode,
            "total_cards": len(cards),
            "card_types_debug": card_types_info if card_types_info else [],
            "message": f"Session started with {len(cards)} cards. Call get_next_card to begin.",
        }

    except Exception as e:
        logger.error(f"Failed to start session: {e}")
        return {"error": str(e)}


@mcp.tool()
async def resume_session(session_id: str) -> dict[str, Any]:
    """Resume an existing learning session.

    Args:
        session_id: ID of the session to resume

    Returns:
        Dictionary with session info
    """
    global _active_session, _learning_engine

    if not _session_manager or not _anki_importer:
        return {"error": "Server not initialized"}

    try:
        # Load session
        session = _session_manager.load_session(session_id)

        # Check if can resume
        if session.status == SessionStatus.COMPLETED:
            return {"error": "Cannot resume completed session"}

        # Resume session
        session = _session_manager.resume_session(session_id)

        # Import cards
        cards = await _anki_importer.import_deck(session.deck_name, session.chapter)
        if not cards:
            return {"error": f"No cards found in deck '{session.deck_name}'"}

        # Filter to cards in session
        session_cards = [card for card in cards if card.id in session.card_ids]

        # Initialize learning engine with optional AnkiClient
        _learning_engine = LearningEngine(session, session_cards, session.mode, anki_client=_anki_client)
        _active_session = session

        logger.info(f"Resumed session {session_id}")

        return {
            "session_id": session.session_id,
            "deck_name": session.deck_name,
            "mode": session.mode.value,
            "total_cards": len(session_cards),
            "message": "Session resumed. Call get_next_card to continue.",
        }

    except FileNotFoundError:
        return {"error": f"Session {session_id} not found"}
    except Exception as e:
        logger.error(f"Failed to resume session: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_next_card() -> dict[str, Any]:
    """Get the next card to study.

    Returns:
        Dictionary with card question and metadata
    """
    if not _learning_engine or not _active_session:
        return {"error": "No active session. Start or resume a session first."}

    try:
        # Start if not started
        if _active_session.state == LearningState.NOT_STARTED:
            result = _learning_engine.start()
        else:
            result = _learning_engine.get_current_state()

        return result

    except Exception as e:
        logger.error(f"Failed to get next card: {e}")
        return {"error": str(e)}


@mcp.tool()
async def submit_answer(answer: str) -> dict[str, Any]:
    """Submit an answer for the current card.

    The system will automatically evaluate your answer and ask you to confirm.

    Args:
        answer: Your answer to the current card

    Returns:
        Dictionary with automatic evaluation result for review
    """
    if not _learning_engine or not _active_session:
        return {"error": "No active session"}

    try:
        result = _learning_engine.submit_answer(answer)
        logger.info(f"Answer submitted, automatic evaluation: {result.get('automatic_evaluation')}")
        return result

    except Exception as e:
        logger.error(f"Failed to submit answer: {e}")
        return {"error": str(e)}


@mcp.tool()
async def confirm_evaluation(is_correct: bool) -> dict[str, Any]:
    """Confirm or override the automatic evaluation.

    The system shows its evaluation of your answer. You need to confirm if this evaluation is correct.
    
    Examples:
    - System says "INCORRECT" and you agree → is_correct: True (evaluation is right)
    - System says "INCORRECT" but you think your answer was right → is_correct: False (evaluation is wrong)

    Args:
        is_correct: True if the system's evaluation is correct, False if you disagree with it

    Returns:
        Dictionary with next action (next card or explanation)
    """
    if not _learning_engine or not _active_session:
        return {"error": "No active session"}

    try:
        result = await _learning_engine.confirm_evaluation(is_correct)

        # Update session
        _session_manager.save_session(_active_session)

        logger.info(f"Evaluation confirmed: {is_correct}, next state: {result.get('state')}")
        return result

    except Exception as e:
        logger.error(f"Failed to confirm evaluation: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_explanation() -> dict[str, Any]:
    """Get AI explanation for an incorrect answer.

    Only available in EXPLAIN mode after confirming an incorrect answer.

    Returns:
        Dictionary with AI-generated explanation
    """
    if not _learning_engine or not _active_session:
        return {"error": "No active session"}

    try:
        result = await _learning_engine.get_explanation()

        # Update session
        _session_manager.save_session(_active_session)

        logger.info(f"Generated explanation for card")
        return result

    except Exception as e:
        logger.error(f"Failed to get explanation: {e}")
        return {"error": str(e)}


@mcp.tool()
async def next_card_after_explanation() -> dict[str, Any]:
    """Move to next card after reading explanation.

    Call this after get_explanation to continue learning.

    Returns:
        Dictionary with next card
    """
    if not _learning_engine or not _active_session:
        return {"error": "No active session"}

    try:
        result = _learning_engine.next_card_after_explanation()
        logger.debug("Moved to next card after explanation")
        return result

    except Exception as e:
        logger.error(f"Failed to move to next card: {e}")
        return {"error": str(e)}


@mcp.tool()
async def get_session_stats() -> dict[str, Any]:
    """Get statistics for the current session.

    Returns:
        Dictionary with session progress and statistics
    """
    if not _learning_engine or not _active_session:
        return {"error": "No active session"}

    try:
        stats = _learning_engine._get_stats()
        state_info = _learning_engine.get_current_state()

        return {
            "session_id": _active_session.session_id,
            "deck_name": _active_session.deck_name,
            "mode": _active_session.mode.value,
            "state": state_info["state"],
            "stats": stats,
        }

    except Exception as e:
        logger.error(f"Failed to get session stats: {e}")
        return {"error": str(e)}


@mcp.tool()
async def end_session() -> dict[str, Any]:
    """End the current session and save progress.

    Returns:
        Dictionary with final statistics
    """
    global _active_session, _learning_engine

    if not _active_session or not _learning_engine:
        return {"error": "No active session"}

    try:
        # Calculate final statistics
        card_progress = _active_session.card_progress
        stats = _progress_tracker.calculate_statistics(card_progress, _active_session.created_at)

        # Create Progress object and save
        from anki_course_tutor.models.progress import Progress

        progress = Progress(
            session_id=_active_session.session_id,
            deck_name=_active_session.deck_name,
            chapter=_active_session.chapter,
            created_at=_active_session.created_at,
            state="completed",
            statistics=stats,
        )
        _progress_tracker.save(progress, card_progress)

        # Mark session complete
        _active_session.status = SessionStatus.COMPLETED
        _active_session.state = LearningState.SESSION_COMPLETE
        _session_manager.save_session(_active_session)

        session_id = _active_session.session_id
        final_stats = {
            "session_id": session_id,
            "deck_name": _active_session.deck_name,
            "total_cards": stats.total_cards,
            "completed_cards": stats.completed_cards,
            "correct_rate": stats.correct_rate,
            "total_attempts": stats.total_attempts,
            "session_duration_seconds": stats.session_duration_seconds,
        }

        # Clear active session
        _active_session = None
        _learning_engine = None

        logger.info(f"Session {session_id} ended with {stats.correct_rate:.1%} correct rate")
        return {**final_stats, "message": "Session completed successfully!"}

    except Exception as e:
        logger.error(f"Failed to end session: {e}")
        return {"error": str(e)}


@mcp.tool()
async def list_sessions() -> dict[str, Any]:
    """List all saved sessions.

    Returns:
        Dictionary with session list
    """
    if not _session_manager:
        return {"error": "Server not initialized"}

    try:
        sessions = _session_manager.list_sessions()
        logger.info(f"Listed {len(sessions)} sessions")

        return {
            "sessions": [
                {
                    "session_id": s["id"],  # SessionManager uses "id" not "session_id"
                    "deck_name": s["deck_name"], 
                    "chapter": s.get("chapter", ""),
                    "mode": s["mode"],
                    "status": s["status"],
                    "created_at": s["created_at"],
                    "card_count": s.get("total_cards", 0),
                }
                for s in sessions
            ],
            "count": len(sessions),
        }

    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return {"error": str(e)}


# Resources
@mcp.resource("deck://list")
async def get_deck_list() -> str:
    """Get list of available Anki decks as a resource."""
    if not _anki_importer:
        return "Error: Server not initialized"

    try:
        if not await _anki_importer.check_connection():
            return "Error: Cannot connect to Anki"

        decks = await _anki_importer.list_decks()
        return "\n".join(f"- {deck}" for deck in decks)

    except Exception as e:
        return f"Error: {e}"


@mcp.resource("session://active")
async def get_active_session() -> str:
    """Get current active session info as a resource."""
    if not _active_session:
        return "No active session"

    return f"""Active Session: {_active_session.session_id}
Deck: {_active_session.deck_name}
Mode: {_active_session.mode.value}
State: {_active_session.state.value}
Status: {_active_session.status.value}
Cards: {len(_active_session.card_ids)}
Created: {_active_session.created_at.strftime("%Y-%m-%d %H:%M")}
"""


def run_server(config=None):
    """Run the MCP server.
    
    Args:
        config: Optional Config object. If not provided, defaults are used.
    """
    # Initialize managers with config
    if config:
        initialize_managers(
            anki_url=config.anki.connect_url,
            use_anki_scheduler=config.anki.use_anki_scheduler,
        )
    else:
        initialize_managers()

    logger.info("Starting Anki Course Tutor MCP Server...")
    logger.info("Available tools: list_decks, start_session, resume_session, get_next_card")
    logger.info("                 submit_answer, confirm_evaluation, get_explanation")
    logger.info("                 next_card_after_explanation, get_session_stats, end_session")
    logger.info("Available resources: deck://list, session://active")

    # Run FastMCP server
    mcp.run()
