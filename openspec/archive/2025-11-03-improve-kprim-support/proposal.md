# Proposal: Improve KPRIM/MC/SC Card Support

## Summary

Enhance AllInOne card type support (KPRIM, Multiple Choice, Single Choice) by properly extracting and displaying options, adding contextual hints in EXPLAIN mode, supporting flexible answer formats, and simplifying the user confirmation workflow.

## Problem Statement

The current implementation has several issues with KPRIM and other AllInOne card types:

1. **Options Not Displayed**: Card options (Q_1, Q_2, Q_3, etc.) are not extracted from card fields and shown to users
2. **No Learning Support**: Extra information and sources are not displayed during learning
3. **Rigid Answer Format**: Only accepts "1 1 0 1 0" format, not "RRFRF" or other common formats
4. **Confusing Workflow**: Users must confirm automatic evaluation instead of directly indicating if their answer was correct
5. **State Management Issue**: `get_current_state()` doesn't present cards properly, only shows generic state info

## Proposed Solution

### 1. Extract and Display Options
- Extract Q_1, Q_2, Q_3, Q_4, Q_5 fields from AllInOne cards
- Add `options` array to card presentation response
- Include `all_in_one_type` (KPRIM/MC/SC) for context

### 2. Add Contextual Hints (EXPLAIN Mode)
- Extract "Extra" and "Sources" fields from cards
- Display as `hint` in EXPLAIN mode only
- Help users learn while answering questions

### 3. Support Flexible Answer Formats
- Accept multiple formats: "1 1 0 1 0", "RRFRF", "11010", "R,R,F,R,F", "TTFTT"
- Normalize both user answer and expected answer
- Map R/T/Y → 1 (correct) and F/N → 0 (incorrect)

### 4. Simplify Confirmation Workflow
- Remove automatic evaluation display
- Show user answer and correct answer side-by-side
- Ask directly: "Was your answer correct?" instead of "Is this evaluation correct?"

### 5. Fix State Management
- Make `get_current_state()` call `_present_card()` when in PRESENTING_CARD or AWAITING_ANSWER state
- Ensure consistent card presentation across all code paths

## Impact

### Users
- ✅ Can see all answer options for KPRIM/MC/SC questions
- ✅ Get contextual hints while learning (EXPLAIN mode)
- ✅ Use natural answer formats (R/F, T/F, or numbers)
- ✅ Simpler, more intuitive confirmation process

### Developers
- ✅ Cleaner code with proper field extraction
- ✅ Better state management
- ✅ More flexible evaluation logic

## Implementation Details

See:
- `tasks.md` for implementation steps
- `design.md` for architectural decisions
- `specs/` for detailed requirements

## Risks & Mitigations

### Risk: Breaking existing answer formats
**Mitigation**: Normalize both user and expected answers, maintain backward compatibility

### Risk: Performance impact from field extraction
**Mitigation**: Extraction happens once during card import, minimal runtime impact

### Risk: VS Code MCP caching issues
**Mitigation**: Document requirement to use local development setup instead of git-based uvx installation

## Success Criteria

- [ ] All KPRIM card options display correctly
- [ ] Hints show in EXPLAIN mode, not in TEST mode
- [ ] Answer formats "RRFRF" and "11010" both work
- [ ] User confirmation workflow uses direct yes/no without evaluation confusion
- [ ] get_current_state() properly presents cards
- [ ] All existing tests pass
- [ ] Manual testing confirms improved UX

## Related Issues

None - this is a feature enhancement

## Timeline

- Implementation: Completed
- Testing: In progress
- Documentation: Needed
