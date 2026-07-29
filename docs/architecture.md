# System Architecture
## AI Career Coach Platform

This is the top-level architecture reference. Read this first, then drill into `frontend_architecture.md`, `backend_architecture.md`, or `database.md` for module-specific detail. All decisions here are final for the free-tier build — do not introduce new services without explicit user approval.

---

## 1. High-Level System Diagram (textual)

```
┌─────────────────────┐         ┌──────────────────────────┐
│   Next.js Frontend   │  HTTPS  │   FastAPI Backend         │
│   (Vercel, free)     │◄───────►│   (Oracle Cloud VM, free) │
│                      │         │                            │
│  - App Router pages  │         │  - REST API (/api/v1/*)   │
│  - NextAuth.js        │         │  - Arq worker (async jobs)│
│  - TanStack Query     │         │  - Groq LLM calls          │
│  - Recharts           │         └──────────┬────────────────┘
└──────────┬───────────┘                    │
           │                                 │
           │                        ┌────────┴────────┐
           │                        │                  │
   ┌───────▼────────┐      ┌────────▼──────┐   ┌───────▼───────┐
   │  Cloudinary     │      │  Neon Postgres │   │  Redis         │
   │  (resume files) │      │  + pgvector    │   │  (Upstash/self)│
   └─────────────────┘      └────────────────┘   └────────────────┘
                                      ▲
                                      │
                             ┌────────┴─────────┐
                             │  Groq API          │
                             │  (LLM inference)   │
                             └─────────────────────┘
```

---

## 2. Component Responsibilities

| Component | Responsibility |
|---|---|
| Next.js Frontend | UI rendering, auth session handling, calling backend REST API, polling async job status, streaming chat responses to the user |
| FastAPI Backend | Business logic, REST API, orchestrating LLM calls, enqueuing/handling async jobs, DB access |
| Arq Worker | Runs inside the same backend codebase but as a separate process — consumes queued jobs (resume parsing, scoring, roadmap generation) from Redis |
| Neon Postgres | System of record for all structured data — users, resumes, skill vectors, roadmaps, chat history, logs |
| pgvector | Stores embeddings for skill vectors and market-skill reference data; powers similarity search for skill-gap matching |
| Redis | Job queue backing store (Arq) and light caching (e.g. Groq rate-limit counters) |
| Cloudinary | Stores uploaded resume PDF/DOCX files; backend stores only the URL/reference in Postgres |
| Groq API | All LLM inference: resume structuring, grammar audit, keyword analysis, roadmap generation, chat |

---

## 3. Request Flow Examples

### Resume Upload → Score (async)
1. Frontend uploads file to `/resume/upload` → backend pushes file to Cloudinary, saves `resumes` row, enqueues `parse_resume` job, returns `job_id`.
2. Frontend polls `/resume/jobs/{job_id}` via TanStack Query until complete.
3. Arq worker picks up `parse_resume` → extracts text → calls Groq to structure into JSON → saves `parsed_json` → enqueues `score_resume`.
4. `score_resume` job calls Groq for ATS scoring + grammar audit → saves `resume_reports` row.
5. Frontend fetches `/resume/{id}/report` once job status = complete.

### Career Chat (streaming, synchronous)
1. Frontend calls `/career/chat/{session_id}/message` with the user's message.
2. Backend forwards conversation context + user's resume/skill/roadmap summary (if relevant) to Groq with streaming enabled.
3. Backend proxies the stream back to the frontend as Server-Sent Events (SSE) or chunked response.
4. Full message is saved to `chat_messages` once streaming completes.

---

## 4. Environments

| Environment | Frontend | Backend | DB |
|---|---|---|---|
| Local dev | `next dev` on localhost:3000 | `uvicorn --reload` on localhost:8000 | Neon dev branch (or local Postgres + pgvector via Docker) |
| Production | Vercel | Oracle Cloud VM (systemd service or Docker) | Neon main branch |

Neon supports branch-based dev databases on the free tier — use a dev branch locally so you don't touch production data during development.

---

## 5. Deployment Notes (Oracle Cloud Free Tier backend)

- Run FastAPI via `uvicorn` behind `nginx` (reverse proxy + free TLS via Let's Encrypt/Certbot).
- Run the Arq worker as a separate systemd service (or a second Docker container) alongside the API — they share the same codebase but are different processes.
- Redis runs as a systemd service or Docker container on the same VM (or point to Upstash free tier instead to avoid self-managing it).

---

## 6. Security Baseline

- All secrets via environment variables (see `.env.example`), never committed.
- HTTPS enforced everywhere (Vercel automatic; Oracle VM via Certbot).
- Backend validates NextAuth session/JWT on every protected route.
- CORS restricted to the deployed frontend origin only.
- All LLM prompts/responses logged to `ai_generation_logs` for auditability (per BRD requirement) — no raw resume PII sent to third parties beyond Groq (the LLM provider itself).

---

## 7. Reference Docs

- `frontend_architecture.md` — Next.js structure, routing, state, component conventions
- `backend_architecture.md` — FastAPI module structure, service layer, worker setup
- `database.md` — full schema, indexes, migration strategy
- `Implementation_plan.md` — phase-by-phase task breakdown for the agent to execute against
