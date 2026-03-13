# SPECIFICATION: Memory Personalization Enhancements

**Version:** 1.0  
**Date:** 2026-03-13  
**Status:** APPROVED FOR IMPLEMENTATION  
**Compliance:** RULES.md v1.0  
**Implementation Time:** 90 minutes estimated

---

## 1. OVERVIEW

### 1.1 Purpose
Enhance memory system utilization to deliver on core value proposition: "More usage = richer profile = smarter responses"

### 1.2 Problem Statement
Current memory system rates 3.2/5 due to underutilization:
- `ai_frustration` saved but never used
- Memory content queried but only count shown to Kira
- Quality scores saved but trend hardcoded as "stable"
- `audience` preference saved but not applied

### 1.3 Goals
| Goal | Metric | Target |
|------|--------|--------|
| Memory Application Rating | Current: 3/5 | → 4.5/5 |
| Onboarding Honesty | Current: 60% | → 100% |
| Personalization Depth | Surface level | → Deep |
| User-Perceived Intelligence | "Remembers me" | → "Understands me" |

### 1.4 Non-Goals
- No database schema changes
- No new API endpoints
- No frontend changes (backend-only)
- No breaking changes to existing flows

---

## 2. REQUIREMENTS

### 2.1 Functional Requirements

#### FR-1: AI Frustration Usage (P1)
**ID:** `FR-1`  
**Priority:** P0 (Blocking MVP)  
**Description:** System MUST use `ai_frustration` from onboarding to constrain Prompt Engineer output

**Acceptance Criteria:**
- [ ] When `ai_frustration = 'too_vague'`, output includes specific examples
- [ ] When `ai_frustration = 'too_wordy'`, output is concise
- [ ] When `ai_frustration = 'too_brief'`, output includes detailed explanations
- [ ] When `ai_frustration = 'wrong_tone'`, output matches audience tone
- [ ] When `ai_frustration = 'repeats'`, output avoids redundancy
- [ ] When `ai_frustration = 'misses_context'`, output considers full context
- [ ] Latency impact: 0ms (string concatenation only)

**Test Cases:**
```python
TC-FR-1.1: User with 'too_vague' frustration → Output has concrete examples
TC-FR-1.2: User with 'too_wordy' frustration → Output is concise
TC-FR-1.3: User with no frustration → No constraint added (graceful fallback)
```

---

#### FR-2: Memory Content for Kira (P2)
**ID:** `FR-2`  
**Priority:** P0 (Blocking MVP)  
**Description:** Kira MUST see actual memory content (not just count) for routing decisions

**Acceptance Criteria:**
- [ ] Kira sees top 3 memory content previews (60 chars each)
- [ ] Kira sees quality score for each memory
- [ ] Memory preview formatted as bullet list
- [ ] Latency impact: <5ms (string formatting only)

**Test Cases:**
```python
TC-FR-2.1: User with 5 memories → Kira sees top 3 with content
TC-FR-2.2: User with 0 memories → No preview shown (graceful fallback)
TC-FR-2.3: User with 1 memory → Kira sees that 1 memory
```

---

#### FR-3: Quality Trend Analysis (P3)
**ID:** `FR-3`  
**Priority:** P1 (Phase 3 Blocker)  
**Description:** System MUST calculate quality trend from last 10 sessions

**Acceptance Criteria:**
- [ ] Trend calculated from last 10 `quality_score.overall` values
- [ ] Returns: 'improving' | 'stable' | 'declining' | 'insufficient_data'
- [ ] Threshold: 0.1 change minimum (avoid noise)
- [ ] Calculation: Compare first 5 vs last 5 averages
- [ ] Runs as background task (user never waits)
- [ ] Latency impact: +50ms (background, user-perceived: 0ms)

**Test Cases:**
```python
TC-FR-3.1: 10 sessions, avg improves 0.2 → Returns 'improving'
TC-FR-3.2: 10 sessions, avg declines 0.2 → Returns 'declining'
TC-FR-3.3: 10 sessions, avg changes <0.1 → Returns 'stable'
TC-FR-3.4: <3 sessions → Returns 'insufficient_data'
TC-FR-3.5: Query fails → Returns 'stable' (graceful fallback)
```

---

#### FR-4: Audience Adaptation (P4)
**ID:** `FR-4`  
**Priority:** P1 (Enhancement)  
**Description:** System MUST use `audience` preference to constrain output style

