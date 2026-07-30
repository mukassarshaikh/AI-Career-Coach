# Product Requirements Document (PRD)
## AI Career Coach Platform

**Document Version:** 1.0
**Date:** July 29, 2026
**Status:** Draft
**Related Document:** brd.md (Business Requirements Document)

---

## 1. Product Overview

AI Career Coach is a web platform that unifies four intelligence engines — Resume, Skill, Learning, and Career — into a single continuously-learning system that helps job seekers optimize their resumes, close skill gaps, follow personalized learning roadmaps, and get 24/7 conversational career guidance.

This PRD translates the BRD's business requirements into concrete product features, user flows, and a finalized (zero-cost) technical implementation plan.

---

## 2. Goals

- Ship a working MVP using entirely free-tier infrastructure — no paid services, no credit card commitments.
- Deliver the four core modules (Resume, Skill, Learning, Career Intelligence) as a single connected experience, not siloed tools.
- Keep the architecture simple enough for a solo/small team to build and maintain, while remaining scalable if usage grows later.

---

## 3. Target Users

| Persona | Description | Primary Need |
|---|---|---|
| Active Job Seeker | Applying to multiple roles, needs ATS-optimized resumes fast | Resume Intelligence, Career Intelligence (interview prep) |
| Early/Mid-Career Professional | Wants to move up or pivot roles | Skill Intelligence, Learning Intelligence |
| Career Switcher | Moving into a new industry/role entirely | All four modules, especially skill-gap + roadmap |

---

## 4. Finalized Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend Framework | Next.js + React + TypeScript | App Router, SSR for dashboard/marketing pages |
| Styling | Tailwind CSS | Utility-first, fast to build accessible UI |
| Data Fetching / Async State | TanStack Query | Handles polling for async resume scoring jobs |
| Charts / Visualization | Recharts | Skill-gap radar, ATS score trends, roadmap progress |
| Frontend Hosting | Vercel (Free Tier) | Native Next.js support, zero-config deploys |
| Backend Framework | Python (FastAPI) | Async-native, good fit for AI/NLP-heavy endpoints |
| Backend Hosting | Oracle Cloud Free Tier | Always-on (4 ARM CPUs / 24GB RAM), no cold starts |
| Database | Neon (Postgres, Free Tier) | Serverless Postgres, no sleep-based data loss |
| Vector Search | pgvector (Postgres extension) | Skill-vector similarity, avoids a separate vector DB |
| LLM Provider | Groq API (Free Tier) | Fast inference, generous free rate limits, Llama models |
| Resume Parsing | pdf-parse (+ mammoth.js for DOCX) | Free text extraction, structured via LLM post-processing |
| Auth | NextAuth.js (Auth.js) | Free, integrates natively with Next.js |
| File Storage | Cloudinary (Free Tier, 25GB) | Resume PDF/DOCX uploads |
| Job Queue | BullMQ (Redis-backed) | Async resume scoring / roadmap regeneration |

> **Note on BullMQ + FastAPI:** BullMQ is a Node.js library and does not run natively inside a Python/FastAPI process. Two options:
> 1. Run a small Node.js worker service (free-tier) purely for queue processing, communicating with FastAPI via Redis/HTTP.
> 2. Use a Python-native equivalent instead — **Celery** or **Arq** (both free, open source) backed by the same free Redis instance — which avoids running two languages for the backend.
> Recommendation: use **Arq** (lightweight, async-native, pairs naturally with FastAPI) unless there's a specific reason to keep BullMQ.

**Redis (for queues + caching):** Self-hosted on the same Oracle free VM, or Upstash free tier — not listed above but required to support the job queue layer.

---

## 5. Feature Requirements by Module

### 5.1 Resume Intelligence
- Upload resume (PDF/DOCX) → parsed via pdf-parse/mammoth.js → structured via Groq LLM into JSON (experience, education, skills, achievements)
- ATS compatibility score (formatting, section structure, parseability)
- Grammar/tone/clarity audit with inline suggestions (Groq LLM)
- Paste/select target job description → keyword gap analysis
- Prioritized action list to improve match score
- Re-score on edit (async job via queue, polled from frontend with TanStack Query)

### 5.2 Skill Intelligence
- Extract "skill vector" from parsed resume data
- Compare against a market skill-demand reference set (static curated dataset for MVP — see Section 7, Phase 1)
- Skill-gap report: missing skills ranked by relevance/demand weight
- Periodic refresh of gap analysis as resume or market reference updates
- Skill vectors and market reference embeddings stored via pgvector for similarity scoring

