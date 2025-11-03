---
description: Complete workflow for learning with Anki Course Tutor MCP Server.
---

$ARGUMENTS
<!-- LEARNING-WORKFLOW:START -->
**Guardrails**
- Ensure Anki Desktop is running with AnkiConnect addon installed before starting
- Always confirm automatic evaluations - be honest about correctness
- Use EXPLAIN mode for learning, TEST mode for assessment
- Read AI explanations carefully when answers are incorrect
- Track progress regularly to maintain motivation

**Steps**
1. **List Available Decks** - Run `list_decks` to see all available Anki decks with card counts and select the deck you want to study.
2. **Start Learning Session** - Use `start_session` with your chosen deck name, specify mode (EXPLAIN or TEST), and optionally filter by chapter.
3. **Get First Card** - Call `get_next_card` to receive the first question from your learning session.
4. **Submit Answer** - Provide your answer using `submit_answer`; the system will automatically evaluate it and show you the expected answer.
5. **Confirm Evaluation** - Review the automatic evaluation carefully and use `confirm_evaluation` to agree (is_correct: true) or disagree (is_correct: false) with the assessment.
6. **Read Explanation** (EXPLAIN mode only) - If your answer was incorrect, use `get_explanation` to receive an AI-generated explanation of the correct answer.
7. **Continue Learning** - After explanation, call `next_card_after_explanation` to move to the next card, or directly `get_next_card` if no explanation was shown.
8. **Check Progress** - Periodically use `get_session_stats` to view your current progress, accuracy rate, and remaining cards.
9. **End Session** - When finished, call `end_session` to save your progress and view final statistics including total cards studied, accuracy, and time spent.

**Session Management**
- **Pause & Resume**: Sessions are automatically saved; use `list_sessions` to find your session ID and `resume_session` to continue later.
- **Multiple Modes**:
  - `EXPLAIN` mode: Get AI explanations for incorrect answers (recommended for learning)
  - `TEST` mode: Assessment only, no explanations provided
- **Anki Scheduler Integration**: When `use_anki_scheduler: true` in config, reviews are synced to Anki (Correct=Easy(4), Incorrect=Again(1))

**Tips for Effective Learning**
- Be honest during evaluation confirmation - only confirm if the assessment is truly correct
- In EXPLAIN mode, read explanations thoroughly before moving to the next card
- Check progress every 10-15 cards to maintain awareness of your performance
- Take breaks between sessions to avoid fatigue
- Use TEST mode only when you're confident and want to assess your knowledge

**Example Workflow**

```
# 1. Check available decks
You: List my Anki decks
AI: Found 3 decks: Spanish Vocabulary (150 cards), Python Programming (87 cards), History (45 cards)

# 2. Start session
You: Start a learning session with "Spanish Vocabulary" in EXPLAIN mode
AI: ✓ Session created (ID: abc-123), 150 cards loaded, Mode: EXPLAIN

# 3. Get cards and answer
You: Show me the next card
AI: 📝 Card 1/150 - Question: ¿Cómo estás?

You: How are you?
AI: 🤔 Automatic evaluation: CORRECT
    Expected: "How are you?" or "Wie geht es dir?"
    Your answer: "How are you?"
    Do you agree with this evaluation? (yes/no)

You: Yes
AI: ✅ Correct! Progress: 1/150 (0.7%)

# 4. Continue with another card
You: Next card
AI: 📝 Card 2/150 - Question: ¿Qué hora es?

You: What hour is it?
AI: 🤔 Automatic evaluation: INCORRECT
    Expected: "What time is it?" or "Wie spät ist es?"
    Your answer: "What hour is it?"
    Do you agree with this evaluation? (yes/no)

You: Yes
AI: ❌ Let me explain:
    💡 "¿Qué hora es?" translates to "What time is it?" The difference 
    between "time" and "hour" is important: "time" refers to the point 
    on the clock, while "hour" refers to duration. In English/German, 
    we use "time"/"Uhrzeit" for this question.

You: Got it, next card
AI: 📝 Card 3/150 - Question: ...

# 5. Check progress periodically
You: Show me my current progress
AI: 📊 Session Statistics:
    - Cards studied: 25/150 (16.7%)
    - Correct: 20 (80.0%)
    - Incorrect: 5 (20.0%)
    - Time: 12 minutes

# 6. End session
You: End the session and show final statistics
AI: ✓ Session completed
    📊 Final Statistics:
    - Total cards: 50
    - Correct: 42 (84.0%)
    - Incorrect: 8 (16.0%)
    - Duration: 25 minutes
    - Explanations given: 8
    🎯 Great job! 84% accuracy rate!
```

**Troubleshooting**
- **Deck not found**: Ensure Anki is running and AnkiConnect is active
- **Session errors**: Check `data/sessions/` for corrupted session files
- **No explanations**: Verify mode is set to EXPLAIN, not TEST
- **Connection timeout**: Increase `connect_timeout` in `config.yaml`

**Reference**
- Available MCP Tools: `list_decks`, `start_session`, `resume_session`, `get_next_card`, `submit_answer`, `confirm_evaluation`, `get_explanation`, `next_card_after_explanation`, `get_session_stats`, `end_session`, `list_sessions`
- Configuration: Edit `config.yaml` for Anki connection, scheduler integration, tutor personalities, and evaluation behavior
- Card Types Supported: Basic (Q&A), Cloze (fill-in-blank), Multiple Choice
- Documentation: See `README.md` for setup, `docs/MANUAL_TESTING.md` for testing scenarios, `docs/LEARNING_WORKFLOW_PROMPT.md` for detailed examples
<!-- LEARNING-WORKFLOW:END -->
