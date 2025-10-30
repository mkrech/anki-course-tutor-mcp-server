# Add AllInOne Card Type Support

## Why
AllInOne is a popular Anki card type that provides flexible question-answer layouts supporting multiple choice variants (KPRIM, MC, SC). Many users have AllInOne decks and expect the Tutor to handle them seamlessly alongside Basic, Cloze, and Multiple Choice cards.

## What Changes
- **New CardType**: Add `ALL_IN_ONE = "all_in_one"` to CardType enum
- **AllInOne Variants**: Support KPRIM (K), MC (single/multiple choice), SC (single choice) subtypes
- **Card Model**: Add `fields: dict[str, str]` and `all_in_one_type: str` to Card for multi-field and variant tracking
- **AnkiClient**: Map Anki's "All-in-One" note type and detect variant (KPRIM/MC/SC)
- **Card Converter**: Extract variants and answer options from AllInOne structure
- **LearningEngine**: Implement answer evaluation for each AllInOne variant (KPRIM: partial credit, MC: multiple options, SC: single option)
- **Tests**: Add comprehensive AllInOne test coverage for all variants

## Impact
**Affected specs:**
- card-learning (new card type variants)
- anki-integration (updated note type mapping with variant detection)

**Affected code:**
- `src/anki_course_tutor/models/card.py` - Add CardType.ALL_IN_ONE, fields, and all_in_one_type fields
- `src/anki_course_tutor/anki_client.py` - Add "All-in-One" note type mapping and variant detection
- `src/anki_course_tutor/learning_engine.py` - Add answer evaluation for KPRIM, MC, SC subtypes
- Tests - Add tests for each AllInOne variant

**Benefits:**
✅ Support for popular AllInOne Anki card type with all variants  
✅ KPRIM support (true/false for each statement, partial credit)  
✅ MC support (multiple correct answers possible)  
✅ SC support (single correct answer)  
✅ Expanded deck compatibility  
✅ No breaking changes to existing card types

**Trade-offs:**
- KPRIM evaluation requires understanding partial credit scoring (0-4 points)
- MC/SC use same logic as Basic (normalized matching)
