# Implementation Report — Phase 2 Story 1: Learning Intelligence Backend

This report documents the completion of **Phase 2 Story 1** for the AI Career Coach platform: **Learning Intelligence Roadmap Generation**.

---

## 1. Summary of Changes

### New Files Created
- [`backend/app/schemas/learning.py`](file:///c:/projects/POC/AI-Career-Coach/backend/app/schemas/learning.py): Pydantic models for request/response serialization (`GenerateRoadmapRequest`, `GenerateRoadmapResponse`, `RoadmapItemResponse`, `RoadmapResponse`).
- [`backend/app/services/learning_service.py`](file:///c:/projects/POC/AI-Career-Coach/backend/app/services/learning_service.py): Business logic for generating roadmap items via LLM, archiving previous `active` roadmaps, and saving/retrieving `roadmaps` and `roadmap_items` records in Postgres.
- [`backend/app/workers/jobs/generate_roadmap.py`](file:///c:/projects/POC/AI-Career-Coach/backend/app/workers/jobs/generate_roadmap.py): Arq async worker job consuming roadmap generation requests.
- [`backend/app/api/v1/learning.py`](file:///c:/projects/POC/AI-Career-Coach/backend/app/api/v1/learning.py): REST API router for `/api/v1/learning/*` endpoints (`POST /roadmap`, `GET /roadmap/{id}`, `POST /roadmap/{id}/regenerate`, `PATCH /roadmap-item/{id}` stub).
- [`backend/tests/test_learning_roadmap.py`](file:///c:/projects/POC/AI-Career-Coach/backend/tests/test_learning_roadmap.py): Integration test suite covering LLM prompt generation, worker job execution, auto-archiving, API endpoints, rate limiting, and 501 stub behavior.

### Files Modified
- [`backend/app/services/llm_service.py`](file:///c:/projects/POC/AI-Career-Coach/backend/app/services/llm_service.py): Added `GENERATE_ROADMAP_SYSTEM_PROMPT`, `GENERATE_ROADMAP_USER_PROMPT_TEMPLATE`, and `generate_roadmap_llm` logging to `ai_generation_logs` (`module='learning'`).
- [`backend/app/workers/worker_settings.py`](file:///c:/projects/POC/AI-Career-Coach/backend/app/workers/worker_settings.py): Registered `generate_roadmap` in `WorkerSettings.functions`.
- [`backend/app/api/v1/__init__.py`](file:///c:/projects/POC/AI-Career-Coach/backend/app/api/v1/__init__.py): Registered `learning.router` in the v1 router aggregation.

---

## 2. API Routes Specification & Implementation

| Endpoint | Method | Rate Limit | Description / Status |
|---|---|---|---|
| `/api/v1/learning/roadmap` | `POST` | `5/hour` | Enqueues background Arq job `generate_roadmap`. Returns `202 Accepted` + `job_id`. |
| `/api/v1/learning/roadmap/{id}` | `GET` | — | Returns `RoadmapResponse` with `items` ordered by `sequence_order`. Returns `200 OK`. |
| `/api/v1/learning/roadmap/{id}/regenerate` | `POST` | `5/hour` | Re-enqueues `generate_roadmap` for existing roadmap's `skill_gap_report_id`. Returns `202 Accepted`. |
| `/api/v1/learning/roadmap-item/{id}` | `PATCH` | — | **Stub route**: Returns `501 Not Implemented` (`"Item completion tracking coming in the next release"`). |

---

## 3. Data Flow & End-to-End Verification

```
[POST /api/v1/learning/roadmap] (skill_gap_report_id)
        │
        ▼
[Arq Redis Queue] ──► [generate_roadmap Worker Job]
                             │
                             ▼
              [learning_service.create_roadmap]
                             │
                             ├──► [llm_service.generate_roadmap_llm] (Groq API)
                             │            │
                             │            └──► Logs to [ai_generation_logs] (module='learning')
                             │
                             ├──► Archives prior active roadmaps (status='archived')
                             │
                             └──► Saves new [roadmaps] & [roadmap_items] rows (status='active')
                                          │
                                          ▼
                         [GET /api/v1/learning/roadmap/{id}]
```

### Verified Features:
1. **Auditability**: Every LLM roadmap prompt and response is saved to `ai_generation_logs` with `module='learning'`.
2. **Single Active Roadmap Invariant**: `learning_service.create_roadmap` executes an `UPDATE roadmaps SET status='archived' WHERE user_id=:user_id AND status='active'` before inserting the new roadmap record.
3. **No Fake URLs Constraint**: Groq prompt instructs the LLM to leave `url` as `null` or use descriptive learning objective titles (e.g. *"Complete official React documentation advanced patterns section"*).
4. **501 Stub**: `PATCH /api/v1/learning/roadmap-item/{id}` returns `501 Not Implemented` cleanly without breaking existing routes.

---

## 4. Pytest Execution Results

The entire Phase 2 Story 1 test suite passed with 100% success rate:

```text
tests/test_learning_roadmap.py::test_generate_roadmap_llm_logging PASSED                   [ 12%]
tests/test_learning_roadmap.py::test_create_roadmap_archives_previous_active_roadmap PASSED [ 25%]
tests/test_learning_roadmap.py::test_generate_roadmap_job_fails_when_missing_skills_is_empty PASSED [ 37%]
tests/test_learning_roadmap.py::test_generate_roadmap_job_success PASSED                  [ 50%]
tests/test_learning_roadmap.py::test_post_roadmap_route PASSED                            [ 62%]
tests/test_learning_roadmap.py::test_get_roadmap_route PASSED                             [ 75%]
tests/test_learning_roadmap.py::test_post_roadmap_regenerate_route PASSED                 [ 87%]
tests/test_learning_roadmap.py::test_patch_roadmap_item_complete_stub_returns_501 PASSED  [100%]

================================= 8 passed in 1.89s =================================
```


---

## 5. Architectural & Schema Conformance

- **`database.md`**: Fully aligned with `roadmaps` (`id`, `user_id`, `skill_gap_report_id`, `status`, `created_at`, `updated_at`) and `roadmap_items` (`id`, `roadmap_id`, `skill_name`, `type`, `title`, `description`, `url`, `sequence_order`, `difficulty`, `status`, `completed_at`).
- **`spec.md`**: API signatures, rate-limit settings (`5/hour`), and Arq worker definitions strictly match the specification.
- **`backend_architecture.md`**: Service boundaries and layered responsibilities (`api` → `services` → `llm_service` / `db`) strictly maintained without Phase 1 code modification.

---

## 6. Recommended Next Story

**Phase 2 Story 2**: **Skill Recalculation Loop & Roadmap Item Completion**
- Implement `PATCH /api/v1/learning/roadmap-item/{id}` route to update item status (`in_progress`, `completed`) and `completed_at` timestamp.
- Implement the `recalculate_skill_vector` Arq worker job to update candidate `skill_vectors` and automatically re-run `compute_skill_gap` upon milestone completion, closing the learning loop.
