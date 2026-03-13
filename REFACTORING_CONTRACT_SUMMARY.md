# PromptForge v2.0 — Refactoring Contract Summary

**Version:** 1.0  
**Date:** 2026-03-13  
**Status:** ✅ READY FOR IMPLEMENTATION  
**Compliance:** RULES.md v1.0

---

## 📋 CONTRACT OVERVIEW

### Three Phases. Three Tabs. Complete Transformation.

```
Phase 1: Chat Tab      → Multi-Chat Support        (5-7 days)
Phase 2: History Tab   → Intelligent Memory Palace (5-7 days)
Phase 3: Profile Tab   → Living Digital Twin       (5-7 days)
                                              ──────────────
Total: 15-21 days (3 weeks)
```

---

## 🎯 WHAT YOU GET

### Before Refactoring

```
┌─────────────────────────────────────────────────────┐
│ [Chat]  [History]  [Profile]                        │
├─────────────────────────────────────────────────────┤
│ • Single chat session                              │
│ • Flat history list                                │
│ • Basic profile stats                              │
│ • No search                                        │
│ • No analytics                                     │
└─────────────────────────────────────────────────────┘
```

### After Refactoring

```
┌─────────────────────────────────────────────────────┐
│ [Chat]  [History]  [Profile]                        │
├─────────────────────────────────────────────────────┤
│ Chat:                                               │
│  • Multi-session sidebar                            │
│  • Create/delete/rename chats                       │
│  • Session switching                                │
│                                                     │
│ History:                                            │
│  • Semantic search (LangMem RAG)                    │
│  • Session grouping                                 │
│  • Domain filtering                                 │
│  • Analytics dashboard                              │
│                                                     │
│ Profile:                                            │
│  • Editable username                                │
│  • Domain niches (confidence visualization)         │
│  • LangMem memory preview                           │
│  • Quality trend sparkline                          │
│  • Usage statistics                                 │
└─────────────────────────────────────────────────────┘
```

---

## 📦 DELIVERABLES

### Phase 1: Chat Tab (Multi-Chat)

**Backend Files:**
- ✅ `api.py` — ADD 4 endpoints (`/sessions` POST/GET/PATCH/DELETE)
- ✅ `database.py` — ADD 3 functions (create, get, update sessions)
- ✅ `migrations/015_add_chat_sessions.sql` — NEW table

**Frontend Files:**
- ✅ `features/chat/hooks/useChatSessions.ts` — NEW hook
- ✅ `features/chat/components/ChatSidebar.tsx` — NEW component
- ✅ `features/chat/types.ts` — ADD ChatSession interface
- ✅ `features/chat/components/ChatContainer.tsx` — MODIFY with sidebar

**Acceptance Criteria:**
- [ ] User can create new chat sessions
- [ ] User can switch between sessions
- [ ] User can delete sessions
- [ ] User can rename sessions
- [ ] Sidebar responsive (mobile + desktop)
- [ ] RLS policies enforced
- [ ] All tests passing

---

### Phase 2: History Tab (Memory Palace)

**Backend Files:**
- ✅ `api.py` — ADD 3 endpoints (`/history/search`, `/history/sessions`, `/history/analytics`)
- ✅ `database.py` — ADD 1 function (get_user_analytics)
- ✅ `migrations/016_add_history_indexes.sql` — Performance indexes

**Frontend Files:**
- ✅ `features/history/hooks/useHistorySearch.ts` — NEW hook
- ✅ `features/history/components/HistorySearchBar.tsx` — NEW component
- ✅ `features/history/components/SessionGroup.tsx` — NEW component
- ✅ `features/history/components/HistoryAnalytics.tsx` — NEW component

**Acceptance Criteria:**
- [ ] Semantic search working (LangMem RAG)
- [ ] Sessions grouped by conversation
- [ ] Domain filter chips functional
- [ ] Analytics dashboard displays stats
- [ ] Quality trend chart renders
- [ ] All queries use RLS
- [ ] All tests passing

---

### Phase 3: Profile Tab (Digital Twin)

**Backend Files:**
- ✅ `api.py` — ADD 5 endpoints (`/user/username`, `/user/domains`, `/user/memories`, `/user/quality-trend`, `/user/stats`)
- ✅ `database.py` — NO CHANGES (uses existing functions)
- ✅ `migrations/017_add_username_to_profiles.sql` — ADD username column

**Frontend Files:**
- ✅ `features/profile/hooks/useProfile.ts` — MODIFY (add username, domains, memories)
- ✅ `features/profile/components/UsernameEditor.tsx` — NEW component
- ✅ `features/profile/components/DomainNiches.tsx` — NEW component
- ✅ `features/profile/components/LangMemPreview.tsx` — NEW component

**Acceptance Criteria:**
- [ ] Username editable with validation
- [ ] Domain niches show confidence dots
- [ ] LangMem memories preview visible
- [ ] Quality trend sparkline interactive
- [ ] Usage statistics dashboard complete
- [ ] All tests passing

---

## 🏗️ ARCHITECTURE PRINCIPLES

### Following RULES.md v1.0

1. **Spec-Driven Development**
   - Every function has type hints
   - Every function has docstring
   - Every endpoint has schema
   - Every change has tests

2. **No AI Slop**
   - Readable, maintainable code
   - Senior-level quality standards
   - Clear variable names
   - Proper error handling

3. **Current Theme Preservation**
   - Dark mode maintained
   - Kira branding preserved
   - Minimalist aesthetic enhanced
   - No visual debt added

