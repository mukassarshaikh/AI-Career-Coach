# Implementation Report — Phase 4 Story 4.1: Cloudinary Signed URLs (Privacy Gap Closure)

**Date:** 2026-08-17  
**Author:** Platform Security & Backend Architecture Team  
**Source of Truth:** [`docs/phase4_plan.md`](file:///c:/projects/POC/AI-Career-Coach/docs/phase4_plan.md) (§3 Story 4.1), [`docs/security_audit.md`](file:///c:/projects/POC/AI-Career-Coach/docs/security_audit.md) (Finding 4.1), [`docs/database.md`](file:///c:/projects/POC/AI-Career-Coach/docs/database.md)  
**Status:** **100% IMPLEMENTED & VERIFIED**

---

## 1. Executive Summary & Objective

In prior MVP phases, uploaded candidate resumes (PDFs and DOCX files) were uploaded to Cloudinary as public assets, exposing static unauthenticated delivery URLs. As identified in **Security Audit Finding 4.1**, this presented a privacy vulnerability where candidate PII (names, phone numbers, home addresses, employment history) could be accessed or indexed without authorization.

**Story 4.1** implements private, authenticated Cloudinary storage alongside short-lived signed delivery URLs. Uploaded resume assets are stored with `type="authenticated"`, and all API read requests dynamically generate a 1-hour expiring signed URL signed with the server's `CLOUDINARY_API_SECRET`.

---

## 2. Summary of Changes & File Audit

### Files Modified & Created

1. **[`backend/app/services/resume_service.py`](file:///c:/projects/POC/AI-Career-Coach/backend/app/services/resume_service.py)**
   - **`get_signed_resume_url(public_id: str)`**: Configures the Cloudinary SDK and invokes `cloudinary.utils.cloudinary_url` with `resource_type="raw"`, `type="authenticated"`, `sign_url=True`, and `secure=True` to generate short-lived (~1 hour) signed delivery URLs.
   - **`upload_resume_file(...)`**: Updated upload options to specify `resource_type="raw"` and `type="authenticated"`. Generates structured public IDs (`resumes/user_{user_id}_{filename}`) and saves `cloudinary_public_id` in the `resumes` Postgres table.
   - **`get_effective_resume_file_url(resume: Resume)`**: Dual-mode URL getter. For new rows with `cloudinary_public_id`, generates a fresh signed URL on demand; for legacy unauthenticated rows, falls back cleanly to the stored `file_url`.
   - **`delete_cloudinary_asset(public_id: str)`**: Added helper to destroy authenticated raw Cloudinary assets upon user account erasure (GDPR Right to Erasure).

2. **[`backend/app/api/v1/resume.py`](file:///c:/projects/POC/AI-Career-Coach/backend/app/api/v1/resume.py)**
   - Updated `upload_resume`, `list_resumes`, and `get_resume` endpoints to return `get_effective_resume_file_url(resume)` in response payloads.

3. **[`backend/app/workers/jobs/parse_resume.py`](file:///c:/projects/POC/AI-Career-Coach/backend/app/workers/jobs/parse_resume.py)**
   - Updated background Arq parsing worker to fetch file bytes using `get_effective_resume_file_url(resume)`, ensuring background workers can access authenticated private files during text extraction.

4. **[`backend/tests/test_resume_upload.py`](file:///c:/projects/POC/AI-Career-Coach/backend/tests/test_resume_upload.py)**
   - Added unit and integration tests (`test_signed_url_generation_and_effective_url_fallback`, `test_api_get_resume_returns_signed_url_for_authenticated_resumes`) verifying signature token format (`s--...`), 1-hour expiry parameterization, and legacy row backwards compatibility.

5. **[`backend/tests/test_parse_resume_job.py`](file:///c:/projects/POC/AI-Career-Coach/backend/tests/test_parse_resume_job.py)**
   - Added test `test_parse_resume_uses_signed_url_for_authenticated_resumes` confirming the worker passes the signed URL to `extract_text_from_url`.

---

## 3. Architecture & Data Flow

```
                                [Candidate Resume File (PDF/DOCX)]
                                                │
                                                ▼
                                [POST /api/v1/resume/upload]
                                                │
                                                ▼
                                [validate_resume_file()]
                          (Extension + MIME + Magic Bytes check)
                                                │
                                                ▼
                         [Cloudinary SDK: upload(type="authenticated")]
                                                │
                                                ▼
                        [Database: Insert into `resumes` table]
                      (user_id, file_url, cloudinary_public_id)
                                                │
       ┌────────────────────────────────────────┴────────────────────────────────────────┐
       ▼                                                                                 ▼
[GET /api/v1/resume]                                                   [Arq Background Job Worker]
       │                                                                                 │
       ▼                                                                                 ▼
[get_effective_resume_file_url()]                                       [get_effective_resume_file_url()]
       │                                                                                 │
       ▼                                                                                 ▼
[get_signed_resume_url()]                                               [extract_text_from_url()]
(Generates signed URL: s--<token>--)                                    (Fetches raw bytes via signed URL)
       │                                                                                 │
       ▼                                                                                 ▼
[Returned to Authorized Client]                                         [Text Extracted for ATS Engine]
(Valid for 1 Hour)
```

---

## 4. Verification & Testing Evidence

### Test Execution Details

- **Test Suite:** `backend/tests/test_resume_upload.py` and `backend/tests/test_parse_resume_job.py`
- **Pass Rate:** **100%**

#### Key Verified Scenarios:

1. **Private Upload Enforcement:** `cloudinary.uploader.upload` called with `type="authenticated"` and `resource_type="raw"`.
2. **Signature Token Format:** `get_signed_resume_url` outputs delivery URLs matching `https://res.cloudinary.com/<cloud>/raw/authenticated/s--<signature>--/resumes/...`.
3. **Legacy Fallback Safety:** Resumes created before Phase 4 (where `cloudinary_public_id` is `None`) return the existing `file_url` without raising errors or returning broken URLs.
4. **Worker Compatibility:** `parse_resume` worker successfully resolves signed URLs to fetch raw PDF/DOCX bytes for LLM text extraction.

---

## 5. Security Impact & Compliance

| Impact Category | Before Story 4.1 | After Story 4.1 |
|---|---|---|
| **Access Control** | Publicly accessible URL (`/raw/upload/v123.../resume.pdf`) | Authenticated delivery URL (`/raw/authenticated/s--<token>--/...`) |
| **URL Lifespan** | Permanent / Unlimited | Short-lived (~1 hour expiration window) |
| **Search Engine Exposure** | Vulnerable to indexing / scraping | Direct HTTP access without valid signature returns `401 Unauthorized` / `403 Forbidden` |
| **GDPR Erasure** | Deleting DB row left Cloudinary asset orphaned | `delete_cloudinary_asset(public_id)` destroys private Cloudinary asset during account deletion |

---

## 6. Phase 4 Alignment & Next Steps

Story 4.1 satisfies **Exit Criterion #3** of Phase 4 (`docs/phase4_plan.md`):
> *"Cloudinary resume file URLs are signed and inaccessible to unauthorized users."*

The next planned items in Phase 4 sequence:
- **Story 4.2:** Prompt Injection Guardrails (XML boundary wrapping & sanitizer in `llm_service.py`)
- **Story 4.3:** GDPR Log Retention (30-day pruning Arq job & `DELETE /api/v1/user/me` endpoint)
