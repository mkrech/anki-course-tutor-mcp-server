# Tasks: Improve KPRIM/MC/SC Card Support

## Implementation Tasks

### Task 1: Extract Card Options
**File**: `src/anki_course_tutor/learning_engine.py`

- [x] Implemented option extraction logic in `_present_card()`
- [x] Pattern matching for Q_1, Q_2, etc. and Q1, Q2, etc.
- [x] Added options array to response
- [x] Added all_in_one_type field

**Changes**:
- Modified `_present_card()` to extract options from card fields
- Pattern matching for `Q_1`, `Q_2`, `Q_3`, `Q_4`, `Q_5` fields
- Added `options` array to response
- Added `all_in_one_type` field (KPRIM/MC/SC)

**Code**:
```python
# Extract options for AllInOne cards
if card.card_type == CardType.ALL_IN_ONE and card.fields:
    options = {}
    for key, value in card.fields.items():
        # Match Q_1, Q_2, etc (len >= 3) or Q1, Q2, etc (len == 2)
        if key.startswith("Q") and (
            (len(key) >= 3 and key[1] == "_" and key[2:].isdigit())
            or (len(key) == 2 and key[1].isdigit())
        ):
            options[key] = value
    
    result["options"] = dict(sorted(options.items()))
    result["all_in_one_type"] = card.metadata.get("all_in_one_type", "unknown")
```

---

### Task 2: Add Contextual Hints (EXPLAIN Mode)
**File**: `src/anki_course_tutor/learning_engine.py`

- [x] Extract "Extra" and "Sources" fields in EXPLAIN mode
- [x] Add hint field to card presentation
- [x] Ensure hints only show in EXPLAIN mode, not TEST mode

**Changes**:
- Extract "Extra" and "Sources" fields in EXPLAIN mode
- Add `hint` field to card presentation
- Only show hints in EXPLAIN mode, not TEST mode

**Code**:
```python
# Add hints in EXPLAIN mode
if self.session.mode == LearningMode.EXPLAIN and card.fields:
    hints = []
    if "Sources" in card.fields and card.fields["Sources"]:
        hints.append(f"Sources: {card.fields['Sources']}")
    for key, value in card.fields.items():
        if key.startswith("Extra") and value:
            hints.append(f"{key}: {value}")
    if hints:
        result["hint"] = " | ".join(hints)
```

---

### Task 3: Support Flexible Answer Formats
**File**: `src/anki_course_tutor/learning_engine.py`

- [x] Created `_normalize_kprim_answer()` method
- [x] Accept R/F, T/F, Y/N, 1/0, with various separators
- [x] Modified `evaluate_all_in_one()` to normalize both answers
- [x] Maintain 60% threshold (4/5 correct)

**Changes**:
- Created `_normalize_kprim_answer()` method
- Accept R/F, T/F, Y/N, 1/0, with various separators
- Modified `evaluate_all_in_one()` to normalize both answers
- Maintain 60% threshold (4/5 correct)

**Code**:
```python
def _normalize_kprim_answer(self, answer: str) -> list[str]:
    """Normalize KPRIM answer to list of '1' and '0'."""
    # Remove common separators
    cleaned = answer.replace(",", "").replace(" ", "").replace(";", "").upper()
    
    # Convert each character: R/T/Y/1 -> '1', F/N/0 -> '0'
    result = []
    for char in cleaned:
        if char in "RTY1":
            result.append("1")
        elif char in "FN0":
            result.append("0")
        else:
            # Keep as-is if unrecognized (will fail comparison)
            result.append(char)
    
    return result
```

---

### Task 4: Simplify Confirmation Workflow
**File**: `src/anki_course_tutor/learning_engine.py`

- [x] Removed automatic evaluation display from `submit_answer()`
- [x] Changed prompt from "Is this evaluation correct?" to "Was your answer correct?"
- [x] Direct yes/no question instead of evaluation confirmation

**Changes**:
- Removed automatic evaluation display from `submit_answer()`
- Changed prompt from "Is this evaluation correct?" to "Was your answer correct?"
- Direct yes/no question instead of evaluation confirmation

**Before**:
```python
# Old flow: automatic evaluation + confirmation
return {
    "status": "awaiting_review",
    "evaluation": evaluation_result,
    "message": "Please confirm if this evaluation is correct..."
}
```

**After**:
```python
# New flow: direct self-evaluation
return {
    "status": "awaiting_review",
    "user_answer": answer,
    "correct_answer": expected_answer,
    "message": f"You answered: '{answer}'\nCorrect answer: '{expected_answer}'\n\nWas your answer correct? (yes/no)"
}
```