4. **LangMem Integration**
   - Every tab showcases LangMem
   - Gemini embeddings visible
   - RAG search functional
   - Memory preview in profile

5. **Security First**
   - JWT on all endpoints
   - RLS on all queries
   - Input validation everywhere
   - No secrets in code

---

## 🧪 TESTING STRATEGY

### Backend Tests (Python)

```python
# tests/test_phase1_chat_sessions.py
# tests/test_phase2_history_search.py
# tests/test_phase3_profile.py

class TestPhase1:
    def test_create_session(self, auth_client): ...
    def test_list_sessions(self, auth_client): ...
    def test_delete_session(self, auth_client): ...
    def test_rls_isolation(self, auth_client, another_user): ...

class TestPhase2:
    def test_semantic_search(self, auth_client): ...
    def test_session_grouping(self, auth_client): ...
    def test_analytics(self, auth_client): ...

class TestPhase3:
    def test_update_username(self, auth_client): ...
    def test_get_domains(self, auth_client): ...
    def test_get_memories(self, auth_client): ...
```

### Frontend Tests (TypeScript)

```typescript
// features/chat/hooks/__tests__/useChatSessions.test.ts
// features/history/hooks/__tests__/useHistorySearch.test.ts
// features/profile/hooks/__tests__/useProfile.test.ts

describe('useChatSessions', () => {
  it('loads sessions on mount', async () => { ... })
  it('creates new session', async () => { ... })
  it('deletes session', async () => { ... })
})
```

---

## 🚀 DEPLOYMENT PLAN

### Pre-Deployment Checklist

- [ ] All TypeScript compilation errors resolved
- [ ] All Python type hints present
- [ ] All docstrings complete
- [ ] All tests passing (backend + frontend)
- [ ] Migration scripts tested locally
- [ ] Environment variables documented
- [ ] Docker image builds successfully
- [ ] Frontend builds without errors

### Deployment Steps

**1. Database Migrations**
```sql
-- Run in Supabase SQL Editor in order:
migrations/015_add_chat_sessions.sql
migrations/016_add_history_indexes.sql
migrations/017_add_username_to_profiles.sql
```

**2. Backend Deployment**
```bash
# Rebuild Docker image
docker build -t godkenny/promptforge-api:latest .

# Push to Docker Hub
docker push godkenny/promptforge-api:latest

# Koyeb auto-deploys (or trigger manually)
```

**3. Frontend Deployment**
```bash
# If using Vercel:
git add .
git commit -m "Refactoring Phases 1-3 complete"
git push origin main

# Vercel auto-deploys
```

### Post-Deployment Verification

- [ ] Health check passes: `GET /health`
- [ ] Create chat session works
- [ ] Semantic search returns results
- [ ] Profile username updates
- [ ] No errors in Sentry logs
- [ ] Performance acceptable (Langfuse)
- [ ] Mobile responsive verified
- [ ] RLS policies working (test with 2 users)

---

## 📊 SUCCESS METRICS

### User Experience Metrics

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Multi-chat support | ❌ | ✅ | User can create 5+ chats |
| Search functionality | ❌ | ✅ | Semantic search <500ms |
| Session organization | Flat | Grouped | Sessions grouped by conversation |
| Profile personalization | Basic | Complete | Username + domains + memories |
| Analytics visibility | None | Full | Dashboard with 6+ metrics |

### Technical Metrics

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Type coverage | 85% | 100% | TypeScript + mypy |
| Test coverage | 60% | 90% | pytest + jest |
| API response time | 2-5s | <3s | P95 latency |
| LangMem integration | Chat only | All tabs | RAG in history, profile |
| Security score | A | A+ | All RLS, JWT, validation |

---

## 🎯 CONTRACT SIGN-OFF

### Implementation Team

**Backend Lead:**
- [ ] Reviewed all backend contracts
- [ ] Understood endpoint specifications
- [ ] Committed to RULES.md compliance
- [ ] Signature: _________________ Date: _______

**Frontend Lead:**
- [ ] Reviewed all frontend contracts
- [ ] Understood component specifications
- [ ] Committed to type-safe code
- [ ] Signature: _________________ Date: _______

**QA Lead:**
- [ ] Reviewed all test requirements
- [ ] Prepared test plans
- [ ] Committed to 90%+ coverage
- [ ] Signature: _________________ Date: _______

---

## 📞 NEXT STEPS

### Ready to Start?

1. **Review all 3 phase contracts:**
   - `REFACTORING_CONTRACT_PHASE_1.md` (Chat)
   - `REFACTORING_CONTRACT_PHASE_2.md` (History)
   - `REFACTORING_CONTRACT_PHASE_3.md` (Profile)

2. **Run migrations in Supabase:**
   - 015, 016, 017 (in order)

3. **Start with Phase 1:**
   - Backend endpoints first
   - Then frontend components
   - Then tests

4. **Deploy incrementally:**
   - Phase 1 complete → Deploy → Test
   - Phase 2 complete → Deploy → Test
   - Phase 3 complete → Deploy → Test

### Questions?

Refer to:
- `DOCS/RULES.md` — Engineering standards
- `REFACTORING_CONTRACT_PHASE_X.md` — Phase specifications
- `COMPREHENSIVE_ANALYSIS_AND_RECOMMENDATIONS.md` — Architecture analysis

---

**Contract Version:** 1.0  
**Created:** 2026-03-13  
**Status:** ✅ READY FOR IMPLEMENTATION  
**Next Review:** After Phase 1 completion

---

*This contract represents a binding agreement between development team and stakeholders. All work must follow RULES.md v1.0 standards. No AI slop. Senior-level code quality required.*
