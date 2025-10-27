"""Tests for AI Tutor explanation generation."""

import pytest

from anki_course_tutor.ai_tutor import AITutor
from anki_course_tutor.models.card import Card, CardType
from anki_course_tutor.models.session import LearningMode


class TestAITutor:
    """Test AI tutor explanation generation."""

    @pytest.fixture
    def sample_card(self):
        """Create a sample card for testing."""
        return Card(
            id="test-card-1",
            type=CardType.BASIC,
            question="What is the capital of France?",
            answer="Paris",
            deck="Geography",
            chapter="Europe",
        )

    def test_initialization(self):
        """Test AITutor initialization."""
        tutor = AITutor()
        assert tutor is not None

    @pytest.mark.asyncio
    async def test_generate_explanation_normal(self, sample_card):
        """Test generating explanation."""
        tutor = AITutor()

        result = await tutor.generate_explanation(
            card=sample_card,
            user_answer="Berlin",
            correct_answer="Paris",
            mode=LearningMode.EXPLAIN,
        )

        assert result["count"] == 1
        assert "explanation" in result
        assert len(result["explanation"]) > 0
        assert "Paris" in result["explanation"]

    @pytest.mark.asyncio
    async def test_test_mode_skips_explanation(self, sample_card):
        """Test that TEST mode does not generate explanations."""
        tutor = AITutor()

        result = await tutor.generate_explanation(
            card=sample_card,
            user_answer="Berlin",
            correct_answer="Paris",
            mode=LearningMode.TEST,
        )

        assert result["explanation"] == ""
        assert result["count"] == 0  # Count should not increment

    @pytest.mark.asyncio
    async def test_sentence_limiting(self, sample_card):
        """Test that explanations are limited to 5 sentences."""
        tutor = AITutor()

        # Use placeholder which generates exactly 5 sentences
        result = await tutor.generate_explanation(
            card=sample_card,
            user_answer="Berlin",
            correct_answer="Paris",
            mode=LearningMode.EXPLAIN,
        )

        # Count sentences in explanation
        explanation = result["explanation"]
        sentences = [s for s in explanation.split(".") if s.strip()]
        assert len(sentences) <= 5

    @pytest.mark.asyncio
    async def test_prompt_includes_context(self, sample_card):
        """Test that prompts include card context."""
        tutor = AITutor()

        result = await tutor.generate_explanation(
            card=sample_card,
            user_answer="Berlin",
            correct_answer="Paris",
            mode=LearningMode.EXPLAIN,
        )

        prompt = result["prompt"]
        assert "What is the capital of France?" in prompt
        assert "Paris" in prompt
        assert "Berlin" in prompt
        assert "Geography" in prompt

    def test_limit_sentences_exact_five(self):
        """Test limiting text with exactly 5 sentences."""
        tutor = AITutor()
        text = "One. Two. Three. Four. Five."

        result = tutor._limit_sentences(text, max_sentences=5)
        assert result == text
        assert not result.endswith("...")

    def test_limit_sentences_more_than_five(self):
        """Test limiting text with more than 5 sentences."""
        tutor = AITutor()
        text = "One. Two. Three. Four. Five. Six. Seven. Eight."

        result = tutor._limit_sentences(text, max_sentences=5)
        assert result == "One. Two. Three. Four. Five...."
        assert result.count(".") == 8  # 5 sentences + 3 dots in ellipsis

    def test_limit_sentences_less_than_five(self):
        """Test limiting text with less than 5 sentences."""
        tutor = AITutor()
        text = "One. Two. Three."

        result = tutor._limit_sentences(text, max_sentences=5)
        assert result == text
        assert not result.endswith("...")

    def test_limit_sentences_with_multiple_punctuation(self):
        """Test limiting with different sentence endings."""
        tutor = AITutor()
        text = "One! Two? Three. Four! Five? Six. Seven."

        result = tutor._limit_sentences(text, max_sentences=5)
        assert "Six" not in result
        assert result.endswith("...")
