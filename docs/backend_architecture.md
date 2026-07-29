# Backend Architecture
## AI Career Coach Platform — FastAPI Backend

Read `architecture.md` first for system context. This file defines the backend folder structure, service-layer conventions, and worker setup in enough detail that the agent shouldn't need re-explaining each time.

---

## 1. Folder Structure

```
/backend
  /app
    main.py                      → FastAPI app instance, router registration, CORS, startup/shutdown events

    /api
      /v1
        resume.py                → /resume/* routes
        skill.py                 → /skill/* routes
        learning.py              → /learning/* routes
        career.py                 → /career/* routes
        dashboard.py              → /dashboard/*, /notifications routes
        deps.py                   → shared dependencies (get_db, get_current_user)

    /core
      config.py                  → Settings (pydantic-settings), reads .env
      security.py                 → JWT validation against NextAuth session
      db.py                       → SQLAlchemy engine/session setup

    /models                       → SQLAlchemy ORM models (one file per table group)
      user.py, resume.py, skill.py, learning.py, career.py, logs.py

    /schemas                      → Pydantic request/response schemas, mirrors /models
      resume.py, skill.py, learning.py, career.py, dashboard.py

    /services                     → business logic, called by API routes — routes stay thin
      resume_service.py           → parsing orchestration, ATS scoring logic, keyword gap logic
      skill_service.py            → skill vector generation, gap computation
      learning_service.py         → roadmap generation, sequencing, recalculation
      career_service.py           → chat orchestration, mock interview logic
      llm_service.py              → shared Groq client wrapper (single place all LLM calls go through)
      embedding_service.py        → shared embedding generation wrapper (for pgvector)

    /workers
      worker_settings.py          → Arq WorkerSettings (job list, redis settings)
      jobs
        parse_resume.py
        score_resume.py
        analyze_keywords.py
        generate_skill_vector.py
        compute_skill_gap.py
        generate_roadmap.py
        recalculate_skill_vector.py

  /alembic
    versions/                     → migration files
    env.py

  requirements.txt
  alembic.ini
```

---

## 2. Layering Rules

- **Routes (`/api/v1/*`)**: parse/validate request via Pydantic schema, call the relevant service function, return the response schema. No business logic, no direct DB queries, no direct LLM calls in route files.
- **Services (`/services`)**: contain all business logic. Services call models/DB directly and call `llm_service`/`embedding_service` for any AI work. Services are what both API routes and Arq jobs call into — this keeps logic in one place regardless of sync vs. async entry point.
- **Workers (`/workers/jobs`)**: thin wrappers that call the same service functions as the API routes, just triggered by the queue instead of an HTTP request. A job file should mostly just fetch its inputs, call the service, and save/update status.
- **`llm_service.py`**: the *only* place Groq API calls are made. All prompt templates live here (or in a `/prompts` subfolder referenced by this service). This makes it trivial to swap providers later or add rate-limit handling/retries in one place.

---

## 3. Async Job Pattern (Arq)

Every long-running operation follows this shape:

1. Route handler creates a DB row representing the pending work (or updates status on an existing row) and enqueues a job via Arq's `redis.enqueue_job(...)`.
2. Route returns immediately with a `job_id` (Arq's built-in job id, or a custom `jobs` tracking table if more detail is needed than Arq exposes).
3. Frontend polls `GET /resume/jobs/{job_id}` (or module-equivalent) which checks Arq's job result store in Redis.
4. Worker function updates the relevant DB row(s) on completion; result data is read from Postgres, not from the job result itself, once complete.

Example job function shape:

```python
# workers/jobs/parse_resume.py
async def parse_resume(ctx, resume_id: str):
    resume = await resume_service.get_resume(ctx["db"], resume_id)
    text = await resume_service.extract_text(resume.file_url)
    structured = await llm_service.structure_resume(text)
    await resume_service.save_parsed_data(ctx["db"], resume_id, structured)
    await ctx["redis"].enqueue_job("score_resume", resume_id)
```

---

## 4. Auth Validation

- Frontend sends the NextAuth session token (JWT) as a Bearer token on every request.
- `api/v1/deps.py` exposes `get_current_user`, a FastAPI dependency that decodes/validates the JWT (shared secret with NextAuth, set via `NEXTAUTH_SECRET` in `.env`) and loads the corresponding `users` row.
- Every protected route declares `current_user: User = Depends(get_current_user)`.

---

## 5. Database Access

- SQLAlchemy (async engine) for ORM access; see `database.md` for full schema.
- One `AsyncSession` per request via a `get_db` dependency; Arq jobs create their own session per job run (not shared with request-scoped sessions).
- Alembic for all migrations — never hand-edit the DB schema directly, even in dev.

---

## 6. LLM Call Conventions (`llm_service.py`)

- All prompts are versioned/templated in this service, not inlined in random services — makes prompt tuning and auditing (BRD requirement) straightforward.
- Every call logs its prompt + response + model name into `ai_generation_logs` before returning to the caller.
- Wrap Groq calls with basic retry/backoff for rate-limit (429) responses — free tier will hit these; fail gracefully (queue retry) rather than erroring the whole job.

---

## 7. Error Handling

- Use FastAPI's `HTTPException` for client-facing errors (400/401/403/404).
- Wrap service-layer exceptions with clear messages; avoid leaking raw stack traces or LLM provider error internals to the frontend.
- Failed Arq jobs should update the relevant DB row's status to `failed` with an error message field, so the frontend can show a meaningful retry prompt instead of polling forever.

---

## 8. Testing Expectations

- Each service function gets at least one unit test (mock the DB/LLM calls).
- Each API route gets at least one integration test (FastAPI `TestClient`) covering the happy path.
- Worker job functions get a test that mocks the service call and asserts the job updates status correctly.
