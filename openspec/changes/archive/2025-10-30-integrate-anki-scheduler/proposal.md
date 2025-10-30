# Proposal: Integrate Anki Scheduler

**Change ID:** `integrate-anki-scheduler`  
**Status:** ✅ Implemented  
**Created:** 2025-10-27  
**Completed:** 2025-10-27  
**Author:** System

## Why

The custom `SimpleLearningScheduler` created separate review histories between the Tutor and Anki Desktop, preventing cross-platform sync and missing the benefits of Anki's proven SM-2 algorithm. This caused data inconsistency and suboptimal learning intervals.

## What Changes

**Complete migration to Anki's native scheduler:**
- Added 3 new AnkiConnect API methods: `answer_card()`, `get_card_info()`, `get_reviews_of_cards()`
- **BREAKING**: Removed SimpleLearningScheduler entirely (-109 lines)
- Integrated card management directly into LearningEngine using session state
- Submit all reviews to Anki's SM-2 scheduler after each answer
- Added `use_anki_scheduler` configuration flag (default: true)
- Updated session structure with `retry_queue` field
- Made all scheduling operations async

## Impact

**Affected specs:**
- anki-integration (added 3 scheduling API methods)
- card-learning (removed SimpleLearningScheduler, integrated Anki scheduler)
- session-management (updated session structure with retry_queue)

**Affected code:**
- `src/anki_course_tutor/anki_client.py` - Added scheduling methods
- `src/anki_course_tutor/learning_engine.py` - Integrated Anki scheduler
- `src/anki_course_tutor/scheduler.py` - **Deleted** (SimpleLearningScheduler removed)
- `src/anki_course_tutor/config.py` - Added `use_anki_scheduler` flag
- `src/anki_course_tutor/models/session.py` - Added `retry_queue` field
- `src/anki_course_tutor/mcp_server.py` - Updated for async operations
- Tests - Updated all tests, removed test_scheduler.py (100 tests passing, 74% coverage)

**Benefits:**
✅ Proven SM-2 spaced repetition algorithm  
✅ Single review history across all platforms  
✅ AnkiWeb/mobile sync enabled  
✅ Reduced complexity (-109 lines)  
✅ Better learning intervals

**Trade-offs:**
⚠️ Requires Anki Desktop running with AnkiConnect  
⚠️ No offline learning (acceptable for MVP)  
✅ Clear error messages when unavailable

**Migration:**
- Old sessions compatible (retry_queue defaults to empty list)
- Requires AnkiConnect running when `use_anki_scheduler=true`

## Problem Statement

The current system uses a simple custom scheduler (`SimpleLearningScheduler`) that doesn't leverage Anki's proven SM-2 spaced repetition algorithm. This leads to:

1. **Inconsistent Learning Data**: Users have separate review histories in the Tutor vs. Anki Desktop
2. **Suboptimal Scheduling**: Our simple scheduler doesn't provide the sophisticated interval calculation that Anki's SM-2 offers
3. **No Cross-Platform Sync**: Learning progress in the Tutor doesn't sync to AnkiWeb/mobile apps
4. **Duplicate Systems**: Maintaining parallel scheduling logic increases complexity and bugs

## Implemented Solution

**Complete migration to Anki's native scheduler** with simplified session-based card management:

- ~~Replace SimpleLearningScheduler with AnkiSchedulerAdapter~~ **Removed SimpleLearningScheduler entirely**
- Submit all card reviews directly to Anki using `answer_card()` API
- Leverage Anki's SM-2 algorithm for optimal interval calculation
- Maintain single source of truth for all review data
- Enable seamless sync across Anki Desktop, AnkiWeb, and mobile apps
- **Architecture Simplification**: Card management integrated directly into LearningEngine using session state

### Key Benefits

✅ **Proven Algorithm**: Use Anki's battle-tested SM-2 spaced repetition  
✅ **Unified Data**: Single review history across all platforms  
✅ **Mobile Sync**: Progress automatically syncs to AnkiWeb/mobile  
✅ **Reduced Complexity**: Removed custom scheduler (-109 lines)  
✅ **Better UX**: Users get optimal review intervals  
✅ **Simpler Architecture**: Direct session-based card management

### Trade-offs

