# Step 3-5: Context, Domain, and Prompt Engineer Agents

**Files:** `agents/context.py`, `agents/domain.py`, `agents/prompt_engineer.py`  
**Estimated Duration:** 7-8 hours combined  
**Complexity:** Medium

---

## QUICK OVERVIEW

These three agents follow the exact same pattern as Intent Agent (STEP_2):

1. Get fast/full LLM
2. Format prompt with context
3. Call LLM
4. Parse JSON response
5. Store in state["breakdown"][agent_name]
6. Handle errors gracefully

---

## STEP 3: CONTEXT AGENT

**File:** `agents/context.py`

### What It Does
Analyzes **who the user is** — experience level, domain, role, communication style, constraints.

### Key Difference from Intent
- Intent: WHAT user wants
- Context: WHO the user is, WHAT they're working with

### Input Context
```python
original_prompt: str
user_profile: Optional[dict]
conversation_history: list
```

### Output Schema
```json
{
  "experience_level": "beginner|intermediate|expert",
  "domain": "string — primary field",
  "role": "string — job function",
  "constraints": ["constraint1", "constraint2"],
  "communication_style": "formal|casual|technical",
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}
```

### System Prompt Template
```
You are the Context Analyzer for PromptForge.
Understand WHO the user is and WHAT context they're working in.

Infer from their prompt and profile:
1. Experience level (beginner, intermediate, expert)
2. Domain/industry context
3. Role or job function
4. Key constraints they operate under
5. Communication style preference

Be specific. Use language patterns from their writing.

Return valid JSON ONLY. No markdown, no extra text.
```

### Implementation Skeleton
```python
async def context_node(state: PromptForgeState) -> PromptForgeState:
    """Analyze user context using fast LLM."""
    
    try:
        llm = get_fast_llm()
        prompt = _format_context_prompt(
            original_prompt=state["original_prompt"],
            conversation_history=state.get("conversation_history", []),
            user_profile=state.get("user_profile")
        )
        response = llm.invoke(prompt)
        parsed = _parse_context_response(response.content if hasattr(response, 'content') else str(response))
        
        # Validate required fields
        required = ["experience_level", "domain", "role", "communication_style"]
        if not all(field in parsed for field in required):
            raise ValueError(f"Missing required fields: {parsed}")
        
        state["breakdown"]["context"] = parsed
        state["agents_used"].append("context")
        
    except Exception as e:
        logging.error(f"Context agent failed: {e}")
        state["breakdown"]["context"] = {"error": str(e), "confidence": 0.0}
        state["agents_skipped"].append({"agent": "context", "reason": str(e)})
    
    return state

def _format_context_prompt(...) -> str:
    # Similar to Intent: include system prompt, profile, history, original prompt
    pass

def _parse_context_response(response: str) -> dict:
    # Same JSON parsing pattern as Intent Agent
    pass
```

### Skip Condition
- **Skip if:** First message in session (zero conversation history)
- **Reason:** New user has no context, so this agent adds noise

### Quality Gates
```python
required_experience = intent_data["experience_level"] in ["beginner", "intermediate", "expert"]
required_style = intent_data["communication_style"] in ["formal", "casual", "technical"]
required_confidence = intent_data.get("confidence", 0) >= 0.7

passes = sum([required_experience, required_style, required_confidence]) >= 2
```

---

## STEP 4: DOMAIN AGENT

**File:** `agents/domain.py`

### What It Does
Identifies the **specific technical/professional domain** — FastAPI, React, DevOps, etc.

### Key Difference
- Intent: WHAT user wants
- Context: WHO user is
- Domain: **WHAT FIELD** user is working in

### Input Context
```python
original_prompt: str
user_profile: Optional[dict]
dominant_domains: list  # From user's history
```

### Output Schema
```json
{
  "primary_domain": "fastapi|react|devops|etc",
  "sub_specialties": ["specialty1", "specialty2"],
  "technical_depth": "foundational|intermediate|expert",
  "relevant_conventions": ["convention1", "convention2"],
  "common_pitfalls": ["pitfall1", "pitfall2"],
  "confidence": 0.0-1.0,
  "reasoning": "brief explanation"
}
```

### System Prompt Template
```
You are the Domain Identifier for PromptForge.
Pinpoint the exact field, technology, or specialty area the user is working in.

Determine:
1. Primary domain (specific, not generic)
2. Sub-specialties or adjacent domains
3. Technical depth indicators
4. Best practices in this domain
5. Common pitfalls for this domain

Reference their past prompts if available.

Return valid JSON ONLY.
```

