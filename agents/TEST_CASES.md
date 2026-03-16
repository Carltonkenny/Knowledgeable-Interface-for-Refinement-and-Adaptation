# Kira Test Cases — Expected Outputs

**Purpose:** Demonstrate Kira's behavior across various edge cases  
**Status:** Reference documentation for expected outputs  
**Version:** 2.0.0

---

## TEST CASE 1: Simple Greeting (CONVERSATION)

**Input:**
```json
{
  "message": "hi",
  "history": [],
  "user_profile": {}
}
```

**Expected Output:**
```json
{
  "intent": "conversation",
  "response": "Hey! I'm Kira. I turn rough prompts into precise, powerful ones. What are you working on today?",
  "improved_prompt": null,
  "changes_made": [],
  "confidence": 0.85,
  "confidence_reason": "Simple greeting, clear intent",
  "clarification_needed": false,
  "latency_ms": 580,
  "personality_adaptation": {
    "detected_formality": 0.2,
    "detected_technical": 0.0,
    "adaptation_notes": "User very casual, adapting to friendly casual tone"
  }
}
```

**Routing Decision:**
```python
RouteType.CONVERSATION
proceed_with_swarm: False
```

---

## TEST CASE 2: Followup Request (FOLLOWUP)

**Input:**
```json
{
  "message": "make it longer",
  "history": [
    {"role": "user", "message": "write a story"},
    {"role": "assistant", "message": "Here's a story...", "improved_prompt": "Write a 500-word short story..."}
  ],
  "user_profile": {"preferred_tone": "direct"}
}
```

**Expected Output:**
```json
{
  "intent": "followup",
  "response": "Got it — expanding the detail and depth.",
  "improved_prompt": "Write a 1,200-word short story with rich character development, detailed world-building, and multiple plot threads that interweave...",
  "changes_made": [
    "Expanded word count from 500 to 1,200 words",
    "Added character development requirement",
    "Included world-building and plot complexity"
  ],
  "confidence": 0.92,
  "confidence_reason": "Clear modification request with context from history",
  "clarification_needed": false,
  "latency_ms": 620,
  "personality_adaptation": {
    "detected_formality": 0.3,
    "detected_technical": 0.2,
    "adaptation_notes": "User casual and direct, matching tone"
  }
}
```

**Routing Decision:**
```python
RouteType.FOLLOWUP
proceed_with_swarm: False
agents_to_run: []
```

---

## TEST CASE 3: Vague Request (CLARIFICATION)

**Input:**
```json
{
  "message": "write something about AI",
  "history": [],
  "user_profile": {}
}
```

**Expected Output:**
```json
{
  "intent": "new_prompt",
  "response": "AI is a big topic — are you writing for technical readers who already know the basics, or explaining it to someone completely new?",
  "improved_prompt": null,
  "changes_made": [],
  "confidence": 0.45,
  "confidence_reason": "Vague request with no domain/context specified",
  "clarification_needed": true,
  "clarification_question": "Is this going to be read by someone who already knows AI, or are you explaining it from scratch?",
  "latency_ms": 540,
  "personality_adaptation": {
    "detected_formality": 0.5,
    "detected_technical": 0.5,
    "adaptation_notes": "Neutral tone detected, using balanced approach"
  }
}
```

**Routing Decision:**
```python
RouteType.CLARIFICATION
proceed_with_swarm: False
clarification_needed: True
ambiguity_score: 0.8
```

---

## TEST CASE 4: Rich Technical Request (SWARM)

**Input:**
```json
{
  "message": "write a 3-email cold outreach sequence for a SaaS selling project management tools to construction companies",
  "history": [],
  "user_profile": {
    "dominant_domains": ["business", "marketing"],
    "preferred_tone": "direct",
    "domain_confidence": 0.91
  }
}
```

**Expected Output:**
```json
{
  "intent": "new_prompt",
  "response": "On it — B2B SaaS cold sequence, construction angle. Firing the swarm.",
  "improved_prompt": "Write a 3-email cold outreach sequence for a B2B SaaS product — project management software targeting construction company owners and project managers. Core pain points: missed deadlines causing penalty clauses, budget overruns from poor subcontractor coordination. Email 1 (Day 1): Pattern interrupt subject line, acknowledge pain without pitching. Email 2 (Day 4): Lead with construction industry stat, introduce product as context. Email 3 (Day 9): Short breakup email. Each email max 150 words. Tone: direct, peer-level, zero corporate fluff.",
  "changes_made": [
    "Added specific pain points for construction industry",
    "Defined email cadence (Day 1, 4, 9)",
    "Set 150-word limit per email for busy PMs",
    "Specified direct, peer-level tone matching user profile"
  ],
  "quality_score": {
    "specificity": 5,
    "clarity": 5,
    "actionability": 5,
    "overall": 5
  },
  "confidence": 0.95,
  "confidence_reason": "Specific, well-formed request with clear domain",
  "clarification_needed": false,
  "latency_ms": 4200,
  "personality_adaptation": {
    "detected_formality": 0.5,
    "detected_technical": 0.6,
    "blended_formality": 0.56,
    "blended_technical": 0.83,
    "adaptation_notes": "User direct and business-focused, matching professional tone"
  },
  "metadata": {
    "user_energy": "direct",
    "topics_mentioned": ["SaaS", "cold outreach", "construction", "project management"],
    "agents_run": ["intent", "context"],
    "agents_skipped": ["domain: profile confidence 0.91 > 0.85"]
  }
}
```

