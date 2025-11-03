# card-learning Delta Specification

## ADDED Requirements

### Requirement: AllInOne Card Options Display
The system SHALL extract and display answer options (Q_1 through Q_5) for AllInOne card types (KPRIM, Multiple Choice, Single Choice).

#### Scenario: Display KPRIM options
- **WHEN** system presents a KPRIM card with fields Q_1 through Q_5
- **THEN** displays all five options in the card presentation
- **AND** includes "options" field in response with sorted option dict
- **AND** includes "all_in_one_type" field indicating "KPRIM"

#### Scenario: Display variable option count
- **WHEN** system presents AllInOne card with only Q_1, Q_2, Q_3
- **THEN** displays three options
- **AND** options dict contains only present fields

#### Scenario: Support Q_n and Qn formats
- **WHEN** card uses Q_1, Q_2 notation or Q1, Q2 notation
- **THEN** extracts both formats correctly
- **AND** includes all matching fields in options

### Requirement: Contextual Hints in EXPLAIN Mode
The system SHALL display contextual learning hints from Extra and Sources fields when in EXPLAIN mode.

#### Scenario: Show hints in EXPLAIN mode
- **WHEN** system presents card in EXPLAIN mode
- **AND** card has "Sources" and "Extra" fields
- **THEN** displays hint combining both fields
- **AND** formats as "Sources: <value> | Extra: <value>"

#### Scenario: Hide hints in TEST mode
- **WHEN** system presents card in TEST mode
- **AND** card has "Sources" and "Extra" fields
- **THEN** does NOT include hint field in response
- **AND** user must answer without additional context

#### Scenario: Multiple Extra fields
- **WHEN** card has "Extra", "Extra 1", "Extra 2" fields
- **THEN** concatenates all Extra fields in hint
- **AND** separates with " | " delimiter

### Requirement: Flexible Answer Format Normalization
The system SHALL accept multiple answer formats for KPRIM/AllInOne questions and normalize them for comparison.

#### Scenario: Accept R/F format (German)
- **WHEN** user answers "RRFRF" for KPRIM question
- **THEN** normalizes to ['1', '1', '0', '1', '0']
- **AND** compares against normalized expected answer
- **AND** evaluates as correct if normalized forms match

#### Scenario: Accept T/F format (English)
- **WHEN** user answers "TTFTT"
- **THEN** normalizes to ['1', '1', '0', '1', '1']
- **AND** uses same comparison logic

#### Scenario: Accept numeric format
- **WHEN** user answers "11010" or "1,1,0,1,0" or "1 1 0 1 0"
- **THEN** normalizes to ['1', '1', '0', '1', '0']
- **AND** strips separators (comma, space, semicolon)

#### Scenario: Case insensitive normalization
- **WHEN** user answers "rrfrf" or "RrFrF"
- **THEN** normalizes to ['1', '1', '0', '1', '0']
- **AND** converts to uppercase before mapping

#### Scenario: Character mapping
- **WHEN** normalizing answer
- **THEN** maps R/T/Y/1 → '1' (correct)
- **AND** maps F/N/0 → '0' (incorrect)
- **AND** preserves any unrecognized characters (will fail comparison)

## MODIFIED Requirements

### Requirement: Answer Evaluation with User Review
The system SHALL show user answer and correct answer side-by-side, then ask user directly if their answer was correct.

#### Scenario: User self-evaluates correct answer
- **WHEN** user submits answer "RRFRF"
- **THEN** system displays "You answered: 'RRFRF'"
- **AND** displays "Correct answer: '1 1 0 1 0'"
- **AND** asks "Was your answer correct? (yes/no)"
- **AND** does NOT perform automatic evaluation display

#### Scenario: User confirms correct
- **WHEN** user answers "yes" to confirmation
- **THEN** system marks card as correct
- **AND** increments correct count
- **AND** moves to next card

#### Scenario: User confirms incorrect
- **WHEN** user answers "no" to confirmation
- **THEN** system marks card as incorrect
- **AND** adds card to retry queue
- **AND** increments incorrect count

#### Scenario: User requests explanation (EXPLAIN mode)
- **WHEN** user is in EXPLAIN mode and answers incorrectly
- **THEN** system provides AI tutor explanation
- **AND** proceeds to next card after explanation

### Requirement: AllInOne Evaluation Threshold
The system SHALL use 60% threshold for KPRIM/AllInOne card evaluation.

#### Scenario: KPRIM partial credit (4 of 5 correct)
- **WHEN** user answers KPRIM with 5 options
- **AND** gets 4 out of 5 correct
- **THEN** evaluation shows 80% score (4/5)
- **AND** passes 60% threshold
- **AND** user sees comparison to confirm

#### Scenario: KPRIM below threshold (2 of 5 correct)
- **WHEN** user gets 2 out of 5 correct
- **THEN** evaluation shows 40% score (2/5)
- **AND** fails 60% threshold
- **AND** user sees comparison to determine correctness

### Requirement: Card Presentation State Management
The system SHALL delegate card presentation to _present_card() method when in PRESENTING_CARD or AWAITING_ANSWER state.

#### Scenario: get_current_state during presentation
- **WHEN** get_current_state() is called
- **AND** state is PRESENTING_CARD or AWAITING_ANSWER
- **THEN** returns result from _present_card() method
- **AND** includes all card data (question, options, hint, type)
- **AND** ensures consistency across all code paths

#### Scenario: Consistent card data
- **WHEN** user calls get_next_card() or get_current_state()
- **THEN** both return same card presentation structure
- **AND** both include options field for AllInOne cards
- **AND** both include hint field in EXPLAIN mode
