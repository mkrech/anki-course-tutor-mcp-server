# Add end_session Hint After Completion

## Why
After completing all cards in a session, users received stats but no guidance on what to do next. The session remained in `SESSION_COMPLETE` state without clear indication that `end_session` should be called to properly finish.

## What Changes
- Updated completion message to include hint: "Call end_session to finish."
- Added emoji for positive reinforcement: 🎉
- Improved user experience by guiding to next action

## Impact
**Affected specs:**
- card-learning (session completion flow)

**Affected code:**
- `src/anki_course_tutor/learning_engine.py` - Updated `_next_card()` completion message

**Benefits:**
- ✅ Clear guidance for users on next action
- ✅ Better UX with explicit instruction
- ✅ Encourages proper session cleanup

**Trade-offs:**
- None - purely additive UX improvement