**Routing Decision:**
```python
RouteType.SWARM
proceed_with_swarm: True
agents_to_run: ["intent", "context"]
skip_reasons: {
  "domain": "profile confidence 0.91 > 0.85",
  "context": None,
  "intent": None
}
```

---

## TEST CASE 5: Ultra-Short Message (CONVERSATION)

**Input:**
```json
{
  "message": "u",
  "history": [],
  "user_profile": {}
}
```

**Expected Output:**
```json
{
  "intent": "conversation",
  "response": "Hey there! What's on your mind?",
  "improved_prompt": null,
  "changes_made": [],
  "confidence": 0.8,
  "confidence_reason": "Very short message treated as greeting",
  "clarification_needed": false,
  "latency_ms": 520
}
```

**Routing Decision:**
```python
RouteType.CONVERSATION
proceed_with_swarm: False
```

**Why:** Message length < 10 characters triggers CONVERSATION route.

---

## TEST CASE 6: Expert Developer Request (SWARM with Domain Skip)

**Input:**
```json
{
  "message": "I'm implementing rate limiting for a FastAPI app with ~1,000 users. Compare Redis sliding window log vs token bucket algorithm.",
  "history": [
    {"role": "user", "message": "How do I structure FastAPI middleware?"},
    {"role": "assistant", "message": "Here's how to structure middleware..."}
  ],
  "user_profile": {
    "dominant_domains": ["coding", "python", "fastapi"],
    "preferred_tone": "technical",
    "domain_confidence": 0.94
  }
}
```

**Expected Output:**
```json
{
  "intent": "new_prompt",
  "response": "Got it — comparing rate limiting algorithms at your scale. Running the analysis.",
  "improved_prompt": "Compare Redis sliding window log vs token bucket algorithm for rate limiting a FastAPI application with ~1,000 users. Address: memory usage per user, burst handling behavior, implementation complexity with redis-py, consistency under concurrent requests. Priorities: correctness under load, implementation simplicity, memory efficiency. Provide clear recommendation with reasoning.",
  "changes_made": [
    "Added specific tradeoff categories (memory, bursts, complexity, consistency)",
    "Specified priority ordering for decision criteria",
    "Requested clear recommendation with reasoning"
  ],
  "quality_score": {
    "specificity": 5,
    "clarity": 5,
    "actionability": 5,
    "overall": 5
  },
  "confidence": 0.96,
  "confidence_reason": "Expert-level request with specific technical context",
  "clarification_needed": false,
  "latency_ms": 3800,
  "personality_adaptation": {
    "detected_formality": 0.6,
    "detected_technical": 0.9,
    "blended_formality": 0.63,
    "blended_technical": 0.91,
    "adaptation_notes": "Expert technical user, using precise terminology"
  },
  "metadata": {
    "agents_run": ["intent", "context"],
    "agents_skipped": ["domain: profile confidence 0.94 > 0.85"]
  }
}
```

**Routing Decision:**
```python
RouteType.SWARM
proceed_with_swarm: True
agents_to_run: ["intent", "context"]
skip_reasons: {
  "domain": "profile confidence 0.94 > 0.85",
  "context": None,
  "intent": None
}
```

---

## TEST CASE 7: Modification Without History (FALLBACK TO NEW_PROMPT)

**Input:**
```json
{
  "message": "make it shorter",
  "history": [],
  "user_profile": {}
}
```

**Expected Output:**
```json
{
  "intent": "followup",
  "response": "I can tighten that up — but I don't see a previous prompt to refine. What are we working with?",
  "improved_prompt": null,
  "changes_made": [],
  "confidence": 0.5,
  "confidence_reason": "Modification phrase detected but no history found",
  "clarification_needed": true,
  "clarification_question": "What prompt would you like me to refine?",
  "latency_ms": 480
}
```

**Why:** Modification phrase detected, but no history → clarification needed.

---

## TEST CASE 8: Forbidden Phrase Detection

**Input (Response to check):**
```
"Certainly! I'd be happy to help you with that prompt."
```

**Expected Output:**
```json
{
  "forbidden_phrases_detected": ["Certainly", "I'd be happy to"],
  "valid": false,
  "suggested_revision": "Got it — let me help you refine that prompt."
}
```

**Implementation:**
```python
from agents import check_forbidden_phrases

text = "Certainly! I'd be happy to help you with that prompt."
found = check_forbidden_phrases(text)
# Returns: ["Certainly", "I'd be happy to"]
```

---

## TEST CASE 9: Input Quality Scoring