---

### Task 5: Fix State Management
**File**: `src/anki_course_tutor/learning_engine.py`

- [x] Modified `get_current_state()` to call `_present_card()` when presenting
- [x] Ensures consistent card presentation across code paths

**Changes**:
- Modified `get_current_state()` to call `_present_card()` when presenting
- Ensures consistent card presentation across code paths

**Code**:
```python
def get_current_state(self) -> dict[str, Any]:
    """Get current session state."""
    if self.state in (State.PRESENTING_CARD, State.AWAITING_ANSWER):
        return self._present_card()
    
    # ... other states
```

---

### Task 6: Code Cleanup
**Files**: 
- `src/anki_course_tutor/anki_client.py`
- `src/anki_course_tutor/mcp_server.py`
- Various test files

- [x] Removed debug logging from `_convert_all_in_one()`
- [x] Removed debug logging from `get_next_card()`
- [x] Deleted temporary test files (test_card_fields.py, test_learning_engine.py, test_converter.py, debug_card.py)

**Changes**:
- Removed debug logging from `_convert_all_in_one()`
- Removed debug logging from `get_next_card()`
- Deleted temporary test files:
  - `test_card_fields.py`
  - `test_learning_engine.py` (standalone test script)
  - `test_converter.py`
  - `debug_card.py`

---

### Task 7: Relaxed Card Validation
**File**: `src/anki_course_tutor/models/card.py`

- [x] Changed AllInOne card validation from error to warning
- [x] Allows cards with missing optional fields (Q_4, Q_5, etc.)

**Changes**:
- Changed AllInOne card validation from error to warning
- Allows cards with missing optional fields (Q_4, Q_5, etc.)

**Before**:
```python
if self.card_type == CardType.ALL_IN_ONE:
    required = {"Question", "QType", "Q_1", "Q_2", "Q_3", "Q_4", "Q_5"}
    missing = required - set(self.fields.keys())
    if missing:
        raise ValueError(f"AllInOne card missing required fields: {missing}")
```

**After**:
```python
if self.card_type == CardType.ALL_IN_ONE:
    recommended = {"Question", "QType", "Q_1", "Q_2", "Q_3"}
    missing = recommended - set(self.fields.keys())
    if missing:
        logger.warning(f"AllInOne card missing recommended fields: {missing}")
```

---

### Task 8: Documentation
**Files**: 
- `.github/prompts/learning-workflow.prompt.md`
- `openspec/changes/improve-kprim-support/`

- [x] Created learning workflow prompt file
- [x] Created OpenSpec proposal.md
- [x] Created OpenSpec tasks.md
- [x] Created OpenSpec design.md
- [x] Created OpenSpec specs/card-learning/spec.md
- [x] Update README.md with new answer format examples
- [x] Add usage examples to documentation

---

### Task 9: Testing

- [x] Manual end-to-end test (100% accuracy)
- [x] Verified options display correctly
- [x] Verified hint display in EXPLAIN mode
- [x] Verified answer format normalization (RRFRF, 11010)
- [x] Verified simplified confirmation workflow
- [x] Add unit tests for `_normalize_kprim_answer()` (5 tests)
- [x] Add unit tests for options extraction (2 tests)
- [x] Add integration tests for full workflow (3 tests)
- [x] Update existing tests for new response format (3 tests updated)

---

## Dependencies

- No external dependencies added
- All changes use existing libraries (Python 3.13 stdlib)

## Testing Plan

1. **Unit Tests**:
   - Test `_normalize_kprim_answer()` with various formats
   - Test options extraction with different Q_n patterns
   - Test hint extraction from Extra/Sources fields

2. **Integration Tests**:
   - Test full learning flow with KPRIM cards
   - Test EXPLAIN vs TEST mode hint display
   - Test answer evaluation with normalized formats

3. **Manual Testing**:
   - ✅ Verify options display in real Anki deck
   - ✅ Test all answer formats: RRFRF, 11010, TTFTT, etc.
   - ✅ Confirm workflow simplification UX

## Rollout

- [x] Implement all code changes
- [x] Test manually with real Anki deck
- [x] Create proposal.md
- [x] Create tasks.md  
- [x] Create design.md
- [x] Create specs/card-learning/spec.md
- [x] Validate with `openspec validate improve-kprim-support --strict`
- [x] Add comprehensive unit/integration tests (10 new tests, all passing)
- [x] Update README.md with examples
- [ ] Commit and tag release
