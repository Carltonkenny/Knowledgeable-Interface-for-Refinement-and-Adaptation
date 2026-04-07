# 🧠 KIRA PERSONALITY & ROUTING — DEEP DIVE ANALYSIS

**Generated:** March 31, 2026  
**Status:** ✅ WORKING — Ready for refinement  
**Files Analyzed:** 8 files across backend + frontend

---

## 📊 EXECUTIVE SUMMARY

### WHAT'S WORKING ✅

| Component | Status | Proof |
|-----------|--------|-------|
| **Personality System Prompt** | ✅ Excellent | `agents/prompts/orchestrator.py:26-180` |
| **Routing Logic (4 routes)** | ✅ Implemented | `orchestrator.py:95-135` |
| **Forbidden Phrases Filter** | ✅ Active | `personality.py:162-179` |
| **Style Adaptation** | ✅ Working | `personality.py:98-135` |
| **Unified Handler** | ✅ Single LLM call | `unified.py:31-145` |
| **Frontend Streaming** | ✅ Typewriter effect | `KiraMessage.tsx:47-52` |

### WHAT CAN BE IMPROVED 🎯

1. **Routing transparency** — Users don't see WHY a route was chosen
2. **Personality consistency** — Some responses still feel generic
3. **Clarification questions** — Could be sharper, more contextual
4. **Memory integration** — LangMem recall is working but underutilized
5. **Frontend display** — No visual indication of routing decisions

---

## 🔍 CURRENT ARCHITECTURE

### 1. ROUTING FLOW (Backend)

```
User Message → Kira Orchestrator → Intent Classification → Route
                      ↓
        ┌─────────────┼─────────────┐
        │             │             │
    CONVERSATION  FOLLOWUP    NEW_PROMPT
    (<10 chars)   (modification)  (full swarm)
```

**File:** `routes/prompts.py:145-200`

**Current Logic:**
```python
# Line 145-158: Intent-based routing
if intent == "CONVERSATION":
    reply = handle_conversation(...)
    return ChatResponse(type="conversation", ...)

elif intent == "FOLLOWUP":
    improved = result.get("improved_prompt", "")
    return ChatResponse(type="followup_refined", ...)

# Line 208: Default to NEW_PROMPT
classification = "NEW_PROMPT"
```

**Problem:** Routing happens in TWO places:
1. Backend orchestrator (`unified.py`) decides intent
2. Backend route handler (`prompts.py`) executes based on intent

**Result:** No transparency for users — they don't know WHY their message was routed a certain way.

---

### 2. PERSONALITY SYSTEM

**File:** `agents/prompts/orchestrator.py:26-85`

**Current Personality Definition:**
```
You are Kira — a prompt engineering AI with a personality 
sharp enough to cut through the noise.

You're that friend who's genuinely good at this stuff and 
doesn't make you feel dumb for asking.
Gen-Z energy. Witty. Direct. A little opinionated.
```

**✅ What's Good:**
- Clear DO / DO NOT lists (lines 47-68)
- Specific examples of what TO say
- Explicit forbidden phrases list
- Tone options: `casual`, `direct`, `technical`, `witty`

**⚠️ What's Missing:**
- No personality "intensity" slider (how witty vs professional?)
- No handling for edge cases (angry users, confused users)
- No escalation path for when personality clashes with user needs

---

### 3. STYLE ADAPTATION

**File:** `agents/orchestration/personality.py:37-96`

**How It Works:**
```python
def adapt_kira_personality(message, user_profile, response_text):
    detected = _detect_user_style(message)      # Analyze user's message
    blended = _blend_with_profile(detected, profile)  # 70% profile + 30% message
    guidance = _get_adaptation_guidance(blended)  # Generate adaptation rules
    forbidden = check_forbidden_phrases(response_text)  # Validate
    return PersonalityAdaptation(...)
```

**Detection Signals:**
```python
casual_signals = ["u ", "pls", "thx", "gonna", "wanna", "hey", "lol"]
formal_signals = ["please", "thank you", "could you", "kindly", "regards"]
tech_signals = ["api", "function", "async", "database", "query", "code"]
```

**✅ Working:** Style detection is functional  
**⚠️ Issue:** Adaptation happens BUT isn't always applied to final response

---

### 4. FRONTEND DISPLAY

**File:** `promptforge-web/features/chat/components/KiraMessage.tsx`

**Current UI:**
```tsx
<div className="w-8 h-8 rounded-lg border border-kira/30 bg-kira/10">
  <span className="text-kira font-bold font-mono text-sm">K</span>
</div>
```