**Test Cases:**

```python
from agents import score_input_quality

# Case 1: Thin input
score1 = score_input_quality("fix my code", has_session_history=False)
print(score1)
# QualityScore(
#   score=1,
#   word_count=3,
#   has_context=False,
#   has_constraints=False,
#   has_domain=True,
#   recommendation="light"
# )

# Case 2: Moderate input
score2 = score_input_quality("write a blog post about AI for beginners", has_session_history=True)
print(score2)
# QualityScore(
#   score=2,
#   word_count=8,
#   has_context=True,  # "for beginners"
#   has_constraints=False,
#   has_domain=True,
#   recommendation="standard"
# )

# Case 3: Rich input
score3 = score_input_quality("write a 700-word argumentative essay claiming that social media has net negative impact on teenage mental health", has_session_history=True)
print(score3)
# QualityScore(
#   score=3,
#   word_count=17,
#   has_context=True,
#   has_constraints=True,  # "700-word", "argumentative essay"
#   has_domain=True,
#   recommendation="full"
# )
```

---

## TEST CASE 10: Personality Adaptation

**Test Cases:**

```python
from agents.context.adapters import analyze_user_style, blend_with_profile

# Case 1: Very casual user
style1 = analyze_user_style("hey can u help me with some code pls")
print(style1)
# {'formality': 0.15, 'technical': 0.3}

# Case 2: Very formal user
style2 = analyze_user_style("Could you please assist me in crafting an API documentation prompt?")
print(style2)
# {'formality': 0.85, 'technical': 0.7}

# Case 3: Blend with profile
profile = {"preferred_tone": "technical", "dominant_domains": ["coding"]}
blended = blend_with_profile(style1, profile)
print(blended)
# {'formality': 0.44, 'technical': 0.75}
# Profile (70%) pulls technical up from 0.3 to 0.75
```

---

## TEST CASE 11: Routing Edge Cases

```python
from agents import decide_route, RouteType

# Case 1: Exactly 10 characters
decision1 = decide_route("hello world", [], {}, False)
print(decision1.route)
# RouteType.SWARM (10 chars is NOT < 10)

# Case 2: 9 characters
decision2 = decide_route("hi there!", [], {}, False)
print(decision2.route)
# RouteType.CONVERSATION (9 < 10)

# Case 3: Pending clarification
decision3 = decide_route("yes the topic is AI ethics", [], {}, True)
print(decision3.route)
# RouteType.SWARM (pending clarification overrides other rules)

# Case 4: Multiple modification phrases
decision4 = decide_route("make it shorter and more formal", [], {}, False)
print(decision4.route)
# RouteType.FOLLOWUP (modification detected)
```

---

## TEST CASE 12: Context Building

```python
from agents import build_context_block

profile = {
  "dominant_domains": ["coding", "marketing"],
  "preferred_tone": "direct"
}
memories = [
  {"content": "User prefers concise prompts", "domain": "coding"},
  {"content": "User likes technical examples", "domain": "coding"}
]

context = build_context_block(
  user_profile=profile,
  langmem_memories=memories,
  session_count=23,
  recent_quality_trend=[2.1, 2.8, 3.2, 3.6, 4.1]
)

print(context)
```

**Output:**
```
## USER CONTEXT — READ BEFORE RESPONDING

SESSION: Power user (23 sessions). Treat as peer.
DOMAINS: Strong in coding, marketing. Adjust depth accordingly.
TONE PREFERENCE: User responds well to direct tone.
QUALITY TREND: Improving — avg 3.2/5.
RELEVANT MEMORIES FROM PAST SESSIONS:
  [coding] User prefers concise prompts
  [coding] User likes technical examples

--- END USER CONTEXT ---
```

---

## SUMMARY TABLE

| Test Case | Input | Expected Route | Latency | Notes |
|-----------|-------|----------------|---------|-------|
| 1. Simple greeting | "hi" | CONVERSATION | ~580ms | Short message |
| 2. Followup | "make it longer" | FOLLOWUP | ~620ms | Has history |
| 3. Vague request | "write something about AI" | CLARIFICATION | ~540ms | High ambiguity |
| 4. Rich technical | "write a 3-email cold..." | SWARM | ~4,200ms | Full pipeline |
| 5. Ultra-short | "u" | CONVERSATION | ~520ms | < 10 chars |
| 6. Expert dev | "I'm implementing rate limiting..." | SWARM | ~3,800ms | Domain skipped |
| 7. No history | "make it shorter" | FOLLOWUP → clarification | ~480ms | Fallback |
| 8. Forbidden phrases | "Certainly! I'd be happy..." | N/A | N/A | Validation |
| 9. Quality scoring | Various | N/A | N/A | 1-3 score |
| 10. Personality | Various | N/A | N/A | Adaptation |
| 11. Routing | Various | Varies | N/A | Edge cases |
| 12. Context | Profile + memories | N/A | N/A | Building |

---

**Last Updated:** 2026-03-15  
**Version:** 2.0.0  
**Status:** Reference documentation
