# Design: Improve KPRIM/MC/SC Card Support

## Architecture Overview

This change enhances the AllInOne card type handling in the learning engine without changing the core architecture. The system maintains its state machine pattern and asyncio-based design.

## Key Design Decisions

### 1. Field Extraction Pattern Matching

**Decision**: Use flexible pattern matching for Q_n fields

**Rationale**:
- Anki cards may use `Q_1` or `Q1` notation
- Need to handle variable number of options (3-5 typically)
- Pattern matching more robust than hardcoded field lists

**Implementation**:
```python
# Match Q_1, Q_2, etc (len >= 3) or Q1, Q2, etc (len == 2)
if key.startswith("Q") and (
    (len(key) >= 3 and key[1] == "_" and key[2:].isdigit())
    or (len(key) == 2 and key[1].isdigit())
):
```

**Alternatives Considered**:
- Hardcoded list of Q_1 through Q_5 - rejected (inflexible)
- Regex matching - rejected (overkill for simple pattern)

---

### 2. Answer Normalization Strategy

**Decision**: Normalize both user answer and expected answer to common format

**Rationale**:
- Users think in different formats (R/F is intuitive for German speakers)
- System stores answers as "1 1 0 1 0" format
- Normalization allows comparison while maintaining storage format

**Implementation**:
```python
def _normalize_kprim_answer(self, answer: str) -> list[str]:
    """Normalize to ['1', '0', ...] regardless of input format."""
    cleaned = answer.replace(",", "").replace(" ", "").upper()
    return ['1' if c in 'RTY1' else '0' for c in cleaned]
```

**Character Mappings**:
- `R` (Richtig) → `1`
- `F` (Falsch) → `0`
- `T` (True) → `1`
- `N` (No) / `F` (False) → `0`
- `Y` (Yes) → `1`
- `1` → `1`
- `0` → `0`

**Alternatives Considered**:
- Force users to specific format - rejected (poor UX)
- Store normalized format in card - rejected (breaks existing data)

---

### 3. Hint Display Conditional Logic

**Decision**: Only show hints in EXPLAIN mode, not TEST mode

**Rationale**:
- EXPLAIN mode is for learning with support
- TEST mode is for self-assessment without aids
- Hints should help learning, not give away answers in tests

**Implementation**:
```python
if self.session.mode == LearningMode.EXPLAIN and card.fields:
    hints = []
    if "Sources" in card.fields:
        hints.append(f"Sources: {card.fields['Sources']}")
    for key in ["Extra", "Extra 1", "Extra 2", ...]:
        if key in card.fields:
            hints.append(f"{key}: {card.fields[key]}")
```

**Alternatives Considered**:
- Always show hints - rejected (defeats purpose of TEST mode)
- Make hints optional per-card - rejected (too complex)

---

### 4. Evaluation Threshold

**Decision**: Maintain 60% threshold (4 out of 5 correct)

**Rationale**:
- KPRIM questions are inherently harder than MC/SC
- 100% threshold would be too strict
- 60% = minimum competency (4/5 for 5 questions)
- Aligns with existing test

**Implementation**:
```python
correct_count = sum(1 for u, e in zip(user_normalized, expected_normalized) if u == e)
total_count = len(expected_normalized)
threshold = 0.6
is_correct = correct_count >= (total_count * threshold)
```

**Alternatives Considered**:
- 100% threshold - rejected (too strict for KPRIM)
- 50% threshold - rejected (too lenient)
- Configurable threshold - deferred (may add later)

---

### 5. State Management Fix

**Decision**: Make `get_current_state()` delegate to `_present_card()` for card presentation states

**Rationale**:
- DRY principle: don't duplicate presentation logic
- `_present_card()` is the single source of truth for card data
- Ensures consistency across all code paths (start, next, get_state)

**Implementation**:
```python
def get_current_state(self) -> dict[str, Any]:
    if self.state in (State.PRESENTING_CARD, State.AWAITING_ANSWER):
        return self._present_card()  # Delegate to presentation logic
    # ... other states
```

**Alternatives Considered**:
- Duplicate presentation logic in get_current_state - rejected (violates DRY)
- Always call _present_card for any state - rejected (wrong for other states)

---

### 6. Confirmation Workflow Simplification

**Decision**: Ask "Was your answer correct?" instead of "Confirm evaluation"

**Rationale**:
- Users found automatic evaluation confusing ("confirm if evaluation is correct")
- Direct question is clearer: you answered X, correct is Y, were you right?
- Reduces cognitive load
- Aligns with self-assessment learning philosophy

**Before**:
```
System automatically evaluates → Shows evaluation → User confirms/overrides
```

**After**:
```
Show user answer & correct answer → User directly indicates if correct
```

**Implementation**:
```python
return {
    "user_answer": answer,
    "correct_answer": expected_answer,
    "message": f"You answered: '{answer}'\nCorrect answer: '{expected_answer}'\n\nWas your answer correct? (yes/no)"
}
```

**Alternatives Considered**:
- Keep automatic evaluation with override - rejected (confusing UX)
- Fully automatic evaluation with no user input - rejected (loses learning opportunity)

---

## Data Flow