**What's Shown:**
- ✅ Avatar ("K" in a box)
- ✅ Message text with **bold** parsing
- ✅ Streaming cursor (blinking line)
- ✅ Retry button on error

**What's NOT Shown:**
- ❌ Which route was chosen (CONVERSATION/FOLLOWUP/SWARM)
- ❌ Why that route was chosen
- ❌ Which agents are running
- ❌ Personality adaptation status
- ❌ Memory recall status

---

## 🎯 IMPROVEMENT OPPORTUNITIES

### TIER 1: HIGH IMPACT, LOW EFFORT 🔴

#### 1. Add Route Transparency to Frontend

**Current:**
```
K: "On it — engineering a precise prompt..."
```

**Better:**
```
K: "On it — engineering a precise prompt..."
   [Route: SWARM | Agents: intent, context, domain | 2.8s]
```

**Implementation:**
- Backend: Add `route` and `agents_to_run` to SSE events
- Frontend: Add small metadata chip below Kira message
- File: `prompts.py:300-350` (streaming endpoint)

**Impact:** Users understand WHAT's happening and WHY

---

#### 2. Sharper Clarification Questions

**Current:**
```
"AI is a big topic — are you writing for technical readers 
who already know the basics, or explaining it to someone 
completely new?"
```

**Better (Contextual):**
```
"Quick one — is this for a deadline today or do you have 
time to iterate?"

"Your profile shows you work in marketing — is this for 
internal docs or customer-facing content?"

"Based on your last 3 prompts, you like direct technical 
style — want me to keep that or try something different?"
```

**Implementation:**
- File: `orchestrator.py:145-155` (clarification logic)
- Add memory-aware question generation
- Inject user profile context into question

**Impact:** Questions feel personalized, not generic

---

#### 3. Personality "Intensity" Slider

**Current:** Binary (casual vs formal, technical vs general)

**Better:** Add intensity levels
```python
personality_config = {
    "wit_level": 0.3,      # 0.0 = serious, 1.0 = very witty
    "directness": 0.7,     # 0.0 = gentle, 1.0 = blunt
    "emoji_frequency": 0.5, # 0.0 = none, 1.0 = frequent
    "profanity_tolerance": 0.0  # Always 0 for professional tool
}
```

**Implementation:**
- Add to user profile table: `personality_preferences` JSON column
- Inject into orchestrator prompt
- File: `orchestrator.py:26-40` (system prompt)

**Impact:** Users can tune Kira to their preference

---

### TIER 2: MEDIUM IMPACT, MEDIUM EFFORT 🟡

#### 4. Route Explanation on Hover

**UI Mock:**
```
┌─────────────────────────────────────────┐
│ K: On it — firing the swarm 🚀          │
│    ───────────────────────────────      │
│    [ℹ️ Why swarm?] (tooltip)            │
│                                         │
│    Your prompt scored 4.2/5 clarity —   │
│    no clarification needed. Running     │
│    intent + context agents (domain      │
│    skipped: profile confidence 0.91)    │
└─────────────────────────────────────────┘
```

**Implementation:**
- Backend: Add `route_explanation` to response
- Frontend: Add tooltip component
- File: `KiraMessage.tsx` (add tooltip)

**Impact:** Educational — users learn prompt engineering

---

#### 5. Memory Recall Visualization

**Current:** LangMem queries happen silently

**Better:**
```
K: "Pulling from your last session about React hooks..."
   [🧠 3 memories applied | Focus: coding, React, performance]
```

**Implementation:**
- Backend: Add `memories_applied` count + topics to SSE
- Frontend: Add memory chip (already exists in OutputCard!)
- File: `unified.py:105-115` (memory summary)

**Impact:** Users see memory is actually working

---

#### 6. Personality Consistency Checker

**Problem:** Some responses still slip into generic AI-speak

**Solution:** Add post-response validation
```python
def validate_kira_response(response: str) -> Tuple[bool, List[str]]:
    """Check response matches Kira personality."""
    violations = []
    
    # Check forbidden phrases
    for phrase in FORBIDDEN_PHRASES:
        if phrase.lower() in response.lower():
            violations.append(f"Contains '{phrase}'")
    
    # Check personality markers
    if len(response) < 20:
        violations.append("Too brief for Kira's style")
    
    # Check for warmth markers (should have at least 1)
    warmth_markers = ["✨", "🚀", "got it", "on it", "let's"]
    if not any(m in response.lower() for m in warmth_markers):
        violations.append("Missing warmth markers")
    
    return len(violations) == 0, violations
```

