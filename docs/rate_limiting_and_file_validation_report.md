# Implementation Report: Rate Limiting & File Upload Magic-Byte Remediation

**Date:** August 3, 2026  
**Status:** Completed & Verified  
**Scope:** `backend/app/main.py`, `backend/app/core/limiter.py`, `backend/app/api/v1/auth.py`, `backend/app/api/v1/resume.py`, `backend/app/api/v1/skill.py`, `backend/app/services/resume_service.py`, `backend/requirements.txt`.

---

## Executive Summary

This story remediates two high-severity security findings identified in `docs/security_audit.md`:
1. **Finding 5.2 — Unrestricted Rate Limits on LLM-Calling & Auth Endpoints:** Implemented user-based and IP-based rate limiting via `slowapi` returning HTTP 429 with `Retry-After` headers.
2. **Finding 3.1 — Extension-Only File Upload Validation:** Implemented binary magic-byte inspection using `filetype` and signature header validation in `validate_resume_file()` prior to Cloudinary upload or document text extraction.

---

## 1. Summary of Code & Dependency Changes

### Dependencies Added (`backend/requirements.txt`)
- **`slowapi==0.1.9`**: Rate limiting wrapper for FastAPI apps.
- **`filetype==1.2.0`**: Pure Python file type inference engine (chosen over `python-magic` to eliminate native Windows C-DLL dependency issues).

### Backend Implementation Details

1. **Rate Limiter Configuration ([backend/app/core/limiter.py](file:///C:/projects/POC/AI-Career-Coach/backend/app/core/limiter.py))**
   - Configured `limiter` with custom `get_user_or_ip_key` function:
     - Checks `Authorization: Bearer <token>` header, decodes user identity via `security.decode_nextauth_token(token)`, and returns `"user:<user_id>"`.
     - For unauthenticated endpoints (login/register), falls back to client IP `"ip:<remote_address>"`.

2. **FastAPI Middleware Integration ([backend/app/main.py](file:///C:/projects/POC/AI-Career-Coach/backend/app/main.py#L44-L55))**
   - Added `app.state.limiter = limiter`.
   - Registered `RateLimitExceeded` exception handler returning `HTTP 429 Too Many Requests` along with standard `Retry-After` headers.

3. **Route Rate Limits Applied:**
   - **`POST /api/v1/auth/login`**: `10/15minute` per IP (Brute-force protection, Audit Finding 1.5).
   - **`POST /api/v1/auth/register`**: `5/hour` per IP (Registration spam protection).
   - **`POST /api/v1/resume/upload`**: `10/hour` per authenticated user.
   - **`POST /api/v1/resume/{id}/score`**: `20/hour` per authenticated user.
   - **`POST /api/v1/resume/{id}/job-description`**: `20/hour` per authenticated user.
   - **`POST /api/v1/skill/vector`**: `20/hour` per authenticated user.
   - **`POST /api/v1/skill/gap-report`**: `20/hour` per authenticated user.
   - **`POST /api/v1/skill/gap-report/refresh`**: `20/hour` per authenticated user.
   - **GET Routes (`/resume`, `/health`, etc.):** **Not rate limited** (0 impact on read operations).

4. **Magic-Byte Binary Validation ([backend/app/services/resume_service.py](file:///C:/projects/POC/AI-Career-Coach/backend/app/services/resume_service.py#L49-L105))**
   - Updated `validate_resume_file(file: UploadFile)`:
     - Maintains fast first-pass check against `ALLOWED_EXTENSIONS` (`.pdf`, `.docx`, `.doc`) and `ALLOWED_CONTENT_TYPES`.
     - Reads the first 2048 bytes of the uploaded file stream and verifies:
       - **PDF (`.pdf`)**: Header must contain binary signature `b"%PDF-"`.
       - **Word (`.docx`, `.doc`)**: Binary header must match Zip structure (`PK\x03\x04` / `PK\x05\x06`), OLE CFB compound header (`\xd0\xcf\x11...`), or `filetype.guess()` signature.
     - Rejects non-matching files with `HTTP 400 Bad Request` and detail `"This file doesn't appear to be a valid PDF or Word document."`.
     - Resets stream offset `await file.seek(0)` so Cloudinary upload and text parsing read from offset 0.

---

## 2. Empirical Verification Evidence (HTTP Results)

Direct API calls were executed against the running FastAPI instance on `http://127.0.0.1:8000`:

### A. Rate Limiting Verification (`POST /api/v1/resume/upload`)
- **User Key:** `user:ea41eb8b-63ed-4453-9760-04b6aff9eac0`
- **Initial Upload Requests (1-10):** `HTTP 201 Created`
- **11th Upload Request (Threshold Exceeded):**
  - **Status Code:** `429 Too Many Requests`
  - **Header:** `retry-after: 3600`
  - **Response Payload:**
    ```json
    {
      "error": "Rate limit exceeded: 10 per 1 hour"
    }
    ```

### B. Magic-Byte Spoofed File Rejection (`POST /api/v1/resume/upload`)
- **Test File:** `spoofed_resume.pdf` (plain text string `"This is plain text, not a real PDF document!"` renamed with `.pdf` extension).
- **Result:**
  - **Status Code:** `400 Bad Request`
  - **Response Payload:**
    ```json
    {
      "detail": "This file doesn't appear to be a valid PDF or Word document."
    }
    ```

### C. Legitimate PDF Upload Success (`POST /api/v1/resume/upload`)
- **Test File:** `valid_resume.pdf` (binary signature `%PDF-1.4...`).
- **Result:**
  - **Status Code:** `201 Created`
  - **Response Payload:**
    ```json
    {
      "resume_id": "765dedeb-1b84-4728-a56f-7896500a8546",
      "file_url": "https://res.cloudinary.com/.../user_ea41eb8b_valid_resume.pdf",
      "created_at": "2026-08-03T06:58:33.786716Z",
      "job_id": "1c3bc219f1db44918a8695ca358fe749",
      "message": "Resume uploaded successfully; background parsing enqueued."
    }
    ```

### D. Unaffected Read Operations (`GET /api/v1/resume`)
- **5 Sequential GET Requests:** `[200, 200, 200, 200, 200]` (Read operations remain unthrottled).

---

## 3. Rate Limit Threshold Rationale

| Endpoint | Threshold | Key Type | Rationale |
| :--- | :--- | :--- | :--- |
| `POST /auth/login` | `10 / 15min` | Client IP | Prevents automated credential stuffing while allowing legitimate users to re-try forgotten passwords. |
| `POST /auth/register` | `5 / hour` | Client IP | Prevents automated account creation spam. |
| `POST /resume/upload` | `10 / hour` | User ID | Uploading 10 resumes per hour exceeds normal candidate user workflows while allowing legitimate updates. |
| `POST /resume/{id}/score` | `20 / hour` | User ID | Prevents Groq API credit exhaustion from re-scoring loops. |
| `POST /resume/{id}/job-description` | `20 / hour` | User ID | Limits Groq LLM keyword gap analysis calls. |
| `POST /skill/*` | `20 / hour` | User ID | Limits vector generation and gap report recalculation. |

---

## 4. Scope & Isolation Confirmation

- **Authentication & JWT Logic:** Untouched (preserves previous story's verified HS256 JWT signature enforcement).
- **LLM Prompt Construction:** Untouched (`llm_service.py` unaltered).
- **Cloudinary URL Delivery:** Untouched (storage upload mechanism unaltered).

---

## 5. Recommended Next Prompt

> Run the Skill Intelligence backend end-to-end verification pass (Stories 5–7) against the live running stack now that authentication bypass, rate limiting, and file upload magic-byte validation remediations are complete.