### Card Import & Conversion
```
Anki Deck 
  → AnkiConnect API
  → AnkiClient._convert_all_in_one()
  → Card(fields={Q_1, Q_2, ..., Extra, Sources})
  → SessionManager storage
```

### Card Presentation
```
get_next_card()
  → LearningEngine.start() or get_current_state()
  → _present_card()
  → Extract options (Q_1 to Q_5)
  → Extract hints (Extra, Sources) if EXPLAIN mode
  → Return {question, options, hint, all_in_one_type}
```

### Answer Evaluation
```
submit_answer("RRFRF")
  → _normalize_kprim_answer("RRFRF") → ['1','1','0','1','0']
  → _normalize_kprim_answer("1 1 0 1 0") → ['1','1','0','1','0']
  → Compare normalized answers
  → Calculate score (4/5 = 80% > 60% threshold)
  → Return {user_answer, correct_answer, message}
```

### Confirmation
```
confirm_evaluation(is_correct=True/False)
  → Update answer history
  → Schedule next card
  → Transition to next state
```

---

## Performance Considerations

### Field Extraction
- **Impact**: Minimal - O(n) where n = number of fields (~10-20)
- **Frequency**: Once per card presentation
- **Optimization**: Pattern matching is fast, no regex compilation overhead

### Answer Normalization
- **Impact**: Negligible - O(m) where m = answer length (~5-10 chars)
- **Frequency**: Once per answer submission
- **Optimization**: Simple character mapping, no complex parsing

### Hint Generation
- **Impact**: Minimal - O(n) field iteration
- **Frequency**: Only in EXPLAIN mode
- **Optimization**: Early return if mode != EXPLAIN

---

## Error Handling

### Missing Fields
- **Scenario**: Card has Q_1, Q_2, Q_3 but no Q_4, Q_5
- **Handling**: Pattern matching only extracts present fields
- **User Impact**: Shorter question list (3 options instead of 5)
- **Mitigation**: Card validation logs warning at import time

### Invalid Answer Format
- **Scenario**: User enters "ABC" instead of "RRF"
- **Handling**: Normalization produces non-standard characters
- **User Impact**: Evaluation will fail (mismatch)
- **Mitigation**: Could add validation pre-normalization (future enhancement)

### State Inconsistencies
- **Scenario**: get_current_state() called in unexpected state
- **Handling**: State machine guards in LearningEngine
- **User Impact**: Appropriate error message
- **Mitigation**: Comprehensive state transition logic

---

## Security Considerations

### Input Validation
- User answers are strings, normalized before comparison
- No code execution or injection vectors
- Field extraction uses safe string operations (no eval/exec)

### Data Privacy
- Session data stored locally in data/sessions/
- No external API calls for evaluation
- Anki data accessed via local AnkiConnect (localhost)

---

## Testing Strategy

### Unit Tests
```python
# Test normalization
assert _normalize_kprim_answer("RRFRF") == ['1','1','0','1','0']
assert _normalize_kprim_answer("11010") == ['1','1','0','1','0']
assert _normalize_kprim_answer("R,R,F,R,F") == ['1','1','0','1','0']

# Test options extraction
card = Card(fields={"Q_1": "A", "Q_2": "B", "Q1": "C"})
options = extract_options(card)
assert options == {"Q_1": "A", "Q_2": "B", "Q1": "C"}

# Test hint extraction
card = Card(fields={"Sources": "p.5", "Extra": "Hint"})
hint = extract_hint(card, LearningMode.EXPLAIN)
assert "Sources: p.5" in hint
```

### Integration Tests
```python
# Test full workflow
session = start_session(deck="PGM::02_Bn1", mode="explain")
card = get_next_card()
assert "options" in card
assert "hint" in card  # EXPLAIN mode

submit_answer("RRFRF")  # Should normalize to 11010
confirm_evaluation(is_correct=True)
```

### Manual Testing
- ✅ Real Anki deck with KPRIM questions
- ✅ Various answer formats
- ✅ EXPLAIN vs TEST mode hint display
- ✅ Full learning session workflow

---

## Backward Compatibility

### Breaking Changes
- None - all changes are additive or internal

### API Changes
- `_present_card()` response now includes `options`, `all_in_one_type`, `hint` (new fields)
- `submit_answer()` response format changed (removed automatic evaluation)
- Both changes are backward compatible (clients can ignore new fields)

### Data Migration
- No migration needed
- Existing session data remains valid
- New fields populated on next card load

---

## Future Enhancements

### Potential Improvements
1. **Configurable Thresholds**: Per-deck or per-card-type thresholds
2. **Answer Validation**: Pre-normalization validation with helpful error messages
3. **Custom Separators**: Support for other answer formats (e.g., "R/R/F/R/F")
4. **Partial Credit**: More nuanced scoring (currently binary correct/incorrect)
5. **Analytics**: Track which answer formats users prefer

### Extension Points
- `_normalize_kprim_answer()` can be extended with more mappings
- Hint extraction can support additional field patterns
- Options extraction can handle other naming conventions

---

## References

- State Machine Pattern: `src/anki_course_tutor/learning_engine.py` class `State`
- Card Model: `src/anki_course_tutor/models/card.py`
- Anki Integration: `src/anki_course_tutor/anki_client.py`
- MCP Tools: `src/anki_course_tutor/mcp_server.py`
