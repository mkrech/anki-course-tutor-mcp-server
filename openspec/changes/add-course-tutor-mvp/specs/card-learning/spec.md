## ADDED Requirements

### Requirement: Card Type Support
The system SHALL support Basic, Cloze, and Multiple Choice card types with appropriate presentation and evaluation.

#### Scenario: Present Basic card
- **WHEN** system presents a Basic card
- **THEN** displays question text
- **AND** waits for user's free-form answer

#### Scenario: Present Cloze card
- **WHEN** system presents a Cloze card
- **THEN** displays text with {{c1::deletion}} markers removed
- **AND** waits for user to fill in missing text

#### Scenario: Present Multiple Choice card
- **WHEN** system presents a Multiple Choice card
- **THEN** displays question with numbered options
- **AND** waits for user to select option number

### Requirement: Answer Evaluation with User Review
The system SHALL evaluate user answers automatically and allow user to review and override the evaluation.

#### Scenario: Automatic evaluation suggests correct
- **WHEN** user answers "Paris" for question "Capital of France?"
- **THEN** system automatically evaluates as correct
- **AND** presents evaluation to user for confirmation: "I think this is CORRECT. Do you agree? (yes/no)"

#### Scenario: Automatic evaluation suggests incorrect
- **WHEN** user answers "Berlin" for question "Capital of France?"
- **THEN** system automatically evaluates as incorrect
- **AND** presents evaluation to user: "I think this is INCORRECT. The correct answer is: Paris. Do you agree? (yes/no/show-explanation)"

#### Scenario: User confirms correct evaluation
- **WHEN** system suggests "correct" and user confirms "yes"
- **THEN** system marks card as correct
- **AND** increments correct count
- **AND** moves to next card

#### Scenario: User overrides to incorrect
- **WHEN** system suggests "correct" but user says "no"
- **THEN** system marks card as incorrect
- **AND** adds card to retry queue
- **AND** increments incorrect count

#### Scenario: User overrides to correct
- **WHEN** system suggests "incorrect" but user says "no, it was correct"
- **THEN** system marks card as correct
- **AND** proceeds to next card

#### Scenario: User requests explanation
- **WHEN** user responds with "show-explanation" or similar
- **THEN** system provides AI tutor explanation
- **THEN** asks again for confirmation: "Was your answer correct? (yes/no)"

#### Scenario: Evaluate Basic card (case insensitive)
- **WHEN** user answers "paris" for correct answer "Paris"
- **THEN** system evaluates as correct (case insensitive match)

#### Scenario: Evaluate Cloze card
- **WHEN** user provides text matching cloze deletion
- **THEN** system evaluates as correct
- **AND** accepts minor whitespace differences

#### Scenario: Evaluate Multiple Choice
- **WHEN** user selects correct option number
- **THEN** system evaluates as correct

### Requirement: Learning Flow State Machine
The system SHALL manage learning flow through explicit states: presenting, awaiting, evaluating, reviewing, explaining.

#### Scenario: Standard flow progression
- **WHEN** session is active
- **THEN** system transitions: PRESENTING_CARD → AWAITING_ANSWER → EVALUATING → AWAITING_REVIEW → (optional EXPLAINING) → next card
- **AND** maintains current state in session data

#### Scenario: Skip explanation in test mode
- **WHEN** learning mode is "test"
- **THEN** system skips EXPLAINING state
- **AND** proceeds directly to next card after review confirmation

#### Scenario: Review flow with explanation request
- **WHEN** user requests explanation during review
- **THEN** system enters EXPLAINING state
- **THEN** returns to AWAITING_REVIEW after explanation
- **AND** user confirms final evaluation

### Requirement: Card Queue Management
The system SHALL manage separate queues for new cards and incorrect cards with retry logic.

#### Scenario: Process new cards first
- **WHEN** session starts with 10 new cards
- **THEN** system presents cards from new queue sequentially
- **AND** only processes retry queue after new queue is empty

#### Scenario: Retry incorrect cards
- **WHEN** user answers card incorrectly
- **THEN** system adds card to retry queue
- **AND** presents it again after all new cards

#### Scenario: Multiple incorrect attempts
- **WHEN** user answers same card incorrectly multiple times
- **THEN** system continues retrying until correct
- **AND** tracks attempt count per card

#### Scenario: Session completion
- **WHEN** both new queue and retry queue are empty
- **THEN** system marks session as complete
- **AND** displays final statistics

### Requirement: Card Conversion from Anki
The system SHALL convert Anki note types to unified Card model for consistent processing.

#### Scenario: Convert Basic note
- **WHEN** system imports Anki note with modelName "Basic"
- **THEN** extracts Front field as question
- **AND** extracts Back field as answer
- **AND** creates Card with type BASIC

#### Scenario: Convert Cloze note
- **WHEN** system imports Anki note with modelName "Cloze"
- **THEN** extracts Text field with cloze deletions
- **AND** parses {{c1::text}} markers
- **AND** creates Card with type CLOZE

#### Scenario: Unsupported note type
- **WHEN** system encounters unknown note type
- **THEN** logs warning
- **AND** skips card or converts to Basic as fallback
