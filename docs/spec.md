# Technical Specification
## AI Career Coach Platform

This spec translates `prd.md` into implementation-ready detail: data models, API routes, and module-by-module build order. Read `GEMINI.md` for stack/conventions first.

---

## 1. Data Models (Postgres via Neon)

### `users`
- id (uuid, pk)
- email (unique)
- password_hash (nullable if OAuth-only)
- name
- target_role (text, nullable)
- created_at, updated_at

### `resumes`
- id (uuid, pk)
- user_id (fk → users)
- file_url (Cloudinary URL)
- raw_text (extracted text)
- parsed_json (structured: experience, education, skills, achievements)
- ats_score (int)
- created_at, updated_at

### `job_descriptions`
- id (uuid, pk)
- user_id (fk → users)
- resume_id (fk → resumes, nullable)
- raw_text
- parsed_keywords (jsonb)
- created_at

### `resume_reports`
- id (uuid, pk)
- resume_id (fk → resumes)
- job_description_id (fk → job_descriptions, nullable)
- ats_breakdown (jsonb: formatting, structure, parseability sub-scores)
- grammar_suggestions (jsonb)
- keyword_gaps (jsonb)
- action_items (jsonb, prioritized list)
- created_at

### `skill_vectors`
- id (uuid, pk)
- user_id (fk → users)
- resume_id (fk → resumes, nullable)
- vector (pgvector embedding)
- raw_skills (jsonb: extracted skill list)
- created_at, updated_at

### `market_skill_reference` (static/curated for Phase 1)
- id (uuid, pk)
- role_title (text)
- skill_name (text)
- demand_weight (float)
- vector (pgvector embedding)
- source (text, e.g. "BLS 2026", "manual curation")
- updated_at

### `skill_gap_reports`
- id (uuid, pk)
- user_id (fk → users)
- skill_vector_id (fk → skill_vectors)
- target_role (text)
- missing_skills (jsonb, ranked by demand_weight)
- created_at

### `roadmaps`
- id (uuid, pk)
- user_id (fk → users)
- skill_gap_report_id (fk → skill_gap_reports)
- status (enum: active, completed, archived)
- created_at, updated_at

### `roadmap_items`
- id (uuid, pk)
- roadmap_id (fk → roadmaps)
- skill_name (text)
- type (enum: course, article, project, milestone)
- title, description, url
- sequence_order (int)
- difficulty (enum: beginner, intermediate, advanced)
- status (enum: not_started, in_progress, completed)
- completed_at (nullable)

### `chat_sessions`
- id (uuid, pk)
- user_id (fk → users)
- context_type (enum: general, mock_interview, career_strategy)
- created_at

### `chat_messages`
- id (uuid, pk)
- session_id (fk → chat_sessions)
- role (enum: user, assistant)
- content (text)
- created_at

### `ai_generation_logs` (auditability — BRD requirement)
- id (uuid, pk)
- user_id (fk → users)
- module (enum: resume, skill, learning, career)
- prompt (text)
- response (text)
- model_used (text)
- created_at

---

## 2. API Routes (FastAPI, prefix `/api/v1`)

### Auth (via NextAuth.js on frontend, verified by backend middleware)
- Backend validates NextAuth session/JWT on protected routes.

### Resume Intelligence — `/resume`
- `POST /resume/upload` — upload PDF/DOCX to Cloudinary, extract text, queue parsing job
- `GET /resume/{id}` — get parsed resume + latest ATS score
- `POST /resume/{id}/score` — queue re-scoring job (async, returns job_id)
- `GET /resume/jobs/{job_id}` — poll job status (for TanStack Query polling)
- `POST /resume/{id}/job-description` — submit target JD, queue keyword gap analysis
- `GET /resume/{id}/report` — get latest resume_report (ATS breakdown, grammar, gaps, action items)

### Skill Intelligence — `/skill`
- `POST /skill/vector` — generate/update skill vector from resume
- `GET /skill/gap-report` — get current skill-gap report vs. target role
- `POST /skill/gap-report/refresh` — queue refresh job

### Learning Intelligence — `/learning`
- `POST /learning/roadmap` — generate roadmap from a skill_gap_report (async job)
- `GET /learning/roadmap/{id}` — get roadmap + items
- `PATCH /learning/roadmap-item/{id}` — mark item complete → triggers skill vector recalculation
- `POST /learning/roadmap/{id}/regenerate` — queue roadmap adjustment job

### Career Intelligence — `/career`
- `POST /career/chat/session` — start a chat session (general / mock_interview / career_strategy)
- `POST /career/chat/{session_id}/message` — send message, stream response (Groq streaming)
- `GET /career/chat/{session_id}/history` — get message history

### Platform — `/dashboard`
- `GET /dashboard/summary` — consolidated view: resume score, skill gaps, roadmap progress, next actions
- `GET /notifications` — pending notifications (milestones due, market updates)

---

## 3. Async Job Definitions (Arq workers)

| Job | Trigger | Action |
|---|---|---|
| `parse_resume` | On upload | Extract text (pdf-parse/mammoth) → structure via Groq → save parsed_json |
| `score_resume` | On upload / re-score request | Compute ATS score + grammar audit via Groq → save resume_report |
| `analyze_keywords` | On JD submission | Compare resume vs. JD → save keyword_gaps + action_items |
| `generate_skill_vector` | After resume parsed | Embed extracted skills → save to skill_vectors (pgvector) |
| `compute_skill_gap` | After skill vector updated | Compare vs. market_skill_reference → save skill_gap_report |
| `generate_roadmap` | On roadmap request | LLM-generate roadmap items, sequence by dependency/difficulty |
| `recalculate_skill_vector` | On roadmap item completion | Update skill_vectors, re-run compute_skill_gap |

---

## 4. Build Order (maps to prd.md Section 7)

**Phase 1** — Auth, resume upload/parse/score, JD keyword gap, static market reference seed, skill-gap report (read-only, no roadmap yet)
**Phase 2** — Roadmap generation, roadmap item tracking, skill-vector recalculation loop
**Phase 3** — Career chat (streaming), mock interview flow, session persistence
**Phase 4** — Replace static market reference with live ingestion pipeline, notifications, rate-limit handling for Groq

---

## 5. Seed Data Needed Before Phase 1 Works End-to-End

- `market_skill_reference` table needs an initial curated dataset (target: 20-50 common roles × their top skills + demand weights) sourced from public data (BLS, public job-posting datasets). This is a manual/semi-manual task, not something the agent can invent — flag to the user if this seed data doesn't exist yet.
