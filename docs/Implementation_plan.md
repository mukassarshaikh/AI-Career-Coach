# Implementation Plan
## AI Career Coach Platform

This is the execution checklist. Reference `architecture.md`, `frontend_architecture.md`, `backend_architecture.md`, and `database.md` for detail on each item — this file just sequences the work. Work top to bottom; do not start a later phase's items before the earlier phase is functionally complete and tested.

Short prompt pattern to use with Antigravity: *"Implement [task name] from Implementation_plan.md, following backend_architecture.md and database.md conventions."*

---

## Phase 0 — Project Scaffolding

- [ ] Initialize `/frontend` with Next.js (App Router, TypeScript, Tailwind) per `frontend_architecture.md` folder structure
- [ ] Initialize `/backend` with FastAPI project structure per `backend_architecture.md`
- [ ] Set up Alembic in `/backend/alembic`
- [ ] Create Neon Postgres project + dev branch; enable `vector` and `pgcrypto` extensions
- [ ] Set up Redis (Upstash free tier or self-hosted) for local dev
- [ ] Wire `.env` files (frontend and backend) from `.env.example`
- [ ] Set up NextAuth.js with credentials provider
- [ ] Create initial Alembic migration for all tables in `database.md`
- [ ] Verify: frontend and backend run locally, backend connects to Neon, frontend can hit a health-check route through auth

---

## Phase 1 — Resume + Skill Intelligence (MVP core)

### Backend
- [ ] `resume_service.py`: file upload handling → Cloudinary, save `resumes` row
- [ ] `parse_resume` Arq job: extract text (pdf-parse/mammoth equivalent) → structure via Groq (`llm_service.py`) → save `parsed_json`
- [ ] `score_resume` Arq job: ATS scoring + grammar audit via Groq → save `resume_reports`
- [ ] `analyze_keywords` Arq job: JD vs. resume comparison → save `keyword_gaps`/`action_items`
- [ ] Routes: `POST /resume/upload`, `GET /resume/{id}`, `POST /resume/{id}/score`, `GET /resume/jobs/{job_id}`, `POST /resume/{id}/job-description`, `GET /resume/{id}/report`
- [ ] `embedding_service.py`: wrapper for generating embeddings (skill text → vector)
- [ ] `generate_skill_vector` Arq job: extract skills from `parsed_json` → embed → save `skill_vectors`
- [ ] Seed `market_skill_reference` table (see Seed Data task below) before building gap comparison
- [ ] `compute_skill_gap` Arq job: compare `skill_vectors` vs. `market_skill_reference` via pgvector similarity → save `skill_gap_reports`
- [ ] Routes: `POST /skill/vector`, `GET /skill/gap-report`, `POST /skill/gap-report/refresh`
- [ ] `ai_generation_logs` writes wired into every Groq call

### Frontend
- [ ] Auth pages: login/register
- [ ] Resume upload page + `ResumeUploadCard` component
- [ ] Job polling hook (`useJobStatus`) + loading states while async scoring runs
- [ ] Resume detail page: ATS score gauge, grammar suggestions, keyword gap list, action items
- [ ] JD paste/submit flow on resume detail page
- [ ] Skill page: `SkillGapRadarChart`, `MissingSkillsTable`

### Seed Data
- [ ] Curate `market_skill_reference` dataset: 20–50 common roles × top skills × demand weights, sourced from public data (BLS, public job-postings). Load via a one-off seed script (`/backend/scripts/seed_market_reference.py`), not through the API.

### Phase 1 Exit Criteria
- [ ] User can register/login, upload a resume, see ATS score + grammar feedback within ~10s (perceived, via async polling), submit a target JD and see keyword gaps, and view a skill-gap report against a target role.

---

## Phase 2 — Learning Intelligence

### Backend
- [ ] `learning_service.py`: roadmap generation logic (LLM prompt: skill gaps → sequenced items)
- [ ] `generate_roadmap` Arq job: create `roadmaps` + `roadmap_items` rows, sequenced by dependency/difficulty
- [ ] `recalculate_skill_vector` Arq job: triggered on roadmap item completion → re-embed skill vector → re-run `compute_skill_gap`
- [ ] Routes: `POST /learning/roadmap`, `GET /learning/roadmap/{id}`, `PATCH /learning/roadmap-item/{id}`, `POST /learning/roadmap/{id}/regenerate`

### Frontend
- [ ] Learning page: roadmap list, status per roadmap
- [ ] Roadmap detail page: `RoadmapTimeline`, `RoadmapItemCard` with mark-complete action
- [ ] Progress bar reflecting completed vs. total items
- [ ] Wire mark-complete → trigger recalculation → refresh skill-gap view

### Phase 2 Exit Criteria
- [ ] User can generate a roadmap from their skill-gap report, see sequenced items, mark items complete, and see their skill-gap report update afterward.

---

## Phase 3 — Career Intelligence

### Backend
- [ ] `career_service.py`: chat orchestration, context assembly (pull relevant resume/skill/roadmap summary into system context when relevant)
- [ ] Streaming Groq integration in `llm_service.py` (SSE or chunked response passthrough)
- [ ] Routes: `POST /career/chat/session`, `POST /career/chat/{session_id}/message` (streaming), `GET /career/chat/{session_id}/history`
- [ ] Disclaimer logic: detect legal/visa/compensation-adjacent topics, prepend disclaimer text to response
- [ ] Mock interview mode: role-specific question generation, text-based answer feedback

### Frontend
- [ ] Career page: `ChatWindow`, `ChatMessageBubble`, streaming token rendering
- [ ] Session start flow (choose general / mock interview / career strategy)
- [ ] `MockInterviewPanel` for structured Q&A flow

### Phase 3 Exit Criteria
- [ ] User can start a chat session, get streamed responses referencing their own resume/skill/roadmap data, run a mock interview flow, and see disclaimers on sensitive topics.

---

## Phase 4 — Live Market Data + Scale Readiness

- [ ] Design and build a market-data ingestion pipeline to replace the static `market_skill_reference` seed (source TBD — public job-posting datasets or a licensed feed if budget changes)
- [ ] Scheduled refresh job (weekly, per BRD NFR) for market data
- [ ] Dashboard notifications: roadmap milestones due, significant market/skill trend changes
- [ ] Groq rate-limit handling: request queuing/backoff, user-facing messaging if throttled
- [ ] Basic caching layer (Redis) for frequently-read, slow-changing data (e.g. market reference lookups)
- [ ] Review Neon/Cloudinary free-tier usage against actual load; flag if approaching limits

### Phase 4 Exit Criteria
- [ ] Market data refreshes on a schedule without manual intervention; system degrades gracefully (not with hard failures) when free-tier rate/storage limits are approached.

---

## Cross-Phase (ongoing, not a separate phase)

- [ ] Unit tests per service function (mock DB/LLM)
- [ ] Integration tests per API route (happy path minimum)
- [ ] Consolidated dashboard (`/dashboard/summary`) updated incrementally as each module ships — don't leave it for last, wire each module's summary card in as it's built
- [ ] Accessibility pass (WCAG 2.1 AA) on each new page as it's built, not retrofitted at the end
