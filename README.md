# AI Career Coach

A free-tier, self-bootstrapped platform unifying four intelligence engines — Resume, Skill, Learning, and Career Intelligence — to help job seekers optimize resumes, close skill gaps, follow personalized learning roadmaps, and get conversational career guidance.

## Docs

- [`brd.md`](./docs/brd.md) — Business Requirements Document
- [`prd.md`](./docs/prd.md) — Product Requirements Document
- [`spec.md`](./docs/spec.md) — Technical specification (data models, API routes, build order)
- [`GEMINI.md`](./GEMINI.md) — Agent configuration for Antigravity (tech stack, conventions, rules)

## Tech Stack

Frontend: Next.js + React + TypeScript + Tailwind + TanStack Query + Recharts, hosted on Vercel.  
Backend: Python (FastAPI) + Arq (job queue), hosted on Oracle Cloud Free Tier.  
Database: Neon (Postgres) + pgvector for embeddings.  
LLM: Groq API (free tier).  
Auth: NextAuth.js. Storage: Cloudinary (free tier).  

Everything in this stack is free-tier / open-source — no paid services required to run the MVP.

## Local Setup

1. Clone the repo and copy the env template:
   ```bash
   cp .env.example .env
   ```
2. Fill in `.env` with your own free-tier credentials (Neon DB URL, Groq API key, Cloudinary keys, NextAuth secret).
3. Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
4. Backend:
   ```bash
   cd backend
   python -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
5. Run DB migrations:
   ```bash
   cd backend
   python -m alembic upgrade head
   ```
6. Seed Market Skill Reference Data:
   ```bash
   cd backend
   python -m app.db.seeds.market_skill_reference_seed
   ```
   > **Note on Model Download**: Running the seed script or generating skill vectors for the first time will cause `sentence-transformers` to download the `all-MiniLM-L6-v2` embedding model (~80MB) from Hugging Face. This requires outbound internet access on first run and may take a moment; it is a one-time download and is cached locally afterward.

7. **Start Redis & Arq Worker (Required for Async Background Jobs)**:
   > **IMPORTANT**: Redis must be running locally on `localhost:6379` before testing any async job flows (`parse_resume`, `score_resume`, `analyze_keywords`, `generate_skill_vector`, `compute_skill_gap`).

   Start Redis:
   ```bash
   redis-server
   # OR using Docker:
   docker run -d -p 6379:6379 redis:7-alpine
   ```

   Start the Arq worker process in a separate backend terminal window:
   ```bash
   cd backend
   python -m app.workers.worker_settings
   # OR using arq CLI:
   python -m arq app.workers.worker_settings.WorkerSettings
   ```

## Build Phases

| Phase | Scope |
|---|---|
| 1 | Auth, resume upload/parsing, ATS scoring, keyword gap analysis, skill-gap report |
| 2 | Learning roadmap generation, progress tracking |
| 3 | Career Intelligence chat advisor, mock interviews |
| 4 | Live market data ingestion, notifications, scale-readiness |

## Status

🚧 Early build — see `spec.md` for current build order.
