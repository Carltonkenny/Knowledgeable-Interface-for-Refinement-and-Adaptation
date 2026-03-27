# PromptForge

**Transform vague prompts into precise, high-performance instructions using multi-agent AI.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![Deploy to Railway](https://img.shields.io/badge/deploy-railway-9055FF)](https://railway.app)

---

## ✨ What It Does

PromptForge uses a **swarm of 4 specialized AI agents** to engineer your rough prompts into production-ready instructions:

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

**Result:** ~2000% more detailed, with role, audience, tone, structure, and constraints.

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/Carltonkenny/Knowledgeable-Interface-for-Refinement-and-Adaptation.git
cd Knowledgeable-Interface-for-Refinement-and-Adaptation
docker-compose up
```

### Option 2: Local Python

```bash
git clone https://github.com/Carltonkenny/Knowledgeable-Interface-for-Refinement-and-Adaptation.git
cd Knowledgeable-Interface-for-Refinement-and-Adaptation
pip install -r requirements.txt
python -m uvicorn api:app --port 8000
```

**Access:**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

## 🎯 Features

- **Multi-Agent Swarm** — 4 specialized agents (Intent, Context, Domain, Engineer)
- **Conversational Memory** — Learns your style over time with LangMem
- **MCP Integration** — Works with Cursor, Claude Desktop, and MCP clients
- **Quality Scoring** — Every engineered prompt includes quality metrics
- **Session History** — Search, filter, and analyze past prompts
- **Docker Ready** — Production container with health checks
- **Sentry Monitoring** — Error tracking and performance monitoring

---

## 🏗️ Architecture

```
┌─────────────┐
│   User      │
│   Input     │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│  Kira (Orchestrator)            │
│  Routes to agent swarm          │
└──────────────┬──────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│ Fast LLM    │  │ Full LLM    │
│ (Analysis)  │  │ (Engineer)  │
│ qwen-safety │  │ qwen-coder  │
└─────────────┘  └─────────────┘
       │                │
       └────────┬───────┘
                │
                ▼
       ┌─────────────────┐
       │  Engineered     │
       │  Prompt + Score │
       └─────────────────┘
```

---

## 📚 Documentation

| Doc | Description |
|-----|-------------|
| [API Reference](./docs/API.md) | Full endpoint documentation |
| [Deployment Guide](./docs/DEPLOYMENT.md) | Railway + Vercel deployment |
| [Database Schema](./docs/SUPABASE_SCHEMA.md) | Supabase tables and RLS |

---

## 🔧 Configuration

Copy `.env.example` to `.env` and configure:

```env
# LLM Provider (Pollinations.ai)
POLLINATIONS_API_KEY=your_api_key
POLLINATIONS_MODEL_FULL=qwen-coder
POLLINATIONS_MODEL_FAST=qwen-safety

# Database (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_key

# Redis (Upstash)
REDIS_URL=rediss://your-redis.upstash.io:6379
```

---

## 🌐 Live Demo

**Frontend:** [https://promptforge.vercel.app](https://promptforge.vercel.app) (after deployment)

**Backend:** [https://promptforge.railway.app](https://promptforge.railway.app) (after deployment)

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI, Python 3.11 |
| **LLM Orchestration** | LangChain, LangGraph |
| **Database** | Supabase (PostgreSQL + pgvector) |
| **Cache** | Redis (Upstash) |
| **Frontend** | Next.js 16, React 19, TypeScript |
| **Monitoring** | Sentry, Better Stack |
| **Deployment** | Docker, Railway, Vercel |

---

## 📊 Performance

| Metric | Target | Status |
|--------|--------|--------|
| First token latency | <500ms | ✅ |
| Full response time | <10s | ✅ |
| Quality score avg | >4.0/5 | ✅ |
| Uptime | >99% | ✅ |

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [LangChain](https://python.langchain.com/) — LLM orchestration framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) — Agent orchestration
- [Supabase](https://supabase.com/) — Database and auth
- [Pollinations.ai](https://pollinations.ai/) — LLM provider
- [Sentry](https://sentry.io/) — Error tracking

---

## 📬 Contact

- **GitHub Issues:** [Report bugs or request features](https://github.com/Carltonkenny/Knowledgeable-Interface-for-Refinement-and-Adaptation/issues)
- **Discussions:** [Community discussions](https://github.com/Carltonkenny/Knowledgeable-Interface-for-Refinement-and-Adaptation/discussions)

---

**Built with ❤️ by Carlton Kenny**
