# Manual Testing with Real Anki Deck

This guide explains how to manually test the Anki Course Tutor MCP Server with a real Anki installation.

## Prerequisites

1. **Anki installed** with AnkiConnect addon
2. **AnkiConnect addon** (Code: 2055492159)
   - Tools → Add-ons → Get Add-ons → Enter code → OK
   - Restart Anki

3. **Anki deck** with at least a few cards ready

## Setup

1. **Start Anki** and keep it running in the background
   - AnkiConnect requires Anki to be open

2. **Install the server**:
   ```bash
   cd /path/to/anki-course-tutor-mcp-server
   uv sync
   ```

3. **Configure MCP** (e.g., for Claude Desktop):
   Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "anki-course-tutor": {
         "command": "uv",
         "args": [
           "--directory",
           "/full/path/to/anki-course-tutor-mcp-server",
           "run",
           "anki-course-tutor"
         ]
       }
     }
   }
   ```

4. **Restart Claude Desktop**

## Test Workflow

### Test 1: List Decks
**User**: "List available Anki decks"

**Expected**: Server returns list of your Anki decks

### Test 2: Start Learning Session
**User**: "Start a learning session with [YourDeckName] deck in EXPLAIN mode"

**Expected**: Server creates session and returns session ID

### Test 3: Get First Card
**User**: "Show me the next card"

**Expected**: Server presents the question from first card

### Test 4: Submit Answer
**User**: [Your answer to the question]

**Expected**: 
- Server evaluates answer automatically
- Returns evaluation (CORRECT/INCORRECT) and asks for confirmation
- Shows correct answer if applicable

### Test 5: Review Evaluation
**User**: "yes" (if you agree) or "no, I was correct/incorrect" (to override)

**Expected**:
- If EXPLAIN mode + incorrect: Server moves to EXPLAINING state
- If TEST mode or correct: Server moves to next card
- Shows previous result feedback in TEST mode

### Test 6: Get Explanation (EXPLAIN mode only)
After incorrect answer in EXPLAIN mode:

**User**: "Explain this to me"

**Expected**:
- Server generates explanation using AI
- Max 5 sentences
- Review submitted to Anki scheduler (ease=1 for incorrect)

### Test 7: Continue After Explanation
**User**: "Next card"

**Expected**: Server moves to next new card

### Test 8: Complete Session
Continue through all cards. Incorrect cards will return for retry.

**User**: "Show session statistics"

**Expected**: 
- Completed cards count
- Correct/incorrect counts
- Accuracy rate
- Session duration

### Test 9: End Session
**User**: "End the learning session"

**Expected**:
- Session marked as completed
- Progress saved to JSON file
- Confirmation message

## Verification Points

### ✅ Deck Import
- [ ] All card types imported (Basic, Cloze, Multiple Choice)
- [ ] Card metadata preserved (deck name, chapter, tags)
- [ ] HTML content cleaned properly

### ✅ Learning Flow
- [ ] New cards presented first
- [ ] Incorrect cards added to retry queue
- [ ] Retry cards presented after all new cards
- [ ] Session completes when all cards mastered

### ✅ Answer Evaluation
- [ ] Basic cards: case-insensitive, whitespace-normalized
- [ ] Cloze cards: extract answer from cloze deletion
- [ ] Multiple choice: match selected option
- [ ] Variant answers accepted (e.g., "How are you?" and "How do you do?")

### ✅ User Review/Override
- [ ] Can confirm automatic evaluation
- [ ] Can override CORRECT → INCORRECT
- [ ] Can override INCORRECT → CORRECT
- [ ] Override affects card progress correctly
- [ ] Reviews submitted to Anki scheduler with correct ease values

### ✅ AI Tutor
- [ ] Explanations generated for incorrect answers (EXPLAIN mode)
- [ ] Sentence limiting applied (max 5)
- [ ] Context includes card question and correct answer

### ✅ Anki Scheduler Integration
- [ ] Reviews submitted to Anki Desktop (check Anki browser)
- [ ] Correct answers use ease=4 (Easy)
- [ ] Incorrect answers use ease=1 (Again)
- [ ] Card intervals updated in Anki
- [ ] Graceful error if Anki not running

### ✅ Progress Tracking
- [ ] Progress saved to JSON file
- [ ] Statistics calculated correctly
- [ ] Can resume paused sessions
- [ ] Atomic writes with backup

### ✅ Error Handling
- [ ] Graceful handling if Anki is closed
- [ ] Clear error messages for connection issues
- [ ] Recovery from corrupted progress files

## Common Issues

### Issue: "AnkiConnect not available"
**Solution**: 
- Check Anki is running
- Verify AnkiConnect addon installed
- Test connection: http://localhost:8765

### Issue: "Deck not found"
**Solution**:
- Verify deck name matches exactly (case-sensitive)
- Check deck has cards
- Refresh deck list in Anki

### Issue: "Session not found"
**Solution**:
- Session may have expired
- Check `data/sessions/` directory
- Start new session

## Test Results Template

```
Date: ____________________
Tester: __________________
Anki Version: ____________
Deck Name: _______________
Number of Cards: _________

✅ Deck import successful
✅ Learning flow works
✅ Answer evaluation accurate
✅ User review/override works
✅ AI explanations generated
✅ Anki scheduler integration works
✅ Reviews visible in Anki browser
✅ Progress tracking works
✅ Session resume works
✅ Statistics accurate
✅ Error handling graceful

Notes:
_________________________
_________________________
```

## Advanced Testing

### Test Anki Scheduler Integration
1. Start Anki Desktop and open a test deck
2. Note the current review count for some cards
3. Start learning session with this deck
4. Complete some cards (both correct and incorrect)
5. Check Anki browser - verify:
   - Review history updated
   - Card intervals changed
   - Due dates updated appropriately
6. Close Anki Desktop
7. Try to answer a card → should get error message
8. Reopen Anki → should work again

### Test AnkiWeb Sync
1. Complete learning session with reviews submitted to Anki
2. Use Anki Desktop to sync with AnkiWeb
3. Check AnkiWeb to verify reviews synced
4. Access Anki on different device
5. Verify review history is present
6. Complete more reviews
7. Sync again and verify bidirectional sync works

### Test Multiple Sessions
1. Start session A with Deck 1
2. Pause session A
3. Start session B with Deck 2  
4. Complete session B
5. Resume session A
6. Verify both progress files exist

### Test Error Recovery
1. Start session
2. Kill Anki during session
3. Try to get next card (should fail gracefully)
4. Restart Anki
5. Resume session (should work)

## Performance Benchmarks

- **Deck Import**: < 2 seconds for 100 cards
- **Answer Evaluation**: < 100ms per card
- **AI Explanation**: < 5 seconds (depends on LLM)
- **Progress Save**: < 50ms

## Reporting Bugs

If you find issues during manual testing:

1. **Collect Information**:
   - Error message
   - Session ID
   - Deck name and card type
   - Steps to reproduce

2. **Check Logs**:
   ```bash
   # Check MCP server logs
   tail -f ~/.local/share/Claude/logs/mcp-server-anki-course-tutor.log
   ```

3. **Create Issue** with:
   - Description
   - Expected vs actual behavior
   - Reproduction steps
   - Logs (if available)
