## 1. Models
- [ ] 1.1 Add `ALL_IN_ONE` variant to CardType enum
- [ ] 1.2 Add `fields: dict[str, str] | None` field to Card dataclass
- [ ] 1.3 Add `all_in_one_type: str | None` field (KPRIM/MC/SC)
- [ ] 1.4 Update Card.__post_init__() validation for AllInOne

## 2. AnkiClient Integration
- [ ] 2.1 Add "All-in-One" note type mapping to ALL_IN_ONE CardType
- [ ] 2.2 Detect AllInOne variant type (KPRIM, MC, SC)
- [ ] 2.3 Extract multi-field values from AllInOne cards
- [ ] 2.4 Extract answer options for each variant
- [ ] 2.5 Add unit tests for AllInOne conversion (all variants)

## 3. Card Presentation
- [ ] 3.1 Update _present_card() to handle AllInOne variants
- [ ] 3.2 Format KPRIM with true/false statements
- [ ] 3.3 Format MC with multiple checkboxes
- [ ] 3.4 Format SC with single-choice radio buttons
- [ ] 3.5 Add tests for variant-specific display

## 4. Answer Evaluation
- [ ] 4.1 Implement KPRIM evaluation (partial credit: 0-4 points)
- [ ] 4.2 Implement MC evaluation (multiple options allowed)
- [ ] 4.3 Implement SC evaluation (single option required)
- [ ] 4.4 Apply whitespace/case normalization consistently
- [ ] 4.5 Add tests for all variant evaluations

## 5. Testing
- [ ] 5.1 Add AllInOne KPRIM card fixtures
- [ ] 5.2 Add AllInOne MC card fixtures
- [ ] 5.3 Add AllInOne SC card fixtures
- [ ] 5.4 Test correct answers for each variant
- [ ] 5.5 Test incorrect answers for each variant
- [ ] 5.6 Test partial credit for KPRIM
- [ ] 5.7 Verify all existing tests still pass

## 6. Documentation
- [ ] 6.1 Update README with AllInOne support details
- [ ] 6.2 Document KPRIM partial credit scoring
- [ ] 6.3 Update MANUAL_TESTING.md with AllInOne variants

## 7. Deployment
- [ ] 7.1 Commit all changes
- [ ] 7.2 Push to GitHub
- [ ] 7.3 Verify all tests pass on main