**Implementation:**
- File: `personality.py` (new function)
- Call before returning response
- Log violations, don't block (performance)

**Impact:** More consistent personality over time

---

### TIER 3: HIGH IMPACT, HIGH EFFORT 🟢

#### 7. User-Configurable Personality Presets

**Presets:**
```
┌─────────────────────────────────────────┐
│ Kira Personality Settings               │
│                                         │
│ ○ Professional                          │
│   Direct, minimal emoji, no jokes       │
│                                         │
│ ● Balanced (Default)                    │
│   Warm but efficient, occasional wit    │
│                                         │
│ ○ Casual                                │
│   More emoji, playful, conversational   │
│                                         │
│ ○ Mentor                                │
│   Educational, explains decisions       │
└─────────────────────────────────────────┘
```

**Implementation:**
- Add `personality_preset` to user_profiles table
- Inject preset into orchestrator system prompt
- File: `orchestrator.py:26-40` (add preset-specific instructions)

**Impact:** Users feel ownership over Kira's personality

---

#### 8. Route Override (User Can Force Swarm)

**Current:** If Kira routes to CONVERSATION, user can't override

**Better:**
```
K: "Hey! What would you like to work on today?"
   [💬 Just chatting]  [🚀 Fire swarm anyway]
```

**Implementation:**
- Frontend: Add "Force swarm" button on CONVERSATION responses
- Backend: Add `/chat?force_swarm=true` parameter
- File: `prompts.py:145` (add force_swarm check)

**Impact:** Users feel in control

---

#### 9. A/B Test Personality Variations

**Hypothesis:** Witty Kira has higher retention than serious Kira

**Test:**
```python
# Randomly assign users to personality variants
variant = hash(user_id) % 3
if variant == 0:
    personality = "witty"    # More jokes, more emoji
elif variant == 1:
    personality = "direct"   # Minimal fluff, straight to work
else:
    personality = "mentor"   # Educational, explains decisions
```

**Metrics to Track:**
- Session length
- Prompts per session
- Return rate (D1, D7, D30)
- Quality score improvement over time

**Implementation:**
- Add `personality_variant` to user_profiles
- Log variant to analytics
- File: `prompts.py:140` (inject variant)

**Impact:** Data-driven personality optimization

---

## 📋 RECOMMENDED IMPLEMENTATION ORDER

