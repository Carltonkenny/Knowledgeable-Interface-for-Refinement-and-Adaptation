# Overview

**What PromptForge is, who it's for, and where it stands at v2.0.0.**

---

## What Is PromptForge?

PromptForge is a **multi-agent AI prompt engineering platform** that transforms vague, rough prompts into precise, production-ready instructions. It uses a swarm of 4 specialized AI agents orchestrated by "Kira" (a personality-driven routing agent) to analyze intent, build context, identify domain, and synthesize an engineered prompt with quality scores.

**Input (vague):**
```
"write a story about a robot"
```

**Output (engineered):**
```
You are a seasoned science-fiction author. Write a 1,200-word short story set in a
near-future city, told from the first-person perspective of a maintenance robot named
Aria. Blend humor with subtle social commentary, exploring the theme of identity versus
programming. Keep the tone witty yet reflective, suitable for adult readers.
```

The result is typically ~2000% more detailed, with role assignment, audience definition, tone guidance, structural constraints, and quality gates.

---

## Value Proposition

| Problem | Solution |
|---------|----------|
| Vague prompts produce vague results | 4-agent swarm adds specificity, context, constraints |
| No memory of past interactions | LangMem + Supermemory persistent memory with pgvector |
| One-size-fits-all responses | Kira's personality adaptation + user profile learning |
| No quality metrics | Quality scoring (specificity, clarity, actionability) on every output |
| No MCP integration | Native MCP server for Cursor/Claude Desktop with 2 tools |

---

## Who Is It For?

1. **Prompt Engineers** — People who regularly craft prompts for AI tools and want systematic quality improvement
2. **Developers** — Engineers using AI for code generation who need structured, domain-specific prompts
3. **Content Creators** — Writers, marketers, and designers who want AI output matched to their style
4. **MCP Users** — Cursor/Claude Desktop users who want prompt engineering directly in their IDE

---

## v2.0 Status

| Phase | Status | Tests | Details |
|-------|--------|-------|---------|
| **Phase 1: Backend Core** | ✅ Complete | 59 passing | FastAPI, JWT auth, Supabase (8 tables, 38 RLS policies), Redis caching, rate limiting |
| **Phase 2: Agent Swarm** | ✅ Complete | 87 passing | 4-agent parallel swarm (Send() API), Kira orchestrator, LangMem with pgvector, profile updater, multimodal input |
| **Phase 3: MCP Integration** | ✅ Complete | 33 passing | Native MCP server, Supermemory, long-lived JWT (365 days), trust levels (0–2), stdio transport |
| **Phase 4: Frontend** | ⚠️ Uncertain | — | Frontend exists (`promptforge-web/`) with Next.js 16, but audit status unclear |

**Security Compliance:** 92% (12/13 rules passing per RULES.md Section 11)

**Total Production Code:** ~4,400 lines
**Total Test Code:** ~1,500 lines
**Total Documentation:** ~17,000 lines (12 files)

---

## Architecture Summary

```
User Input → Kira (Orchestrator) → Route Decision
                                    ↓
              ┌─────────────────────┼─────────────────────┐
              ↓                     ↓                     ↓
        Intent Agent          Context Agent         Domain Agent
        (parallel)           (parallel)            (parallel)
              ↓                     ↓                     ↓
              └─────────────────────┼─────────────────────┘
                                    ↓
                          Prompt Engineer Agent
                          (synthesizes all outputs)
                                    ↓
                          Quality Gate Validation
                                    ↓
                          Engineered Prompt + Score
```

See [architecture](architecture.md) for full details.

---

## Key Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Cache hit latency | <100ms | ~50ms | ✅ Exceeds |
| Full swarm latency | 3–5s | 4–6s | ⚠️ Close (+20%) |
| LangMem search | <500ms | ~50–100ms | ✅ Exceeds (5–10x) |
| Database query | <50ms | ~30ms | ✅ Exceeds |
| Kira orchestrator | <1s | ~500ms | ✅ Exceeds |
| First token latency | <500ms | ✅ | ✅ |
| Full response time | <10s | ✅ | ✅ |
| Quality score avg | >4.0/5 | ✅ | ✅ |
| Uptime | >99% | ✅ | ✅ |

---

## Sources

The following raw source files were used to compile this overview:

- `README.md` — Project overview, features, tech stack, performance table
- `history/PROJECT_SUMMARY.md` — Phase completion status, metrics, database status, security compliance
- `docs/API.md` — Endpoint overview, rate limits
- `docs/DEPLOYMENT.md` — Deployment targets, monitoring tools
- `agents/README.md` — Agent system description, quality metrics
- `state.py` — State schema (27 fields, 5 sections)
- `workflow.py` — LangGraph workflow structure
- `api.py` — App factory, middleware stack
- `service.py` — Business logic layer
- `config.py` — LLM factory configuration

---

*See also: [architecture](architecture.md), [features](features.md), [tasks](tasks.md)*
