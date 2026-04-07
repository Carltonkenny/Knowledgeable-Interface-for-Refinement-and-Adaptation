# PromptForge Test Prompts — Edge Cases & Stress Tests

## How to Use
Copy each prompt into the chat at http://localhost:3000. After each one:
1. **Check LangFuse** (http://localhost:3001) → Traces tab → see agents that ran, latencies, quality scores
2. **Check Context extraction** → Did it pick up skill level, tone, constraints?
3. **Check Domain classification** → Which domain was detected?
4. **Check Conversation history** → Does the sidebar show the conversation?
5. **Check Quality score** → Is it improving or declining?

---

## Test Category 1: First Message — No History (Context Agent Extracts from Message Alone)

**Goal:** Verify context agent runs even on first message with zero history.

| # | Prompt | What to Verify |
|---|--------|---------------|
| 1 | `hi` | CONVERSATION branch — should reply warmly, NO swarm |
| 2 | `write a python function to sort a list of dictionaries by a nested key` | Technical tone → should detect "expert" skill level |
| 3 | `help me write a poem about love` | Creative → should detect "creative" tone, "beginner" skill |
| 4 | `i need a distributed system architecture for a payment processing platform that handles 10k tps with eventual consistency` | Very technical → should detect expert skill, "Technical Architecture" domain |
| 5 | `can you make a cool story for my kid about a brave little robot` | Casual → should detect "casual" tone, "creative" domain |

**In LangFuse:** Each trace should show `context` agent ran with `skill_level`, `tone`, `constraints`, `implicit_preferences` extracted.

---

## Test Category 2: Followup Modifications (Context Agent Skips on Followup)

**Goal:** Verify followup detection and refinement flow.

| # | Sequence | What to Verify |
|---|----------|---------------|
| 6 | First: `write a python function to parse JSON from a string`<br>Then: `make it handle nested objects` | FOLLOWUP branch — 1 LLM call, no full swarm |
| 7 | First: `write a react component for a login form`<br>Then: `add form validation` | FOLLOWUP — should refine, not start from scratch |
| 8 | First: `write a blog post about AI ethics`<br>Then: `make it more professional` | FOLLOWUP — tone adjustment |
| 9 | First: `create a sql query to find duplicate users`<br>Then: `add a count of how many duplicates` | FOLLOWUP — technical refinement |
| 10 | First: `write a story about a wizard`<br>Then: `make it shorter and funnier` | FOLLOWUP — creative adjustment |

**In LangFuse:** Should show only 1-2 LLM calls, not full swarm.

---

## Test Category 3: Domain Drift Detection (Domain Agent Catches Switches)

**Goal:** Verify domain agent detects when user switches topics.

| # | Sequence | Expected Domain |
|---|----------|----------------|
| 11 | `build a microservice for user authentication using FastAPI and JWT` | Technical Architecture |
| 12 | `now write a marketing email for this product` | Marketing & Communications |
| 13 | `create a data pipeline that ingests events from Kafka and writes to PostgreSQL` | Data Intelligence |
| 14 | `write a children's book about sharing` | Creative Writing |
| 15 | `design a system prompt for a code review assistant` | Meta-Prompting |

**In LangFuse:** Each trace should show different `primary_domain`. Domain confidence should decrease on drift.

---

## Test Category 4: Ambiguous Requests (Clarification Loop)

**Goal:** Verify orchestrator asks clarifying questions for vague prompts.

| # | Prompt | Expected Behavior |
|---|--------|------------------|
| 16 | `write something about AI` | CLARIFICATION — "What kind of AI content? Technical article, story, or business overview?" |
| 17 | `make it better` (without prior context) | CLARIFICATION — "Better how? More specific, more professional, or something else?" |
| 18 | `write a thing for my boss` | CLARIFICATION — "What kind of thing? Email, report, presentation?" |
| 19 | `help me with coding` | CLARIFICATION — "What language? What are you building?" |
| 20 | `do the thing we talked about` | CLARIFICATION — "Which thing? Can you remind me?" |

**In LangFuse:** Should show `clarification_needed: true`, `clarification_question` populated.

---

## Test Category 5: Long Conversation Sessions (Memory Accumulation)

**Goal:** Verify conversation history builds up and context agent uses it.

**Send these in sequence in the SAME session:**

| # | Prompt | What to Verify |
|---|--------|---------------|
| 21 | `i'm a junior python developer learning FastAPI. can you show me a basic CRUD endpoint?` | Context: beginner, technical tone, FastAPI domain |
| 22 | `make it use async database calls` | Context: should still know user is junior |
| 23 | `now add authentication with JWT` | Context: should build on previous |
| 24 | `can you explain what each part does?` | Context: should know user needs explanations |
| 25 | `write tests for this endpoint` | Context: should know it's the same FastAPI project |

**In LangFuse:** Traces 22-25 should show `context_agent` using conversation history (not empty).

---

## Test Category 6: Complex Multi-Domain Requests

**Goal:** Verify prompt engineer synthesizes multiple domains correctly.

| # | Prompt | Expected |
|---|--------|----------|
| 26 | `write a technical spec for a React dashboard that shows real-time analytics from a PostgreSQL database, with a Python backend that processes streaming data from IoT sensors` | Domain: Full-Stack + Data Intelligence. Context: technical, expert skill. |
| 27 | `create a business plan for an AI startup that uses machine learning to optimize supply chain logistics, including financial projections and market analysis` | Domain: Business Strategy + Data Intelligence. |
| 28 | `write a tutorial blog post explaining transformers to a non-technical audience, with code examples in Python` | Domain: Creative Writing + Technical Architecture. Context: needs simplification. |
| 29 | `design a prompt template for a customer support chatbot that handles complaints empathetically and escalates to humans when needed` | Domain: Meta-Prompting. Context: needs empathy. |
| 30 | `create a SQL query that finds the top 10 customers by revenue, then write a Python script that emails them a personalized thank-you note using the results` | Domain: Data Intelligence + Full-Stack. |

---

## Test Category 7: Edge Cases & Stress Tests

| # | Prompt | What to Test |
|---|--------|-------------|
| 31 | *(empty message)* | Should handle gracefully — no crash |
| 32 | `a` | CONVERSATION — very short message |
| 33 | `write a 10,000 word novel about the history of computing from Babbage to modern AI, with character development, plot twists, and accurate technical details` | Very long request — quality gate should evaluate |
| 34 | `write a story` | Minimal — should clarify or give generic output |
| 35 | `HELLO HELLO HELLO` | ALL CAPS — context should detect tone |
| 36 | `pls help me wit coding im not good at it` | Informal spelling — context: beginner, casual |
| 37 | `Create a distributed, fault-tolerant microservice architecture using event sourcing, CQRS, and saga patterns for a multi-tenant SaaS platform with 99.99% SLA.` | Highly technical — context: expert skill |
| 38 | `write code` | Extremely vague — should clarify |
| 39 | `i want to build something cool with AI` | Vague + enthusiastic — context: beginner, creative |
| 40 | `refactor this: def x(a,b): return a+b` | Code-only input — domain: coding |

---

## Test Category 8: Cache Behavior

| # | Sequence | What to Verify |
|---|----------|---------------|
| 41 | Send exact same prompt twice | Second should be instant (cache hit) |
| 42 | `write a python sort function` then `Write a Python sort function` | Case difference → should still cache hit? (Currently exact match only) |
| 43 | `write a story` → wait 1 hour → `write a story` | Cache TTL is 1 hour — should miss after expiry |

---

## What to Check After Each Request

### In LangFuse (http://localhost:3001 → Traces):
- [ ] Which agents ran? (intent, context, domain, prompt_engineer)
- [ ] What was the quality score?
- [ ] What was the per-agent latency?
- [ ] Was the original prompt and improved prompt captured?

### In the Chat UI:
- [ ] Did the "Thought Accordion" show agent analysis?
- [ ] Did the improved prompt appear with quality score?
- [ ] Did the diff view show changes?
- [ ] Did the conversation sidebar update?

### In LangFuse Dashboard:
- [ ] Go to http://localhost:3001/project/kira/traces
- [ ] Click on any trace → see full breakdown
- [ ] Check "Scores" tab → quality scores should be visible
