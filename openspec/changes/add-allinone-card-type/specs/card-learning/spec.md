## ADDED Requirements

### Requirement: AllInOne Card Type Support
The system SHALL support Anki's AllInOne card type with KPRIM, MC (multiple choice), and SC (single choice) variants.

#### Scenario: Present KPRIM AllInOne card
- **WHEN** presenting an AllInOne card of type KPRIM
- **THEN** system displays true/false statements for each option
- **AND** allows user to select true/false for each statement
- **AND** scoring is 0-4 points based on correct answers

#### Scenario: Present MC (Multiple Choice) AllInOne card
- **WHEN** presenting an AllInOne card of type MC
- **THEN** system displays multiple options as checkboxes
- **AND** allows selecting multiple correct answers
- **AND** requires all correct answers to be marked for full credit

#### Scenario: Present SC (Single Choice) AllInOne card
- **WHEN** presenting an AllInOne card of type SC
- **THEN** system displays options as radio buttons
- **AND** allows selecting exactly one answer
- **AND** requires exact match with correct option

#### Scenario: Evaluate KPRIM answer
- **WHEN** user submits answer for KPRIM card
- **THEN** system scores based on statements answered correctly
- **AND** awards 1 point per correct statement (max 4 points)
- **AND** converts score to correct/incorrect (≥3 = correct, <3 = incorrect)

#### Scenario: Evaluate MC answer
- **WHEN** user submits answer for MC card
- **THEN** system checks all selected options against correct answers
- **AND** requires all correct options selected AND no incorrect options
- **AND** marks correct only if all selections match exactly

#### Scenario: Evaluate SC answer
- **WHEN** user submits answer for SC card
- **THEN** system checks single selected option
- **AND** applies whitespace and case normalization
- **AND** marks correct if option matches answer

