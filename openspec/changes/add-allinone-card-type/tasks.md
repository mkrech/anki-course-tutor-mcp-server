```markdown
## 1. Models
- [x] 1.1 Add `ALL_IN_ONE` variant to CardType enum
- [x] 1.2 Add `fields: dict[str, str] | None` field to Card dataclass
- [x] 1.3 Add `all_in_one_type: str | None` field (KPRIM/MC/SC)
- [x] 1.4 Update Card.__post_init__() validation for AllInOne

## 2. AnkiClient Integration
- [x] 2.1 Add "All-in-One" note type mapping to ALL_IN_ONE CardType
- [x] 2.2 Detect AllInOne variant type (KPRIM, MC, SC)
- [x] 2.3 Extract multi-field values from AllInOne cards
- [x] 2.4 Extract answer options for each variant
- [x] 2.5 Add unit tests for AllInOne conversion (all variants)

## 3. Card Presentation
- [x] 3.1 Update _present_card() to handle AllInOne variants
- [x] 3.2 Format KPRIM with true/false statements
- [x] 3.3 Format MC with multiple checkboxes
- [x] 3.4 Format SC with single-choice radio buttons
- [x] 3.5 Add tests for variant-specific display

## 4. Answer Evaluation
- [x] 4.1 Implement KPRIM evaluation (partial credit: 0-4 points)
- [x] 4.2 Implement MC evaluation (multiple options allowed)
- [x] 4.3 Implement SC evaluation (single option required)
- [x] 4.4 Apply whitespace/case normalization consistently
- [x] 4.5 Add tests for all variant evaluations

## 5. Testing
- [x] 5.1 Add AllInOne KPRIM card fixtures
- [x] 5.2 Add AllInOne MC card fixtures
- [x] 5.3 Add AllInOne SC card fixtures
- [x] 5.4 Test correct answers for each variant
- [x] 5.5 Test incorrect answers for each variant
- [x] 5.6 Test partial credit for KPRIM
- [x] 5.7 Verify all existing tests still pass (101/101 ✅)

## 6. Refactoring: Remove MULTIPLE_CHOICE Redundancy
- [x] 6.1 Remove CardType.MULTIPLE_CHOICE from enum
- [x] 6.2 Replace Card.options with Card.fields (dict-based)
- [x] 6.3 Migrate all test fixtures to ALL_IN_ONE
- [x] 6.4 Update LearningEngine to route MC → evaluate_all_in_one()
- [x] 6.5 Add _convert_multiple_choice_to_all_in_one() migration

## 7. Documentation
- [ ] 7.1 Update README with AllInOne support details
- [ ] 7.2 Document KPRIM partial credit scoring
- [ ] 7.3 Update MANUAL_TESTING.md with AllInOne variants

## 8. Deployment
- [x] 8.1 Commit all changes (8384fa1)
- [ ] 8.2 Push to GitHub
- [ ] 8.3 Verify all tests pass on main (101/101 ✅)

```
