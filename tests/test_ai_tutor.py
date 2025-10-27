"""Tests for AI Tutor with personality rotation."""

import pytest

from anki_course_tutor.ai_tutor import AITutor, Personality, PersonalityRotation
from anki_course_tutor.models.card import Card, CardType
from anki_course_tutor.models.session import LearningMode


class TestPersonalityRotation:
    """Test personality rotation logic."""

    def test_initialization(self):
        """Test PersonalityRotation initialization."""
        rotation = PersonalityRotation(0)
        assert rotation.get_current_count() == 0

    def test_initialization_with_count(self):
        """Test PersonalityRotation with existing count."""
        rotation = PersonalityRotation(5)
        assert rotation.get_current_count() == 5

    def test_first_three_normal(self):
        """Test first three explanations use normal personality."""
        rotation = PersonalityRotation(0)

        assert rotation.get_next_personality() == Personality.NORMAL  # 1st
        assert rotation.get_current_count() == 1

        assert rotation.get_next_personality() == Personality.NORMAL  # 2nd
        assert rotation.get_current_count() == 2

        assert rotation.get_next_personality() == Personality.NORMAL  # 3rd
        assert rotation.get_current_count() == 3

    def test_fourth_pirate(self):
        """Test fourth explanation uses pirate personality."""
        rotation = PersonalityRotation(0)

        # Skip first three
        rotation.get_next_personality()
        rotation.get_next_personality()
        rotation.get_next_personality()

        # Fourth should be pirate
        assert rotation.get_next_personality() == Personality.PIRATE
        assert rotation.get_current_count() == 4

    def test_rotation_continues(self):
        """Test rotation continues after first pirate."""
        rotation = PersonalityRotation(0)

        # First cycle: N, N, N, P
        for _ in range(3):
            assert rotation.get_next_personality() == Personality.NORMAL
        assert rotation.get_next_personality() == Personality.PIRATE

        # Second cycle: N, N, N, P
        for _ in range(3):
            assert rotation.get_next_personality() == Personality.NORMAL
        assert rotation.get_next_personality() == Personality.PIRATE

        assert rotation.get_current_count() == 8

    def test_rotation_persists_across_resume(self):
        """Test rotation state can be restored from count."""
        # Simulate session paused after 2 explanations
        rotation1 = PersonalityRotation(0)
        rotation1.get_next_personality()  # 1st: Normal
        rotation1.get_next_personality()  # 2nd: Normal
        count = rotation1.get_current_count()
        assert count == 2

        # Resume session with saved count
        rotation2 = PersonalityRotation(count)
        assert rotation2.get_next_personality() == Personality.NORMAL  # 3rd
        assert rotation2.get_next_personality() == Personality.PIRATE  # 4th

    def test_pirate_at_multiples_of_four(self):
        """Test pirate appears at positions 4, 8, 12, etc."""
        rotation = PersonalityRotation(0)

        pirate_positions = []
        for i in range(12):
            personality = rotation.get_next_personality()
            if personality == Personality.PIRATE:
                pirate_positions.append(i + 1)

        assert pirate_positions == [4, 8, 12]


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
        tutor = AITutor(0)
        assert tutor.get_current_count() == 0

    def test_initialization_with_count(self):
        """Test AITutor with existing count."""
        tutor = AITutor(3)
        assert tutor.get_current_count() == 3

    @pytest.mark.asyncio
    async def test_generate_explanation_normal(self, sample_card):
        """Test generating normal personality explanation."""
        tutor = AITutor(0)

        result = await tutor.generate_explanation(
            card=sample_card,
            user_answer="Berlin",
            correct_answer="Paris",
            mode=LearningMode.EXPLAIN,
        )

        assert result["personality"] == "normal"
        assert result["count"] == 1
        assert "explanation" in result
        assert len(result["explanation"]) > 0
        assert "Paris" in result["explanation"]

    @pytest.mark.asyncio
    async def test_generate_explanation_pirate(self, sample_card):
        """Test generating pirate personality explanation."""
        tutor = AITutor(3)  # Start at 3, next is pirate

        result = await tutor.generate_explanation(
            card=sample_card,
            user_answer="Berlin",
            correct_answer="Paris",
            mode=LearningMode.EXPLAIN,
        )

        assert result["personality"] == "pirate"
        assert result["count"] == 4
        assert "explanation" in result
        # Pirate speech indicators
        assert any(word in result["explanation"].lower() for word in ["ahoy", "matey", "ye"])

    @pytest.mark.asyncio
    async def test_test_mode_skips_explanation(self, sample_card):
        """Test that TEST mode does not generate explanations."""
        tutor = AITutor(0)

        result = await tutor.generate_explanation(
            card=sample_card,
            user_answer="Berlin",
            correct_answer="Paris",
            mode=LearningMode.TEST,
        )

        assert result["explanation"] == ""
        assert result["count"] == 0  # Count should not increment

    @pytest.mark.asyncio
    async def test_personality_rotation_in_tutor(self, sample_card):
        """Test personality rotation through tutor."""
        tutor = AITutor(0)

        # First three should be normal
        for i in range(3):
            result = await tutor.generate_explanation(
                card=sample_card,
                user_answer="Wrong",
                correct_answer="Right",
                mode=LearningMode.EXPLAIN,
            )
            assert result["personality"] == "normal"
            assert result["count"] == i + 1

        # Fourth should be pirate
        result = await tutor.generate_explanation(
            card=sample_card,
            user_answer="Wrong",
            correct_answer="Right",
            mode=LearningMode.EXPLAIN,
        )
        assert result["personality"] == "pirate"
        assert result["count"] == 4

    @pytest.mark.asyncio
    async def test_sentence_limiting(self, sample_card):
        """Test that explanations are limited to 5 sentences."""
        tutor = AITutor(0)

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
        tutor = AITutor(0)

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
        tutor = AITutor(0)
        text = "One. Two. Three. Four. Five."

        result = tutor._limit_sentences(text, max_sentences=5)
        assert result == text
        assert not result.endswith("...")

    def test_limit_sentences_more_than_five(self):
        """Test limiting text with more than 5 sentences."""
        tutor = AITutor(0)
        text = "One. Two. Three. Four. Five. Six. Seven. Eight."

        result = tutor._limit_sentences(text, max_sentences=5)
        assert result == "One. Two. Three. Four. Five...."
        assert result.count(".") == 8  # 5 sentences + 3 dots in ellipsis

    def test_limit_sentences_less_than_five(self):
        """Test limiting text with less than 5 sentences."""
        tutor = AITutor(0)
        text = "One. Two. Three."

        result = tutor._limit_sentences(text, max_sentences=5)
        assert result == text
        assert not result.endswith("...")

    def test_limit_sentences_with_multiple_punctuation(self):
        """Test limiting with different sentence endings."""
        tutor = AITutor(0)
        text = "One! Two? Three. Four! Five? Six. Seven."

        result = tutor._limit_sentences(text, max_sentences=5)
        assert "Six" not in result
        assert result.endswith("...")