**Acceptance Criteria:**
- [ ] When `audience = 'technical'`, use precise terminology
- [ ] When `audience = 'business'`, focus on ROI/practical outcomes
- [ ] When `audience = 'general'`, avoid jargon, explain clearly
- [ ] When `audience = 'academic'`, use formal tone, cite sources
- [ ] When `audience = 'creative'`, use evocative language
- [ ] Latency impact: 0ms (string concatenation only)

**Test Cases:**
```python
TC-FR-4.1: User with 'technical' audience → Output uses jargon
TC-FR-4.2: User with 'general' audience → Output explains concepts
TC-FR-4.3: User with no audience → No constraint added (graceful fallback)
```

---

### 2.2 Non-Functional Requirements

#### NFR-1: Performance
- **Latency:** P1/P2/P4 add 0ms, P3 adds 50ms (background)
- **User-perceived latency:** 0ms for all changes
- **Memory usage:** No increase (reusing existing queries)

#### NFR-2: Reliability
- **Error handling:** All functions must have try/catch with graceful fallback
- **Logging:** All constraint additions logged at DEBUG level
- **Fallback behavior:** Missing data → silent skip (no errors)

#### NFR-3: Security
- **RLS:** All queries must use `auth.uid() = user_id`
- **No new attack surface:** String concatenation only (no SQL injection risk)

#### NFR-4: Maintainability
- **Type hints:** All functions must have complete type annotations
- **Docstrings:** NumPy style with Parameters, Returns, Examples
- **Constants:** Frustration/audience constraints as module-level constants

---

## 3. DESIGN

### 3.1 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ IMPLEMENTATION ARCHITECTURE                                 │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐     ┌──────────────────┐
│ prompt_engineer  │     │   autonomous     │
│     .py          │     │     .py          │
├──────────────────┤     ├──────────────────┤
│ + frustration    │     │ + memory content │
│   constraint     │     │   preview        │
│ + audience       │     │                  │
│   constraint     │     │                  │
└──────────────────┘     └──────────────────┘
         ↑                        ↑
         │                        │
         └──────────┬─────────────┘
                    │
         ┌──────────▼─────────────┐
         │   user_profile (dict)  │
         │   - ai_frustration     │
         │   - audience           │
         │   - preferred_tone     │
         └────────────────────────┘

┌──────────────────┐
│   langmem.py     │
├──────────────────┤
│ + get_quality_   │
│   trend()        │
└──────────────────┘
         ↑
         │
         └─── Queries langmem_memories
              Calculates trend
              Returns: 'improving'|'stable'|'declining'
```

### 3.2 Data Flow

#### FR-1 + FR-4 (Prompt Engineer):
```
User Profile → prompt_engineer_agent()
    ↓
Extract: ai_frustration, audience
    ↓
Build constraint strings (if/elif chain)
    ↓
Append to style_context
    ↓
LLM receives constraints
    ↓
Output matches preferences
```

#### FR-2 (Kira Orchestrator):
```
query_langmem() → 5 memories
    ↓
Extract top 3 content + quality_score
    ↓
Format as bullet list (60 chars each)
    ↓
Append to profile_context
    ↓
Kira LLM sees content
    ↓
Better routing decisions
```

#### FR-3 (Quality Trend):
```
update_user_profile() (every 5th interaction)
    ↓
Call get_quality_trend(user_id)
    ↓
Query last 10 quality_scores
    ↓
Calculate avg(first 5) vs avg(last 5)
    ↓
Compare with 0.1 threshold
    ↓
Return: 'improving'|'stable'|'declining'
    ↓
Save to user_profiles.prompt_quality_trend
```

---

## 4. IMPLEMENTATION PLAN

### 4.1 File Changes

| File | Change Type | Lines | Phase |
|------|-------------|-------|-------|
| `agents/prompt_engineer.py` | MODIFY | +27 | P1 + P4 |
| `agents/autonomous.py` | MODIFY | +10 | P2 |
| `memory/langmem.py` | ADD FUNCTION | +40 | P3 |
| `memory/profile_updater.py` | MODIFY | +2 | P3 |

### 4.2 Implementation Order

```
PHASE 1 (30 minutes):
  1. FR-1: ai_frustration usage (10 min)
  2. FR-2: Memory content for Kira (10 min)
  3. FR-4: Audience adaptation (10 min)

PHASE 2 (60 minutes):
  4. FR-3: Quality trend analysis (45 min)
  5. Testing & verification (15 min)
```

---

## 5. TESTING STRATEGY

### 5.1 Unit Tests

```python
# tests/test_memory_personalization.py

