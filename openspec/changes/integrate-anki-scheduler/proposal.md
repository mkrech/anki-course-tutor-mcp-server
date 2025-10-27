# Proposal: Integrate Anki Scheduler

**Change ID:** `integrate-anki-scheduler`  
**Status:** Draft  
**Created:** 2025-10-27  
**Author:** System

## Problem Statement

The current system uses a simple custom scheduler (`SimpleLearningScheduler`) that doesn't leverage Anki's proven SM-2 spaced repetition algorithm. This leads to:

1. **Inconsistent Learning Data**: Users have separate review histories in the Tutor vs. Anki Desktop
2. **Suboptimal Scheduling**: Our simple scheduler doesn't provide the sophisticated interval calculation that Anki's SM-2 offers
3. **No Cross-Platform Sync**: Learning progress in the Tutor doesn't sync to AnkiWeb/mobile apps
4. **Duplicate Systems**: Maintaining parallel scheduling logic increases complexity and bugs

## Proposed Solution

**Complete migration to Anki's native scheduler** by integrating with AnkiConnect's scheduling APIs:

- Replace `SimpleLearningScheduler` with `AnkiSchedulerAdapter` that uses AnkiConnect APIs
- Submit all card reviews directly to Anki using `answerCards` API
- Leverage Anki's SM-2 algorithm for optimal interval calculation
- Maintain single source of truth for all review data
- Enable seamless sync across Anki Desktop, AnkiWeb, and mobile apps

### Key Benefits

✅ **Proven Algorithm**: Use Anki's battle-tested SM-2 spaced repetition  
✅ **Unified Data**: Single review history across all platforms  
✅ **Mobile Sync**: Progress automatically syncs to AnkiWeb/mobile  
✅ **Reduced Complexity**: Remove custom scheduler maintenance  
✅ **Better UX**: Users get optimal review intervals  

### Trade-offs

⚠️ **Dependency**: Requires Anki Desktop running with AnkiConnect  
⚠️ **Online-Only**: No offline learning (could add later with queue)  
✅ **Mitigation**: Clear error messages when Anki unavailable  

## Scope

### In Scope
- AnkiConnect API integration for card scheduling
- Replace SimpleLearningScheduler with AnkiSchedulerAdapter
- Submit reviews to Anki's scheduler after each answer
- Update configuration to use Anki scheduler
- Error handling for AnkiConnect failures
- Update tests for new scheduler integration

### Out of Scope
- Offline queueing (future enhancement)
- Custom scheduling algorithms (using Anki's)
- Migration of existing session data
- Anki Desktop installation/setup (user responsibility)

## Impact Assessment

### Affected Components
- `anki_client.py` - Add scheduling API methods
- `learning_engine.py` - Integrate scheduler after answer confirmation
- `scheduler.py` - Archive SimpleLearningScheduler (keep for reference)
- `config.py` - Scheduler configuration
- `session_manager.py` - Remove scheduler dependency
- Tests - Update mocks and integration tests

### Breaking Changes
- Session data structure changes (no local interval tracking needed)
- Requires AnkiConnect running for all learning sessions
- Old sessions may not resume correctly (acceptable for alpha)

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
- [ ] Documentation updated with setup requirements

## Timeline Estimate

- **Specification**: 1 hour
- **Implementation**: 4-6 hours
- **Testing**: 2-3 hours
- **Documentation**: 1 hour
- **Total**: ~8-11 hours

## References

- [AnkiConnect API Documentation](https://github.com/FooSoft/anki-connect)
- AnkiConnect Scheduling Endpoints Research (completed)
- Anki SM-2 Algorithm: https://faqs.ankiweb.net/what-spaced-repetition-algorithm.html

## Delta Specs

### Modified
- `anki-integration` - Add scheduling API methods
- `card-learning` - Integrate Anki scheduler
- `session-management` - Update session lifecycle

### Removed
- None (SimpleLearningScheduler kept for reference)
