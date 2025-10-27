# Implementation Tasks

## Phase 1: AnkiConnect API Extension ✅ COMPLETE
- [x] 1.1 Add `answer_card()` method to AnkiClient
- [x] 1.2 Add `get_card_info()` method to retrieve Anki card state
- [x] 1.3 Add `get_reviews_of_cards()` to fetch review history
- [x] 1.4 Add connection check and error handling
- [x] 1.5 Unit tests for new AnkiClient methods (8 new tests, all passing)

## Phase 2: Scheduler Adapter ⏭️ SKIPPED
- [~] 2.1-2.5 Skipped per design decision: Use AnkiClient directly instead of adapter pattern

## Phase 3: Learning Engine Integration ✅ COMPLETE
- [x] 3.1 Update `LearningEngine` to accept optional `anki_client` parameter
- [x] 3.2 Submit review to Anki after `confirm_evaluation()` (async)
- [x] 3.3 Map correctness to Anki ease values (correct=4, incorrect=1)
- [x] 3.4 Implement fail-fast error handling (return error to user if Anki fails)
- [x] 3.5 Update all tests to async and add 5 new Anki integration tests
- [x] 3.6 All 53 tests passing (32 learning_engine + 21 anki_client)

## Phase 4: Configuration ✅ COMPLETE
- [x] 4.1 Add `use_anki_scheduler` flag to config.yaml
- [x] 4.2 Update `AnkiConfig` dataclass with new field (default: True)
- [x] 4.3 Document AnkiConnect settings in README (connection, scheduler, ease mapping)
- [x] 4.4 Add troubleshooting section for AnkiConnect and scheduler issues
- [x] 4.5 Config validation test passed

## Phase 5: Session Management ✅ COMPLETE
- [x] 5.1 Add `_anki_client` global variable to mcp_server.py
- [x] 5.2 Update `initialize_managers()` to accept `use_anki_scheduler` parameter
- [x] 5.3 Create AnkiClient instance when scheduler enabled
- [x] 5.4 Pass AnkiClient to LearningEngine in `start_session()`
- [x] 5.5 Pass AnkiClient to LearningEngine in `resume_session()`
- [x] 5.6 Update `run_server()` to accept Config parameter
- [x] 5.7 Update `__main__.py` to pass config to run_server()
- [x] 5.8 Make `confirm_evaluation` tool async in MCP server
- [x] 5.9 All 56 tests passing (32 learning_engine + 21 anki_client + 3 mcp_server)

## Phase 6: Testing ✅ PARTIALLY COMPLETE
- [x] 6.1 Update unit tests for LearningEngine (32 tests passing, including 5 Anki integration tests)
- [x] 6.2 Update E2E tests with AnkiConnect mocks (3 tests passing)
- [~] 6.3 Add integration tests for scheduler adapter (SKIPPED - no adapter pattern used)
- [ ] 6.4 Test error scenarios (Anki offline, timeout) - Basic coverage exists
- [ ] 6.5 Verify AnkiWeb sync workflow (manual testing required)
- [x] 6.6 Remove personality system (simplified codebase, 9 tests removed, 112 tests now passing)

## Phase 7: Documentation ✅ COMPLETE
- [x] 7.1 Update README with AnkiConnect setup (already documented in Phase 4)
- [x] 7.2 Update MANUAL_TESTING.md (removed personality references, added Anki scheduler tests)
- [x] 7.3 Add troubleshooting guide for Anki connection (already in README Phase 4)
- [x] 7.4 Document ease value mapping (correct=4/incorrect=1, documented in README and code)
- [x] 7.5 Remove personality references from all documentation files
- [x] 7.6 Update test counts in README (100 tests)

## Phase 8: Cleanup ✅ COMPLETE
- [x] 8.1 Remove SimpleLearningScheduler (decision: simplify architecture, use session-based card management directly in LearningEngine)
- [x] 8.2 Remove unused scheduler imports (verified with ruff - all clear)
- [x] 8.3 Final validation and testing (100 tests passing, 74% coverage)
- [x] 8.4 Update CHANGELOG (completed)

## Testing Checklist
- [x] All unit tests pass (100 tests passing)
- [x] All integration tests pass (5 Anki scheduler integration tests)
- [ ] E2E test with real Anki Desktop (manual testing required)
- [ ] Verify reviews appear in Anki (manual testing required)
- [ ] Verify AnkiWeb sync works (manual testing required)
- [x] Test error handling (Anki offline) - Basic coverage exists
- [x] Test with different card types (Basic, Cloze, MC) - Covered in existing tests
- [x] Coverage remains above 70% (currently 74%)