class TestFrustrationConstraints:
    def test_too_vague_constraint(self):
        """Verify 'too_vague' adds specificity constraint."""
        
    def test_too_wordy_constraint(self):
        """Verify 'too_wordy' adds conciseness constraint."""
    
    def test_no_frustration_graceful_skip(self):
        """Verify missing frustration doesn't break."""

class TestMemoryContent:
    def test_memory_preview_formatting(self):
        """Verify top 3 memories formatted correctly."""
    
    def test_zero_memories_graceful_skip(self):
        """Verify 0 memories doesn't break."""

class TestQualityTrend:
    def test_improving_trend(self):
        """Verify improving trend detected."""
    
    def test_declining_trend(self):
        """Verify declining trend detected."""
    
    def test_stable_trend(self):
        """Verify stable trend when change < 0.1."""
    
    def test_insufficient_data(self):
        """Verify <3 sessions returns insufficient_data."""

class TestAudienceConstraints:
    def test_technical_audience(self):
        """Verify technical audience uses jargon."""
    
    def test_general_audience(self):
        """Verify general audience avoids jargon."""
```

### 5.2 Integration Tests

```python
# tests/test_personalization_integration.py

class TestEndToEndPersonalization:
    def test_full_personalization_flow(self):
        """
        1. User completes onboarding (coding + technical + too_vague)
        2. User sends 3 chat messages
        3. Verify: Output is specific, technical, concise
        4. Verify: Kira references past sessions
        5. Verify: Quality trend calculated after 5th
        """
```

---

## 6. DEPLOYMENT PLAN

### 6.1 Pre-Deployment Checklist
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Lint checks passing (`npm run lint`, `flake8`)
- [ ] Type checks passing (`tsc --noEmit`, `mypy`)
- [ ] Local testing with real user data
- [ ] Staging deployment verified

### 6.2 Rollout Strategy
```
Stage 1: Local testing (10 minutes)
  - Test with mock user profiles
  - Verify all 6 frustration types
  - Verify all 5 audience types

Stage 2: Staging deployment (10 minutes)
  - Deploy to staging environment
  - Test with production-like data
  - Verify logs show constraints added

Stage 3: Production deployment (5 minutes)
  - Deploy to production
  - Monitor logs for errors
  - Verify no latency increase
```

### 6.3 Rollback Plan
If issues detected:
```bash
# Revert to previous commit
git revert HEAD~1
# Redeploy
python main.py
# Verify logs show no errors
```

---

## 7. MONITORING & SUCCESS METRICS

### 7.1 Logging Requirements

```python
# All constraint additions logged at DEBUG level
logger.debug(f"[prompt_engineer] frustration constraint added: {frustration}")
logger.debug(f"[prompt_engineer] audience constraint added: {audience}")
logger.debug(f"[kira] memory preview: {len(langmem_context)} memories")
logger.info(f"[langmem] quality trend for {user_id[:8]}: {trend}")
```

### 7.2 Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Memory Application Rating | 3.2/5 | 4.5/5 | Code audit |
| Onboarding Questions Used | 60% | 100% | Constraint logging |
| Kira Memory Awareness | Count only | Content + Count | Log analysis |
| Quality Trend Accuracy | N/A (hardcoded) | Calculated | DB comparison |
| User-Perceived Latency | 3-5s | 3-5s (unchanged) | Response time logs |

### 7.3 Alerting
- **Error rate > 1%:** Page on-call
- **Latency increase > 100ms:** Investigate
- **Constraint skip rate > 5%:** Check profile loading

---

## 8. RULES.md COMPLIANCE

### 8.1 Code Quality Standards
- ✅ Type hints on all functions (mandatory)
- ✅ NumPy-style docstrings (mandatory)
- ✅ Error handling with try/catch (mandatory)
- ✅ Contextual logging (mandatory)

### 8.2 DRY Principles
- ✅ Frustration constraints as module-level constant
- ✅ Audience constraints as module-level constant
- ✅ Extracted helper function for trend calculation

### 8.3 Performance Optimization
- ✅ Background task for quality trend (user never waits)
- ✅ No additional API calls (string concatenation only)
- ✅ Reuse existing query_langmem() call

### 8.4 Security Rules
- ✅ RLS enforced (all queries use user_id)
- ✅ No SQL injection risk (parameterized queries)
- ✅ No secrets in code (all from .env)

---

## 9. APPROVAL

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | |
| Tech Lead | | | |
| Backend Engineer | | | |

---

## 10. CHANGE LOG

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-03-13 | Initial specification | AI Agent |

---

**END OF SPECIFICATION**
