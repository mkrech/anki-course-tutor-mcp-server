# Design Decisions

Key architectural and technical decisions made during development of anki-course-tutor.

## Table of Contents
1. [Persistence Strategy](#1-persistence-strategy)
2. [State Machine Pattern](#2-state-machine-pattern)
3. [Two-Phase Answer Evaluation](#3-two-phase-answer-evaluation)
4. [Anki Scheduler Integration](#4-anki-scheduler-integration)
5. [AI Tutor Implementation](#5-ai-tutor-implementation)
6. [Card Type Handling](#6-card-type-handling)
7. [Error Handling Strategy](#7-error-handling-strategy)

---

## 1. Persistence Strategy

### Decision
Use Anki Desktop as the single source of truth for all persistent data. Keep session state in-memory only.

### Context
- Need to track card review history and scheduling
- Must support multi-device workflows via AnkiWeb
- Deployed via `uvx` (read-only package directory)
- Sessions are typically short-lived (single study session)

### Options Considered

#### Option A: SQLite Database (Rejected)
```
Pros:
+ Full control over schema
+ Could persist session state
+ Independent of Anki

Cons:
- Data duplication with Anki
- Sync complexity with AnkiWeb
- Need write permissions (conflicts with uvx)
- Must implement own scheduling logic
```

#### Option B: JSON Files (Rejected)
```
Pros:
+ Simple implementation
+ Human-readable

Cons:
- Write permissions required
- Concurrent access issues
- Still duplicates Anki data
- No transactional guarantees
```

#### Option C: Anki as Single Source of Truth (Selected)
```
Pros:
+ No data duplication
+ Leverage Anki's mature persistence
+ AnkiWeb sync works automatically
+ Simpler architecture
+ No filesystem dependencies

Cons:
- Requires Anki Desktop running
- Session state ephemeral
- Coupled to AnkiConnect API
```

### Implementation

**Data Flow:**
```python
# Reviews immediately persisted to Anki
await anki_client.answer_card(card_id=123, ease=4)
# Anki updates SQLite → AnkiWeb sync → all devices

# Session recovery after restart
start_session("MyDeck")
# Anki naturally filters already-reviewed cards
```

**In-Memory Session State:**
```python
class SessionManager:
    def __init__(self):
        self._sessions: dict[str, Session] = {}  # Lost on restart
```

### Consequences
- ✅ No additional persistence layer needed
- ✅ Data survives server restarts (in Anki)
- ✅ Multi-device sync via AnkiWeb
- ❌ Cannot resume mid-session after restart
- ❌ Must have Anki Desktop running

### Alternatives Revisited
If uvx constraint is removed, could add optional SQLite persistence for session state while keeping Anki as review history source.

---

## 2. State Machine Pattern

### Decision
Implement learning flow as explicit state machine with typed states.

### Context
- Complex multi-step workflow (present → answer → review → explain)
- Different behavior in EXPLAIN vs TEST modes
- Need to prevent invalid operations
- Must be testable and auditable

### Implementation

```python
class LearningState(str, Enum):
    NOT_STARTED = "not_started"
    PRESENTING_CARD = "presenting_card"
    AWAITING_ANSWER = "awaiting_answer"
    AWAITING_REVIEW = "awaiting_review"
    EXPLAINING = "explaining"
    SESSION_COMPLETE = "session_complete"

# State transitions enforced
def submit_answer(self, user_answer: str):
    if self.session.state != LearningState.AWAITING_ANSWER:
        return {"error": f"Cannot submit answer in state {self.session.state.value}"}
```

**State Diagram:**
```
NOT_STARTED
    ↓
PRESENTING_CARD
    ↓
AWAITING_ANSWER
    ↓ (submit_answer)
AWAITING_REVIEW
    ↓ (confirm_evaluation)
    ├─ EXPLAIN mode → EXPLAINING → (next card)
    └─ TEST mode → (next card directly)
```

### Alternatives Considered

#### Implicit State (Rejected)
```python
# No explicit state, just flags
has_answered = False
needs_explanation = False
```
**Why rejected:** Hard to reason about, easy to get into invalid states

#### Event Sourcing (Rejected)
```python
# Store all events, derive state
events = [CardPresented(), AnswerSubmitted(), ...]
```
**Why rejected:** Overkill for this use case, adds complexity

### Benefits
- Clear, testable state transitions
- Impossible to reach invalid states
- Easy to add new states/transitions
- Self-documenting code

### Trade-offs
- More verbose than implicit state
- Requires discipline to maintain

---

## 3. Two-Phase Answer Evaluation

### Decision
Automatically evaluate answers, then ask user to confirm or override.

### Context
- Answer matching is imperfect (typos, alternatives)
- Users need to learn from evaluation process
- Trust requires transparency
- Some card types are ambiguous (KPRIM partial credit)

### Flow

```python
# Phase 1: Automatic evaluation (suggestion only)
submit_answer("Berlin")
→ "You answered: 'Berlin'\n   Correct answer: 'Paris'\n   Is your answer correct? (yes/no)"

# Phase 2: User confirmation
confirm_evaluation(is_correct=False)
→ Card marked incorrect, added to retry queue
```

### Alternatives Considered

#### Automatic Only (Rejected)
```python
submit_answer("Berlin") → immediately marked incorrect
```
**Why rejected:** 
- Users might disagree with evaluation
- No learning opportunity from evaluation
- Frustrating when system wrong

#### No Automatic Evaluation (Rejected)
```python
submit_answer("Berlin") → just show correct answer, ask "correct?"
```
**Why rejected:**
- Misses opportunity to teach evaluation
- More cognitive load on user
- Less guidance

### Benefits
- Handles edge cases gracefully
- User feels in control
- Transparent evaluation process
- Learning opportunity

### Implementation Details

**Evaluation Logic:**
```python
class AnswerEvaluator:
    @staticmethod
    def evaluate_basic(user_answer: str, correct_answer: str) -> bool:
        # Case-insensitive, whitespace-normalized
        user_clean = user_answer.strip().lower()
        correct_clean = correct_answer.strip().lower()
        
        # Exact match or contained in variants
        return user_clean == correct_clean or user_clean in variants
    
    @staticmethod
    def evaluate_cloze(user_answer: str, correct_answer: str) -> bool:
        # Handle multiple deletions: "k^n-1, 1"
        # Normalize mathematical expressions
        pass
    
    @staticmethod
    def evaluate_all_in_one(user_answer: str, correct_answer: str, variant_type: str) -> bool:
        # KPRIM: Accept RFRF, 1010, TFTF, Y N Y N
        # MC/SC: Standard evaluation
        pass
```

---

## 4. Anki Scheduler Integration

### Decision
Submit reviews directly to Anki's scheduler with binary ease mapping.

### Context
- Anki has mature spaced repetition (SM-2, FSRS)
- Users expect reviews to sync across devices
- Want to leverage Anki's ecosystem
- Need immediate feedback in Anki Desktop

### Implementation

```python
async def _submit_review_to_anki(self, card: Card, is_correct: bool):
    ease = 4 if is_correct else 1  # Binary mapping
    await self.anki_client.answer_card(card_id=int(card.id), ease=ease)
```

**Ease Values:**
- `1` = Again (show soon)
- `4` = Easy (show much later)

### Alternatives Considered

#### Local-Only Scheduling (Rejected)
```python
# Track reviews in our own system
self._schedule_next_review(card, is_correct)
```
**Why rejected:**
- Duplicates Anki's logic
- No AnkiWeb sync
- Reinventing the wheel

#### Batch Submission (Considered for Future)
```python
# Submit all reviews at session end
await self.anki_client.answer_cards([...])
```
**Why not now:**
- More complex error handling
- Delayed feedback in Anki
- Risk of losing batch on crash

#### Granular Ease (Future Enhancement)
```python
# Map to 4 levels: Again, Hard, Good, Easy
ease = {
    "again": 1,
    "hard": 2,
    "good": 3,
    "easy": 4
}[difficulty]
```
**Why not now:**
- MVP scope - binary is simpler
- Can add later without breaking changes

### Error Handling Strategy

**Fail-Fast Approach:**
```python
try:
    await self._submit_review_to_anki(card, is_correct)
except Exception as e:
    return {"error": str(e), "state": "error"}
```

**Rationale:**
- User should know immediately if review didn't save
- Better than silent failure
- Anki connection required anyway for card loading

**Future Consideration:**
- Queue failed reviews for retry
- Allow offline mode with sync-later

### Benefits
- Leverages proven scheduling algorithms
- Seamless multi-device workflow
- Reviews visible immediately in Anki
- No scheduling logic to maintain

### Trade-offs
- ✅ Simple, reliable
- ❌ Binary only (no nuanced difficulty)
- ❌ Requires Anki running
- ❌ Network dependency

---

## 5. AI Tutor Implementation

### Decision
Prepare LLM prompts but use placeholder explanations for MVP.

### Current State

```python
class AITutor:
    PROMPT_TEMPLATE = """You are a helpful tutor...
    Card Question: {question}
    Correct Answer: {correct_answer}
    User's Answer: {user_answer}
    ..."""
    
    async def generate_explanation(self, card, user_answer, correct_answer, mode):
        prompt = self.PROMPT_TEMPLATE.format(...)
        
        # TODO: LLM integration
        explanation = self._generate_placeholder_explanation(...)
        
        return {
            "explanation": explanation,
            "prompt": prompt  # For future LLM call
        }
```

**Placeholder Output:**
```
"The correct answer is 'Paris'. You answered 'Berlin', which is incorrect. 
To remember this, try associating it with something familiar. 
Don't worry, learning takes practice! You'll get it next time."
```

### Why Not Implement LLM Yet?

#### Technical Reasons
1. **Architecture First:** Validate learning flow before AI integration
2. **Testing Simplicity:** Placeholders are deterministic and easy to test
3. **MVP Scope:** Core functionality (learning flow, Anki sync) more critical
4. **Context Injection:** Requires passing `Context` through layers

#### Cost Considerations
- LLM calls have monetary cost per request
- Want to optimize prompts before production use
- Placeholder allows testing without API costs

### Future LLM Integration Plans

#### Option 1: Context Through Layers (Recommended)
```python
# mcp_server.py
@mcp.tool()
async def get_explanation(ctx: Context):
    result = await _learning_engine.get_explanation(ctx)

# learning_engine.py
async def get_explanation(self, ctx: Context):
    result = await self.ai_tutor.generate_explanation(..., ctx=ctx)

# ai_tutor.py
async def generate_explanation(self, ..., ctx: Context):
    response = await ctx.request_sampling(
        messages=[{"role": "user", "content": self.PROMPT_TEMPLATE.format(...)}],
        max_tokens=200,
        temperature=0.7
    )
    return {"explanation": response.content}
```

**Pros:**
- Clean separation of concerns
- AITutor testable in isolation
- Can mock Context in tests

**Cons:**
- More refactoring needed
- Context parameter threaded through layers

#### Option 2: Direct in MCP Tool (Simpler)
```python
@mcp.tool()
async def get_explanation(ctx: Context):
    card = _learning_engine.current_card
    prompt = AITutor.PROMPT_TEMPLATE.format(
        question=card.question,
        correct_answer=card.answer,
        user_answer=_learning_engine.current_user_answer,
        ...
    )
    response = await ctx.request_sampling(
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    return {"explanation": response.content}
```

**Pros:**
- Minimal changes
- Direct access to Context
- Faster to implement

**Cons:**
- Mixes concerns (MCP layer knows prompt details)
- Harder to test AITutor independently

### Prompt Engineering Considerations

**Current Template:**
- Max 5 sentences (concise)
- Encouraging tone
- Focus on why correct answer is right
- Actionable memory tips

**Future Enhancements:**
- Adaptive difficulty based on user history
- Personalized explanations (learning style)
- Multi-language support
- Domain-specific prompts (math vs history)

### Benefits of Current Approach
- ✅ System fully functional without LLM
- ✅ Prompts ready for future integration
- ✅ Easy to test and iterate
- ✅ No API costs during development

---

## 6. Card Type Handling

### Decision
Support multiple card types with unified evaluation interface.

### Card Types

```python
class CardType(str, Enum):
    BASIC = "basic"           # Q&A pairs
    CLOZE = "cloze"          # Fill-in-blank
    ALL_IN_ONE = "all_in_one" # Flexible (KPRIM, MC, SC)
```

### Evaluation Strategy

**Polymorphic Evaluation:**
```python
class AnswerEvaluator:
    @staticmethod
    def evaluate_basic(user, correct) -> bool: ...
    
    @staticmethod
    def evaluate_cloze(user, correct) -> bool: ...
    
    @staticmethod
    def evaluate_all_in_one(user, correct, variant_type) -> bool: ...
```

### KPRIM Handling (Special Case)

**Challenge:** Multiple valid input formats
```
User might answer:
- "1 0 1 0"
- "RFRF"
- "T F T F"
- "Y N Y N"
- "1,0,1,0"
```

**Solution: Normalization**
```python
@staticmethod
def _normalize_kprim_answer(answer: str) -> list[bool]:
    """Convert any format to [True, False, True, False]"""
    # Remove separators
    answer = answer.replace(",", "").replace(" ", "")
    
    result = []
    for char in answer.upper():
        if char in "1TYR": result.append(True)
        elif char in "0FNF": result.append(False)
    
    return result
```

**Comparison:**
```python
user_norm = _normalize_kprim_answer("R F R F")      # [True, False, True, False]
correct_norm = _normalize_kprim_answer("1 0 1 0")   # [True, False, True, False]
is_correct = user_norm == correct_norm              # True
```

### Mathematical Expression Normalization

**Challenge:** Unicode vs ASCII notation
```
User: "k²"   vs   Correct: "k^2"
User: "k×n"  vs   Correct: "k*n"
```

**Solution:**
```python
@staticmethod
def _normalize_math_expression(text: str) -> str:
    # Superscripts → ^
    text = text.replace("²", "^2").replace("³", "^3")
    
    # Operators
    text = text.replace("×", "*").replace("÷", "/")
    
    # Whitespace around operators
    text = re.sub(r'\s*([+\-*/^])\s*', r'\1', text)
    
    return text.strip().lower()
```

### Multiple Cloze Deletions

**Example:**
```
Question: "The time complexity is {{c1::O(n²)}} and space is {{c2::O(1)}}"
User must answer: "O(n²), O(1)"
```

**Evaluation:**
```python
def evaluate_cloze(user_answer: str, correct_answer: str) -> bool:
    user_parts = [p.strip() for p in user_answer.split(',')]
    correct_parts = [p.strip() for p in correct_answer.split(',')]
    
    if len(user_parts) != len(correct_parts):
        return False
    
    # Evaluate each deletion
    for user_part, correct_part in zip(user_parts, correct_parts):
        if not self._matches(user_part, correct_part):
            return False
    
    return True
```

### Benefits
- ✅ Supports popular Anki card types
- ✅ Flexible answer formats (KPRIM)
- ✅ Handles mathematical notation
- ✅ Multiple cloze deletions

### Trade-offs
- More complex evaluation logic
- Edge cases require testing
- Normalization might be too permissive

---

## 7. Error Handling Strategy

### Decision
Fail-fast for critical errors, graceful degradation for non-critical.

### Critical Errors (Fail-Fast)

**Anki Connection Failures:**
```python
async def _submit_review_to_anki(self, card: Card, is_correct: bool):
    try:
        await self.anki_client.answer_card(card_id, ease)
    except Exception as e:
        logger.error(f"Failed to submit review to Anki: {e}")
        # Return error to user - don't continue
        raise Exception(
            "Failed to submit review to Anki. "
            "Please ensure Anki is running with AnkiConnect enabled."
        )
```

**Rationale:**
- Review not saved = data loss
- Better to stop than silently fail
- User needs to fix Anki connection

### Non-Critical Errors (Graceful)

**Missing Card Fields:**
```python
if not card.question:
    logger.warning(f"Card {card.id} has no question, skipping")
    # Continue with next card
```

**Invalid Session State:**
```python
def submit_answer(self, answer: str):
    if self.session.state != LearningState.AWAITING_ANSWER:
        # Return error but don't crash
        return {"error": f"Cannot submit answer in state {self.session.state.value}"}
```

### Logging Strategy

```python
logger.info()    # High-level operations (session start, card transitions)
logger.debug()   # Detailed state info (useful for debugging)
logger.warning() # Unexpected but recoverable (missing fields)
logger.error()   # Failures requiring attention (Anki errors)
```

### Future Improvements

**Retry Logic:**
```python
# Retry AnkiConnect calls with exponential backoff
@retry(max_attempts=3, backoff=exponential)
async def answer_card(self, card_id: int, ease: int):
    ...
```

**Offline Queue:**
```python
# Queue reviews when Anki unavailable, sync later
class ReviewQueue:
    def enqueue(self, card_id: int, ease: int):
        self._pending.append((card_id, ease))
    
    async def flush(self):
        # Submit all pending when Anki reconnects
        ...
```

### Benefits
- ✅ Clear error messages
- ✅ No silent failures
- ✅ Appropriate error granularity

### Trade-offs
- ❌ No automatic retry (yet)
- ❌ No offline support (yet)

---

## Related Documentation
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture overview
- [openspec/project.md](../openspec/project.md) - Project conventions
- [CHANGELOG.md](../CHANGELOG.md) - Change history
