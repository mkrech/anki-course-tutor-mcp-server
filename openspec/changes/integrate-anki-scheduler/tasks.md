# Implementation Tasks

## Phase 1: AnkiConnect API Extension
- [ ] 1.1 Add `answer_card()` method to AnkiClient
- [ ] 1.2 Add `get_card_info()` method to retrieve Anki card state
- [ ] 1.3 Add `get_reviews_of_cards()` to fetch review history
- [ ] 1.4 Add connection check and error handling
- [ ] 1.5 Unit tests for new AnkiClient methods

## Phase 2: Scheduler Adapter
- [ ] 2.1 Create `AnkiSchedulerAdapter` class
- [ ] 2.2 Implement card state retrieval from Anki
- [ ] 2.3 Implement review submission to Anki
- [ ] 2.4 Implement error handling and fallbacks
- [ ] 2.5 Unit tests for AnkiSchedulerAdapter

## Phase 3: Learning Engine Integration
- [ ] 3.1 Update `LearningEngine` to use AnkiSchedulerAdapter
- [ ] 3.2 Submit review to Anki after `confirm_evaluation()`
- [ ] 3.3 Map correctness to Anki ease values (1-4)
- [ ] 3.4 Remove SimpleLearningScheduler dependencies
- [ ] 3.5 Update error messages for Anki failures

## Phase 4: Configuration
- [ ] 4.1 Update config schema for Anki scheduler
- [ ] 4.2 Add AnkiConnect settings (URL, timeout)
- [ ] 4.3 Document configuration requirements

## Phase 5: Session Management
- [ ] 5.1 Update Session model (remove local interval tracking)
- [ ] 5.2 Update SessionManager to use Anki scheduler
- [ ] 5.3 Simplify session state (Anki handles scheduling)

## Phase 6: Testing
- [ ] 6.1 Update unit tests for LearningEngine
- [ ] 6.2 Update E2E tests with AnkiConnect mocks
- [ ] 6.3 Add integration tests for scheduler adapter
- [ ] 6.4 Test error scenarios (Anki offline, timeout)
- [ ] 6.5 Verify AnkiWeb sync workflow

## Phase 7: Documentation
- [ ] 7.1 Update README with AnkiConnect setup
- [ ] 7.2 Update MANUAL_TESTING.md
- [ ] 7.3 Add troubleshooting guide for Anki connection
- [ ] 7.4 Document ease value mapping (correct/incorrect → 1-4)

## Phase 8: Cleanup
- [ ] 8.1 Archive SimpleLearningScheduler (move to legacy/)
- [ ] 8.2 Remove unused scheduler imports
- [ ] 8.3 Final validation and testing
- [ ] 8.4 Update CHANGELOG

## Testing Checklist
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] E2E test with real Anki Desktop
- [ ] Verify reviews appear in Anki
- [ ] Verify AnkiWeb sync works
- [ ] Test error handling (Anki offline)
- [ ] Test with different card types (Basic, Cloze, MC)
- [ ] Coverage remains above 80%
