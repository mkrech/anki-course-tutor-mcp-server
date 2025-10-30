## ADDED Requirements

### Requirement: AllInOne Note Type Mapping with Variant Detection
The AnkiClient SHALL recognize Anki's "All-in-One" note type and detect its KPRIM, MC, or SC variant.

#### Scenario: Detect KPRIM AllInOne note type
- **WHEN** AnkiClient imports cards with note type "All-in-One" and KPRIM structure
- **THEN** system recognizes the variant as "KPRIM"
- **AND** converts to CardType.ALL_IN_ONE with all_in_one_type="KPRIM"
- **AND** extracts true/false options and correct answers

#### Scenario: Detect MC AllInOne note type
- **WHEN** AnkiClient imports cards with note type "All-in-One" and multiple choice structure
- **THEN** system recognizes the variant as "MC"
- **AND** converts to CardType.ALL_IN_ONE with all_in_one_type="MC"
- **AND** extracts options and correct answer(s)

#### Scenario: Detect SC AllInOne note type
- **WHEN** AnkiClient imports cards with note type "All-in-One" and single choice structure
- **THEN** system recognizes the variant as "SC"
- **AND** converts to CardType.ALL_IN_ONE with all_in_one_type="SC"
- **AND** extracts options and single correct answer

#### Scenario: Extract AllInOne variant fields
- **WHEN** converting All-in-One note with variant-specific structure
- **THEN** system extracts all relevant fields
- **AND** stores as `fields: dict[str, str]`
- **AND** identifies correct option(s) for evaluation

#### Scenario: Fallback for unknown AllInOne structure
- **WHEN** All-in-One card has unexpected structure
- **THEN** system attempts to detect variant
- **AND** logs warning about unusual structure
- **AND** continues processing as best-effort conversion