### PHASE 1: TRANSPARENCY (Week 1)
1. ✅ Add route metadata to frontend (TIER 1, #1)
2. ✅ Add memory recall visualization (TIER 2, #5)
3. ✅ Sharper clarification questions (TIER 1, #2)

**Time:** 4-6 hours  
**Impact:** Users immediately see what's happening

---

### PHASE 2: CONSISTENCY (Week 2)
1. ✅ Personality consistency checker (TIER 2, #6)
2. ✅ Personality intensity slider (TIER 1, #3)
3. ✅ Route explanation tooltip (TIER 2, #4)

**Time:** 6-8 hours  
**Impact:** Kira feels more "real" and consistent

---

### PHASE 3: PERSONALIZATION (Week 3-4)
1. ✅ User-configurable presets (TIER 3, #7)
2. ✅ Route override (TIER 3, #8)
3. ✅ A/B testing framework (TIER 3, #9)

**Time:** 12-16 hours  
**Impact:** Users feel ownership, higher retention

---

## 🔧 TECHNICAL DEBT TO ADDRESS

### 1. Dual Intent Classification

**Problem:** Intent is classified TWICE:
1. `unified_handler()` classifies intent
2. `prompts.py` re-classifies based on keywords

**File:** `prompts.py:145-165`

**Fix:** Trust unified handler's intent, remove duplicate logic

---

### 2. Memory Underutilization

**Problem:** LangMem recalls 5 memories but only uses count, not content

**File:** `unified.py:105-115`

**Fix:** Inject specific memory topics into Kira's response
```python
memory_summary = f"Recalled {len(langmem_context)} memories, 
focusing on your work in {topic_str}."
```

---

### 3. No Personality Metrics

**Problem:** No way to measure if personality is working

**Fix:** Add personality metrics to analytics:
- Forbidden phrase violations per 100 responses
- Average response length by route
- User retention by personality variant

---

## 🎨 FRONTEND UI MOCKS

### CURRENT (What You Have)
```
┌──────────────────────────────┐
│  K                           │
│  On it — engineering a       │
│  precise prompt...           │
│  ▌                           │
└──────────────────────────────┘
```

### BETTER (With Transparency)
```
┌─────────────────────────────────────────┐
│  K                                      │
│  On it — firing the swarm 🚀            │
│  ▌                                      │
│  ─────────────────────────────────      │
│  [⚡ Route: SWARM] [🧠 3 memories]      │
│  [🤖 Agents: intent, context, domain]   │
└─────────────────────────────────────────┘
```

### BEST (With Tooltip Explanation)
```
┌─────────────────────────────────────────┐
│  K                                      │
│  On it — firing the swarm 🚀            │
│  ▌                                      │
│  ─────────────────────────────────      │
│  [ℹ️ Why swarm?]                        │
│                                         │
│  Your prompt scored 4.2/5 clarity —     │
│  no clarification needed. Running       │
│  intent + context agents (domain        │
│  skipped: profile confidence 0.91)      │
│                                         │
│  [🧠 3 memories applied]                │
│  [⏱️ ETA: ~3s]                          │
└─────────────────────────────────────────┘
```

---

## 📊 METRICS TO TRACK

### Personality Health
| Metric | Target | Current |
|--------|--------|---------|
| Forbidden phrase violations | <1% | ❓ Unknown |
| Avg response length (CONVERSATION) | 15-40 words | ❓ Unknown |
| Personality consistency score | >0.85 | ❓ Unknown |

### Routing Effectiveness
| Metric | Target | Current |
|--------|--------|---------|
| Clarification → Swarm conversion | >80% | ❓ Unknown |
| CONVERSATION → FOLLOWUP rate | <20% | ❓ Unknown |
| Avg agents per SWARM | 2.5-3.5 | ❓ Unknown |

### User Satisfaction
| Metric | Target | Current |
|--------|--------|---------|
| Session length | >5 min | ❓ Unknown |
| Prompts per session | >3 | ❓ Unknown |
| D7 retention | >40% | ❓ Unknown |

---

## 🚀 QUICK WINS (Do These First)

### 1. Add Route Chip to Frontend (30 min)

**File:** `KiraMessage.tsx`

```tsx
// Add below message
{metadata?.route && (
  <div className="mt-2 flex gap-2">
    <span className="px-2 py-0.5 rounded bg-kira/10 text-kira text-[10px] font-mono">
      {metadata.route}
    </span>
    {metadata.agents_to_run && (
      <span className="px-2 py-0.5 rounded bg-border-default text-text-dim text-[10px] font-mono">
        🤖 {metadata.agents_to_run.join(', ')}
      </span>
    )}
  </div>
)}
```

---

### 2. Sharpen Clarification Questions (1 hour)

**File:** `orchestrator.py:145-155`

**Add:**
```python
# Inject user profile context
if user_profile.get("dominant_domains"):
    domain = user_profile["dominant_domains"][0]
    question = f"Is this for {domain} work, or something different?"
else:
    question = "Quick one — is this for a deadline today or do you have time to iterate?"
```

---

### 3. Personality Consistency Logging (1 hour)

**File:** `personality.py` (new function)

```python
def log_personality_violations(response: str, violations: List[str]):
    """Log violations without blocking response."""
    if violations:
        logger.warning(f"[kira_personality] violations: {violations}")
        # Could send to analytics here
```

---

## 🎯 FINAL RECOMMENDATIONS

### DO NOW (This Week)
1. ✅ Add route transparency to frontend
2. ✅ Sharpen clarification questions
3. ✅ Add personality consistency logging

### DO NEXT (Next Week)
1. ✅ Memory recall visualization
2. ✅ Route explanation tooltip
3. ✅ Personality intensity slider

### DO LATER (Next Month)
1. ✅ User-configurable presets
2. ✅ Route override
3. ✅ A/B testing framework

---

## 📁 FILES TO MODIFY

| File | Change | Priority | Lines |
|------|--------|----------|-------|
| `KiraMessage.tsx` | Add route chip | 🔴 HIGH | 55-70 |
| `orchestrator.py` | Sharper questions | 🔴 HIGH | 145-155 |
| `personality.py` | Consistency checker | 🟡 MEDIUM | 180-220 |
| `prompts.py` | Add route to SSE | 🟡 MEDIUM | 300-350 |
| `unified.py` | Memory summary | 🟢 LOW | 105-115 |

---

**READY TO IMPLEMENT?** Pick a tier and I'll code it up.
