# GEMINI.md — Agent Configuration
## AI Career Coach Platform

This file is read by the agent at the start of every session. It defines the tech stack, conventions, and boundaries the agent must follow. Do not deviate from this stack without explicit user confirmation — this is a zero-cost, free-tier-only build.

---

## Project Summary

AI Career Coach is a web platform with four connected modules:
1. Resume Intelligence (ATS scoring, grammar audit, keyword gap analysis)
2. Skill Intelligence (skill-vector vs. market-demand gap report)
3. Learning Intelligence (dynamic learning roadmaps)
4. Career Intelligence (conversational chat advisor, mock interviews)

Full requirements live in `brd.md` (business) and `prd.md` (product). Technical breakdown lives in `spec.md`. Read all three before planning any feature.

---

## Tech Stack (fixed — do not substitute paid services)

| Layer | Technology |
|---|---|
| Frontend | Next.js (App Router) + React + TypeScript |
| Styling | Tailwind CSS |
| Data fetching | TanStack Query |
| Charts | Recharts |
| Frontend hosting | Vercel (free tier) |
| Backend | Python (FastAPI) |
| Backend hosting | Oracle Cloud Free Tier |
| Database | Neon (Postgres, free tier) |
| Vector search | pgvector (Postgres extension) |
| LLM provider | Groq API (free tier) |
| Resume parsing | pdf-parse / mammoth.js → structured via Groq LLM |
| Auth | NextAuth.js (Auth.js) |
| File storage | Cloudinary (free tier, 25GB) |
| Job queue | Arq (Python-native, async, Redis-backed) — **not BullMQ**, since BullMQ is Node-only and the backend is FastAPI |
| Cache / queue backend | Redis (self-hosted on Oracle VM, or Upstash free tier) |

---

## Folder Structure Convention

```
/frontend          → Next.js app (App Router)
  /app              → routes
  /components       → shared UI components
  /lib              → API clients, utils, TanStack Query hooks
  /types            → shared TypeScript types

/backend            → FastAPI app
  /app
    /api            → route handlers, grouped by module (resume, skill, learning, career)
    /core           → config, security, db session
    /models         → SQLAlchemy models
    /schemas        → Pydantic schemas
    /services       → business logic per module
    /workers        → Arq job definitions
  /alembic          → DB migrations

/docs                → brd.md, prd.md, spec.md
```

---

## Coding Rules

- No paid APIs, SDKs, or hosting tiers may be introduced without explicit user approval.
- All secrets (DB URL, Groq API key, Cloudinary keys, NextAuth secret) go in `.env` — never hardcoded, never committed.
- Every new backend endpoint needs a Pydantic request/response schema.
- Long-running work (resume scoring, roadmap regeneration) must go through an Arq job — never a blocking request, per the 10-second NFR.
- All AI-generated output (resume feedback, roadmap items, chat responses) must be logged to Postgres for auditability (per BRD FR/NFR on auditability).
- Career Intelligence chat must show a disclaimer for legal/visa/compensation topics — do not remove this.
- Follow WCAG 2.1 AA basics: semantic HTML, labeled form fields, sufficient color contrast (Tailwind defaults + shadcn/ui components help with this).

---

## Working Style

- Explore and plan before coding — read `spec.md` and produce an implementation plan artifact before writing code for a new feature.
- Build one module at a time, following the phased plan in `prd.md` (Phase 1: Resume + Skill Intelligence → Phase 2: Learning → Phase 3: Career chat → Phase 4: live market data).
- After implementing a feature, write or update a basic test and run it before marking the task done.
- Debug with logs before guessing — add temporary logging rather than making blind changes.
- Flag any point where a "free tier" limit (Groq rate limits, Neon storage cap, Cloudinary 25GB cap) could become a real constraint, rather than silently working around it.