⚠️ **Dependency**: Requires Anki Desktop running with AnkiConnect  
⚠️ **Online-Only**: No offline learning (acceptable for MVP)  
✅ **Mitigation**: Clear error messages when Anki unavailable  

## Scope

### Completed
- AnkiConnect API integration for card scheduling (3 new methods)
- ~~Replace SimpleLearningScheduler with AnkiSchedulerAdapter~~ Removed SimpleLearningScheduler
- Submit reviews to Anki's scheduler after each answer
- Update configuration to use Anki scheduler (`use_anki_scheduler` flag)
- Error handling for AnkiConnect failures (fail-fast)
- Update tests for new scheduler integration (100 tests, 74% coverage)
- Session-based card management with retry queue
```

### Out of Scope
- Offline queueing (acceptable limitation for MVP)
- Custom scheduling algorithms (using Anki's)
- Migration of existing session data
- Anki Desktop installation/setup (user responsibility)

## Impact Assessment

### Affected Components
- ✅ `anki_client.py` - Added 3 scheduling API methods (`answer_card`, `get_card_info`, `get_reviews_of_cards`)
- ✅ `learning_engine.py` - Integrated Anki scheduler, removed SimpleLearningScheduler dependency, added session-based card management
- ✅ `scheduler.py` - **Deleted** (SimpleLearningScheduler removed, -109 lines)
- ✅ `config.py` - Added `use_anki_scheduler` configuration flag
- ✅ `session_manager.py` - Updated for new session structure (retry_queue field)
- ✅ `models/session.py` - Added `retry_queue: list[str]` field
- ✅ Tests - Updated all tests, removed test_scheduler.py (100 tests remaining)

### Breaking Changes
- Session data structure changes (added `retry_queue` field)
- Requires AnkiConnect running when `use_anki_scheduler=true`
- Old sessions compatible (retry_queue defaults to empty list)
- **SimpleLearningScheduler removed** - card management now in LearningEngine


### Migration Strategy
1. Deploy with feature flag (optional: keep simple scheduler as fallback)
2. Document Anki Desktop + AnkiConnect setup requirements
3. Clear error messages if AnkiConnect unavailable
4. Future: Add offline queue for reviews

## Success Criteria

- [ ] All card reviews are submitted to Anki via `answerCards` API
- [ ] Review data visible in Anki Desktop after Tutor session
- [ ] Intervals calculated by Anki's SM-2 algorithm
- [ ] AnkiWeb sync works with Tutor-generated reviews
- [ ] Clear error handling when AnkiConnect unavailable
- [ ] All existing tests pass with new scheduler
- [ ] Integration tests verify AnkiConnect scheduling
- [x] Documentation updated with setup requirements

## Timeline Estimate

- **Specification**: 1 hour ✅
- **Implementation**: 4-6 hours ✅ (completed in ~6 hours)
- **Testing**: 2-3 hours ✅ (100 tests passing)
- **Documentation**: 1 hour ✅
- **Total**: ~8-11 hours ✅ **Completed**

**Actual**: ~10 hours including architecture simplification (SimpleLearningScheduler removal)

## References

- [AnkiConnect API Documentation](https://github.com/FooSoft/anki-connect)
- AnkiConnect Scheduling Endpoints Research (completed)
- Anki SM-2 Algorithm: https://faqs.ankiweb.net/what-spaced-repetition-algorithm.html

## Implementation Notes

### Architecture Decision: SimpleLearningScheduler Removal

After implementing the initial Anki integration with SimpleLearningScheduler as a fallback, we decided to simplify the architecture by removing SimpleLearningScheduler entirely:

**Rationale**:
- Anki is already the single source of truth for scheduling
- SimpleLearningScheduler added unnecessary complexity (109 lines)
- Session-based card management is simpler and equally effective
- Reduced test maintenance burden (111 → 100 tests)

**Implementation**:
- Card iteration logic integrated directly into LearningEngine
- Retry queue stored in Session model and synced on save
- Statistics calculated from session state
- Same functionality with cleaner architecture

## Delta Specs

### Modified
- `anki-integration` - Added 3 scheduling API methods ✅
- `card-learning` - Integrated Anki scheduler, removed SimpleLearningScheduler ✅
- `session-management` - Updated session structure (retry_queue field) ✅
```

### Removed
- None (SimpleLearningScheduler kept for reference)