### Implementation Skeleton
```python
async def domain_node(state: PromptForgeState) -> PromptForgeState:
    """Identify user's domain expertise."""
    
    try:
        llm = get_fast_llm()
        prompt = _format_domain_prompt(
            original_prompt=state["original_prompt"],
            user_profile=state.get("user_profile"),
            dominant_domains=state.get("user_profile", {}).get("dominant_domains", [])
        )
        response = llm.invoke(prompt)
        parsed = _parse_domain_response(response.content if hasattr(response, 'content') else str(response))
        
        # Validate
        if "primary_domain" not in parsed or not parsed["primary_domain"]:
            raise ValueError("primary_domain must be non-empty")
        
        state["breakdown"]["domain"] = parsed
        state["agents_used"].append("domain")
        
        # Update domain confidence in profile
        if parsed.get("confidence", 0) > 0.7:
            await update_domain_confidence(
                state["user_id"],
                parsed["primary_domain"],
                parsed["confidence"]
            )
        
    except Exception as e:
        logging.error(f"Domain agent failed: {e}")
        state["breakdown"]["domain"] = {"error": str(e), "confidence": 0.0}
        state["agents_skipped"].append({"agent": "domain", "reason": str(e)})
    
    return state
```

### Skip Condition
- **Skip if:** User profile has domain confidence > 85%
- **Reason:** We're already confident about their domain, identifying it again wastes LLM calls
- **Used in:** `_select_agents_by_profile()` routing function

### Quality Gates
```python
domain_not_generic = domain_data["primary_domain"] not in ["tech", "software", "coding"]
has_pitfalls = len(domain_data.get("common_pitfalls", [])) >= 1
reasonable_confidence = domain_data.get("confidence", 0) >= 0.6  # Lower bar (domains fuzzy)

passes = sum([domain_not_generic, has_pitfalls, reasonable_confidence]) >= 2
```

---

## STEP 5: PROMPT ENGINEER AGENT

**File:** `agents/prompt_engineer.py`

### What It Does
Synthesizes all context from other agents and **rewrites the user's prompt** for maximum quality.

### CRITICAL: This Agent ALWAYS Runs
- Never skipped
- Always after all other agents complete
- Uses **full LLM** (gpt-4o), not fast model
- Highest token budget (2048)

### Input Context
```python
original_prompt: str
breakdown: dict  # Results from intent, context, domain agents
user_profile: dict
langgem_context: list  # Top 5 past prompts for style reference
```

### Output Schema
```json
{
  "improved_prompt": "the rewritten prompt",
  "quality_score": {
    "clarity": 0.0-1.0,
    "specificity": 0.0-1.0,
    "feasibility": 0.0-1.0,
    "overall": 0.0-1.0
  },
  "key_changes": ["change1", "change2", "change3"],
  "reasoning": "why these changes improve it",
  "structured_sections": {
    "goal": "one-liner",
    "context": "key background",
    "requirements": ["req1", "req2"],
    "constraints": ["constraint1"],
    "success_criteria": ["criterion1", "criterion2"]
  }
}
```

### System Prompt Template
```
You are the Prompt Engineer. Transform a raw user prompt 
into a precise, high-performance instruction.

Input available:
- Original prompt: {original_prompt}
- User's intent: {breakdown.intent}
- User's context: {breakdown.context}
- User's domain: {breakdown.domain}
- User's past prompts (for style): {langgem_context}

Your rewrite should:
1. Be crystal clear about the goal
2. Include specific constraints and format requirements
3. Match the user's established tone and style
4. Be appropriately scoped
5. Include quality gates (how to verify it's correct)

Return valid JSON ONLY.
```

### Implementation Skeleton
```python
async def prompt_engineer_node(state: PromptForgeState) -> PromptForgeState:
    """Synthesize and rewrite prompt using full LLM."""
    
    try:
        # Get full LLM (NOT fast)
        llm = get_llm()
        
        # Query LangMem for style reference (CRITICAL)
        style_reference = await query_langgem(
            user_id=state["user_id"],
            query=state["original_prompt"],
            top_k=5
        )
        state["langgem_context"] = style_reference
        
        # Format prompt with all context
        prompt = _format_engineer_prompt(
            original=state["original_prompt"],
            breakdown=state["breakdown"],
            user_profile=state["user_profile"],
            past_prompts=style_reference
        )
        
        response = llm.invoke(prompt)
        parsed = _parse_engineer_response(response.content if hasattr(response, 'content') else str(response))
        
        # Quality gate: overall score must be >= 0.7
        if parsed.get("quality_score", {}).get("overall", 0) < 0.7:
            logging.warning(f"Engineer: Low quality score {parsed['quality_score']['overall']}")
        
        state["improved_prompt"] = parsed["improved_prompt"]
        state["quality_score"] = parsed["quality_score"]
        state["breakdown"]["engineer"] = parsed
        state["agents_used"].append("prompt_engineer")
        
    except Exception as e:
        logging.error(f"Engineer agent failed: {e}")
        state["improved_prompt"] = state["original_prompt"]  # Fallback to original
        state["quality_score"] = {"overall": 0.5}  # Degraded score
        state["breakdown"]["engineer"] = {"error": str(e), "confidence": 0.0}
        state["agents_skipped"].append({"agent": "prompt_engineer", "reason": str(e)})
    
    return state

def _format_engineer_prompt(...) -> str:
    # Include all agent breakdowns, style reference, original prompt
    pass

def _parse_engineer_response(response: str) -> dict:
    # Parse JSON, validate all required fields
    pass
```