### 5.3 Learning Intelligence
- Generate step-by-step roadmap per skill gap (LLM-generated: courses, articles, projects, milestones)
- Sequence items by dependency/difficulty
- Track completion status per roadmap item
- Recalculate skill vector when items are marked complete
- Regenerate/adjust roadmap when new gaps are identified (async job)

### 5.4 Career Intelligence
- Conversational chat interface (Groq-powered, streaming responses)
- Mock interview scenarios based on target role
- Text-based feedback on interview answers
- Career strategy Q&A (negotiation, pivots, promotion readiness)
- Session context maintained across chat; references user's resume/skill/roadmap data when relevant
- Disclaimer shown for legal/visa/compensation-adjacent topics (per BRD risk mitigation)

### 5.5 Platform / Cross-Cutting
- Unified user profile shared across all four modules (single Postgres schema)
- Consolidated dashboard: resume score, skill gaps, roadmap progress, suggested next actions
- In-app notifications for roadmap milestones and significant skill/market updates
- Auth via NextAuth.js (email/password + optional OAuth, e.g., Google — free)

---

## 6. Non-Functional Requirements (Carried from BRD)

| Category | Requirement | Free-Stack Implication |
|---|---|---|
| Performance | Resume analysis completes within 10 seconds | Handle via async job (Arq/BullMQ) + polling, not a blocking request |
| Data Privacy | Encrypted at rest/in transit; GDPR/CCPA-aware | Neon encrypts at rest by default; enforce HTTPS everywhere (Vercel/Oracle both support free TLS via Let's Encrypt) |
| Availability | Aim for high uptime | Oracle Free Tier VM is always-on (no cold starts); Neon free tier has no forced sleep |
| Accuracy | ATS scoring validated against benchmarks | Manual benchmark validation in MVP; no paid benchmark service |
| Accessibility | WCAG 2.1 AA | Use shadcn/ui + semantic HTML + Tailwind's accessible defaults |
| Auditability | Log AI-generated recommendations | Store LLM inputs/outputs in Postgres for review |

---

## 7. Phased Build Plan

| Phase | Deliverables |
|---|---|
| **Phase 1 (MVP)** | Auth, resume upload/parsing, ATS scoring, grammar audit, keyword gap analysis, static market skill-reference dataset, basic skill-gap report |
| **Phase 2** | Learning roadmap generation, progress tracking, skill-vector recalculation on completion |
| **Phase 3** | Career Intelligence chat advisor, mock interview flow, session context |
| **Phase 4** | Live market data ingestion (replace static reference set), dashboard notifications, scale-readiness (rate-limit handling for Groq free tier, caching layer) |

---

## 8. Key Constraints (Free-Tier Reality Check)

- **LLM rate limits:** Groq's free tier has request-per-minute/day caps — design the chat and scoring flows to queue/throttle gracefully rather than fail hard.
- **Static market data first:** Real-time job-posting ingestion (BRD FR-2.2) requires a licensed data feed, which isn't free. Phase 1–3 use a manually curated/periodically-updated skill-demand reference dataset (e.g., pulled from public sources like BLS, LinkedIn public reports, or open job-posting datasets) instead of a live paid feed.
- **Storage caps:** Cloudinary free tier (25GB) and Neon free tier storage limits are generous for MVP but should be monitored as user count grows.
- **No paid support/SLA:** Acceptable tradeoff for a zero-cost bootstrap; revisit if the product gains real traction.

---

## 9. Success Metrics (Carried from BRD, Section 11)

| Metric | Target (6 Months Post-Launch) |
|---|---|
| Resume ATS score improvement (avg.) | +25% |
| Interview callback rate increase | +15% |
| Skill-gap roadmap completion rate | ≥40% |
| MAU retention (3 months) | ≥50% |
| Chat advisor engagement | ≥3 sessions/user/month |
| NPS | ≥40 |

---

## 10. Open Questions

- Which specific Python queue library — Arq vs. Celery vs. keeping a small Node/BullMQ worker — should be finalized before backend scaffolding begins.
- Which public data source(s) will seed the static market skill-demand reference set for Phase 1.
- Whether OAuth providers (Google/GitHub) are needed at launch or email/password auth is sufficient for MVP.

---

*End of Document*