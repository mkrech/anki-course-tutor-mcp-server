## ADDED Requirements

### Requirement: Personality Rotation
The system SHALL rotate between tutor personalities in a 3:1 ratio (3 normal, 1 pirate).

#### Scenario: First three explanations normal
- **WHEN** session starts and user requests 3 explanations
- **THEN** all 3 use "Normal Tutor" personality
- **AND** provide straightforward educational explanations

#### Scenario: Fourth explanation pirate
- **WHEN** user requests 4th explanation in session
- **THEN** system uses "Pirate" personality
- **AND** provides explanation in pirate speech style

#### Scenario: Rotation continues
- **WHEN** user requests 5th, 6th, 7th explanations
- **THEN** system returns to normal personality
- **AND** uses pirate again on 8th explanation

#### Scenario: Rotation persists across session resume
- **WHEN** session paused after 2 explanations and resumed
- **THEN** next explanation is normal (3rd in sequence)
- **AND** 4th explanation after resume is pirate

### Requirement: Learning Mode Support
The system SHALL support two learning modes: Explain and Test with different AI behavior.

#### Scenario: Explain mode provides feedback
- **WHEN** learning mode is "explain"
- **AND** user answers incorrectly
- **THEN** system requests AI explanation
- **AND** displays explanation to user

#### Scenario: Test mode suppresses explanations
- **WHEN** learning mode is "test"
- **AND** user answers incorrectly
- **THEN** system skips AI explanation
- **AND** proceeds to next card immediately

#### Scenario: Explain mode for correct answers
- **WHEN** learning mode is "explain"
- **AND** user answers correctly
- **THEN** system MAY provide brief reinforcement (optional)

### Requirement: Explanation Length Limiting
The system SHALL limit AI explanations to maximum 5 sentences.

#### Scenario: Truncate long explanation
- **WHEN** AI generates explanation with 8 sentences
- **THEN** system truncates to first 5 sentences
- **AND** adds "..." indicator if truncated

#### Scenario: Short explanation preserved
- **WHEN** AI generates explanation with 3 sentences
- **THEN** system presents full explanation without modification

### Requirement: Context-Aware Prompting
The system SHALL provide AI with card context and user answer for accurate explanations.

#### Scenario: Explanation for incorrect answer
- **WHEN** user answers "Berlin" for "Capital of France?"
- **THEN** system sends prompt with question, correct answer "Paris", user answer "Berlin"
- **AND** AI explains why Paris is correct and clarifies confusion with Germany

#### Scenario: Personality injection in prompt
- **WHEN** pirate personality is active
- **THEN** system adds "Respond in pirate speech" to prompt
- **AND** AI adopts appropriate tone

#### Scenario: Card metadata in context
- **WHEN** requesting explanation
- **THEN** system includes card type, deck name, and any tags
- **AND** AI can reference learning context

### Requirement: FastMCP Integration
The system SHALL use FastMCP for model-agnostic AI communication.

#### Scenario: Call AI via MCP
- **WHEN** explanation is needed
- **THEN** system invokes FastMCP with formatted prompt
- **AND** receives response asynchronously

#### Scenario: Handle AI errors gracefully
- **WHEN** MCP call fails or times out
- **THEN** system displays fallback message "Explanation temporarily unavailable"
- **AND** allows continuing learning without AI

#### Scenario: Model flexibility
- **WHEN** user configures different LLM backend
- **THEN** system works without code changes
- **AND** FastMCP handles model abstraction