### K EY DIFFERENCES FROM OTHER AGENTS

| Aspect | Other Agents | Engineer |
|--------|----------|----------|
| Model | gpt-4o-mini (fast) | gpt-4o (full) |
| Tokens | 400 | 2048 |
| Temperature | 0.1 | 0.3 |
| Latency | 400-600ms | 1000-1500ms |
| Always runs? | No (conditional) | **YES** |
| Uses LangMem? | No | **YES (style reference)** |
| Output | Analysis | **Rewritten prompt** |

### LangMem Integration (CRITICAL)
```python
# In prompt_engineer_node, BEFORE calling LLM

style_reference = await query_langgem(
    user_id=state["user_id"],
    query=state["original_prompt"],
    top_k=5  # Get top 5 best past prompts
)

# Include in engineer prompt
engineer_prompt = f"""
Study this user's established style (their best past prompts).
Match this style in your rewrite:

{format_style_reference(style_reference)}

Now rewrite: {original_prompt}
"""
```

### Quality Gates
```python
improved_differs = parsed["improved_prompt"] != state["original_prompt"]
has_changes = len(parsed.get("key_changes", [])) >= 3
high_quality = parsed.get("quality_score", {}).get("overall", 0) >= 0.7

all_pass = improved_differs and has_changes and high_quality
```

---

## IMPLEMENTATION CHECKLIST

**STEP 3 (Context Agent):**
- [ ] Create `agents/context.py`
- [ ] Implement `context_node()` async function
- [ ] Add prompt formatting function
- [ ] Add JSON parsing with fallback
- [ ] Add quality validation
- [ ] Add error handling with logging
- [ ] Test with sample inputs
- [ ] Verify skipped when zero history

**STEP 4 (Domain Agent):**
- [ ] Create `agents/domain.py`
- [ ] Implement `domain_node()` async function
- [ ] Add domain confidence update call
- [ ] Add JSON parsing with fallback
- [ ] Add quality validation
- [ ] Add error handling with logging
- [ ] Test with sample inputs
- [ ] Verify skipped when >85% confidence

**STEP 5 (Prompt Engineer):**
- [ ] Create `agents/prompt_engineer.py`
- [ ] Implement `prompt_engineer_node()` async function
- [ ] Add LangMem query call (CRITICAL)
- [ ] Add style reference integration
- [ ] Add JSON parsing and validation
- [ ] Add quality gates
- [ ] Add fallback to original prompt on error
- [ ] Test with all agent outputs available

---

## TESTING STRATEGY

Test each agent individually first:

```python
# Test Context
state = PromptForgeState(
    original_prompt="Build a React component",
    conversation_history=[{"role": "user", "content": "..."}]
)
result = await context_node(state)
assert "context" in result["breakdown"]

# Test Domain
state = PromptForgeState(
    original_prompt="FastAPI POST endpoint with SQLAlchemy",
)
result = await domain_node(state)
assert result["breakdown"]["domain"]["primary_domain"] in ["fastapi", "sqlalchemy"]

# Test Engineer with full breakdown
state["breakdown"] = {
    "intent": {...},
    "context": {...},
    "domain": {...}
}
result = await prompt_engineer_node(state)
assert result["improved_prompt"] != state["original_prompt"]
```

---

## PERFORMANCE EXPECTATIONS

| Agent | Time | Notes |
|-------|------|-------|
| Context | 400-600ms | Can be skipped |
| Domain | 400-600ms | Can be skipped |
| Engineer | 1000-1500ms | Never skipped |
| All 3 parallel | ~1600ms | Max of all + overhead |

---

## NEXT STEPS

1. Implement STEP_3, test locally
2. Implement STEP_4, test locally
3. Implement STEP_5 with LangMem, test locally
4. Move to STEP_6 (LangGraph Workflow) to connect them

