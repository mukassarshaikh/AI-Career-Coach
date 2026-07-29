# Frontend Architecture
## AI Career Coach Platform — Next.js App

Read `architecture.md` first for system context. This file defines the frontend folder structure, routing, state management, and component conventions in enough detail that the agent shouldn't need re-explaining each time.

---

## 1. Folder Structure

```
/frontend
  /app
    /(auth)
      /login/page.tsx
      /register/page.tsx
    /(dashboard)
      /dashboard/page.tsx              → consolidated summary view
      /resume/page.tsx                 → upload + list resumes
      /resume/[id]/page.tsx            → resume detail, ATS score, report
      /skill/page.tsx                  → skill-gap report view
      /learning/page.tsx               → roadmap list
      /learning/[roadmapId]/page.tsx   → roadmap detail, item tracking
      /career/page.tsx                 → chat advisor interface
      layout.tsx                        → shared dashboard shell (nav, sidebar)
    /api                                → Next.js route handlers (thin proxies to backend if needed, e.g. NextAuth)
    layout.tsx                          → root layout
    page.tsx                            → marketing/landing page

  /components
    /ui                                 → shadcn/ui primitives (button, card, dialog, etc.)
    /resume                             → ResumeUploadCard, AtsScoreGauge, KeywordGapList
    /skill                              → SkillGapRadarChart, MissingSkillsTable
    /learning                           → RoadmapTimeline, RoadmapItemCard, ProgressBar
    /career                             → ChatWindow, ChatMessageBubble, MockInterviewPanel
    /dashboard                          → SummaryCard, NextActionsList
    /layout                             → Sidebar, Navbar, PageHeader

  /lib
    /api                                → typed fetch functions per module (resumeApi.ts, skillApi.ts, learningApi.ts, careerApi.ts)
    /hooks                              → TanStack Query hooks (useResume, useSkillGap, useRoadmap, useChatSession)
    /auth                               → NextAuth config, session helpers
    /utils                              → formatting, constants

  /types
    resume.ts, skill.ts, learning.ts, career.ts, dashboard.ts   → shared TS interfaces matching backend Pydantic schemas

  /styles
    globals.css                        → Tailwind base + custom CSS variables
```

---

## 2. Routing Conventions

- Use **route groups** `(auth)` and `(dashboard)` to apply different layouts (auth pages have no sidebar; dashboard pages share a nav shell).
- Protected routes under `(dashboard)` check session via NextAuth middleware (`middleware.ts` at project root) — redirect to `/login` if unauthenticated.
- Dynamic routes (`[id]`, `[roadmapId]`) fetch their data via a TanStack Query hook inside a client component; the page itself can be a server component wrapper if SEO/SSR isn't needed for authenticated pages (most aren't — these are behind auth, so client-rendered is fine and simpler).

---

## 3. State Management

- **Server state** (resumes, skill reports, roadmaps, chat history): always via **TanStack Query**. Never duplicate server state into local component state beyond optimistic UI needs.
- **Async job polling** (resume scoring, roadmap generation): use `useQuery` with `refetchInterval` while job status is `pending`/`processing`, stop polling once `complete`/`failed`.
- **Local/UI state** (modal open/close, form inputs, active tab): plain `useState`. No global state library needed at MVP scale — if cross-page UI state becomes genuinely necessary later, add Zustand rather than Redux (lighter footprint).
- **Chat streaming state**: managed locally in the `ChatWindow` component via `useState` + `EventSource`/`fetch` streaming reader, appending tokens as they arrive; persisted message history still comes from TanStack Query on session load.

---

## 4. API Client Pattern

Each module gets a typed API file in `/lib/api`, e.g.:

```ts
// lib/api/resumeApi.ts
export async function uploadResume(file: File): Promise<{ resumeId: string; jobId: string }> { ... }
export async function getResume(id: string): Promise<Resume> { ... }
export async function getJobStatus(jobId: string): Promise<JobStatus> { ... }
```

Corresponding hook in `/lib/hooks`:

```ts
// lib/hooks/useResume.ts
export function useResume(id: string) {
  return useQuery({ queryKey: ['resume', id], queryFn: () => getResume(id) });
}
```

All requests attach the NextAuth session token automatically via a shared fetch wrapper (`/lib/api/client.ts`) that reads the session and sets the Authorization header.

---

## 5. Component Conventions

- One component per file, PascalCase filenames matching the export.
- Presentational components take typed props only — no direct data fetching inside them; fetching happens in the page/parent via hooks, passed down as props.
- Charts (Recharts) live in dedicated wrapper components (e.g. `SkillGapRadarChart.tsx`) that accept already-shaped data — no raw API shaping inside chart components.
- Use shadcn/ui primitives as the base for anything resembling a button, input, dialog, or card — don't hand-roll these from scratch.

---

## 6. Styling Conventions

- Tailwind utility classes directly in JSX; avoid separate CSS files except `globals.css` for base/theme variables.
- Maintain a small design-token set in `globals.css` (CSS variables for primary/secondary colors, radius) so charts and custom components can reference consistent colors rather than hardcoding hex values.

---

## 7. Auth Flow

- NextAuth.js configured in `/lib/auth/authOptions.ts` — credentials provider (email/password) for MVP, Google OAuth provider slot left in place but optional.
- Session available via `useSession()` client-side or `getServerSession()` in server components/middleware.
- Backend independently validates the NextAuth JWT on each API call (see `backend_architecture.md`) — frontend session state is not trusted as sole authorization.
