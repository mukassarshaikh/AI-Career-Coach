# Design System
## AI Career Coach Platform

This is the authoritative visual and content design reference. Every frontend story must follow this exactly — no ad-hoc colors, fonts, spacing, or copy voice outside what's defined here. If a new UI need arises that isn't covered, extend this document first (propose the addition, get it confirmed), then build — don't invent a one-off exception in a component.

---

## 0. Design Thesis

AI Career Coach is not a chatbot product and shouldn't look like one. It's an instrument for charting a path — resume health, skill gaps, a learning route, career trajectory — across time. The visual language draws from **field instruments and topographic mapping**: precise, legible, quietly confident, built for someone making real decisions about their career, not a flashy AI-startup pitch page.

**Signature element:** a hand-plotted **ascending contour line** — think a single elevation line on a topographic map, or a plotted trajectory on an instrument display. This line motif recurs across the product at different scales: as a hero visual, as the shape of progress bars, as the spine of the roadmap timeline, as the stroke style in the skill-gap radar chart. It is the one thing that should make every screen recognizably part of the same product.

**What this product is not:** a gradient-blob SaaS landing page, a glassmorphism dashboard, a chatbot-with-rounded-bubbles app, or a cream-background-with-terracotta-accent AI demo. Avoid all of these explicitly (see Section 7).

---

## 1. Color Tokens

Define these as CSS variables in `globals.css` and reference them everywhere — never hardcode hex values in components.

| Token | Hex | Usage |
|---|---|---|
| `--color-ink` | `#1B2A22` | Primary text, primary UI ink (deep charcoal with a green undertone — not pure black) |
| `--color-paper` | `#F2F3EE` | Primary background (cool sage-tinted off-white, not warm cream) |
| `--color-paper-raised` | `#FFFFFF` | Card/surface background on top of paper |
| `--color-forest` | `#25443A` | Primary brand color — buttons, active states, primary links |
| `--color-forest-hover` | `#1D362D` | Hover/active state of forest |
| `--color-brass` | `#C89B3C` | Accent — achievement moments, highlights, the contour-line signature, milestone markers |
| `--color-brass-soft` | `#E8D9B0` | Light accent background (badges, subtle highlights) |
| `--color-teal` | `#3E6259` | Secondary data color — charts, skill visualizations, secondary emphasis |
| `--color-clay-alert` | `#B5533C` | Error/warning states only — used sparingly, never decoratively |
| `--color-ink-muted` | `#6B675E` | Secondary/muted text, captions, timestamps |
| `--color-line` | `#DAD8CE` | Hairline borders, dividers |

**Contrast rule:** `--color-ink` on `--color-paper` and `--color-paper-raised` must meet WCAG AA (4.5:1) for body text — verify before shipping, don't eyeball it.

**Do not introduce:** purple, blue-violet gradients, neon/acid accents, or any color not in this table without updating this doc first.

---

## 2. Typography

Three roles, used with restraint — not decoration for its own sake.

| Role | Typeface | Usage |
|---|---|---|
| Display | **Fraunces** (variable, use optical size + soft italic for select moments) | Page headlines, module titles, the hero statement. Used sparingly — never for body copy or UI labels. |
| Body | **IBM Plex Sans** | All body text, form labels, navigation, buttons, general UI copy |
| Utility / Data | **IBM Plex Mono** | Scores, numbers, skill tags, timestamps, code-like data (ATS score, demand weights, dates) — anything that is data rather than prose |

**Type scale (Tailwind `fontSize` extension):**
- `display-xl`: 3.5rem / 1.05 — Fraunces, for the main dashboard/marketing headline only
- `display-lg`: 2.5rem / 1.1 — Fraunces, module page titles (Resume, Skill, Learning, Career)
- `display-md`: 1.75rem / 1.2 — Fraunces, card/section headers
- `body-lg`: 1.125rem / 1.6 — Plex Sans, intro paragraphs
- `body`: 1rem / 1.6 — Plex Sans, default body
- `body-sm`: 0.875rem / 1.5 — Plex Sans, captions/secondary
- `data-lg`: 2rem / 1 — Plex Mono, hero numbers (ATS score, gap count)
- `data`: 0.875rem / 1.4 — Plex Mono, inline data/tags

**Rule:** Fraunces never appears in a button, form input, or nav item — display type is for narrative moments only, not UI chrome.

---

## 3. Layout & Spacing

- Spacing scale: Tailwind default 4px base scale (`1` = 4px) — no custom scale needed, but **be consistent**: card padding always `p-6` or `p-8`, section gaps always `gap-8` or `gap-12`, never mix arbitrary values like `p-5` and `p-7` in siblings.
- Radius scale: `rounded-md` (6px) for buttons/inputs, `rounded-xl` (12px) for cards, **never** `rounded-full` except for avatars/status dots. No pill-shaped buttons — this is an instrument, not a bubbly consumer app.
- Shadows: minimal. One elevation level only — `shadow-sm` equivalent (a soft, low-opacity shadow) for raised cards on the paper background. No glassmorphism, no blurred glow shadows, no colored shadows.
- Borders: prefer `--color-line` hairline borders over shadows for separating content where possible — this reinforces the "instrument/map" precision feeling.
- Grid: dashboard content max-width `1280px`, centered, with a consistent `24px`/`32px` gutter (mobile/desktop).

---

## 4. The Signature Motif — Contour Line

This is the one recurring visual element. Apply it as follows:

- **Hero (landing/dashboard):** a single plotted ascending line (SVG path, hand-drawn quality — slightly irregular, not a perfect bezier) rendered in `--color-brass`, representing "your trajectory." This is the one bold visual moment — everything else stays quiet.
- **Progress bars (roadmap items, upload polling status):** the fill of the progress bar follows a subtle contour-line texture at low opacity rather than a flat gradient fill.
- **Skill-gap radar chart:** the Recharts radar stroke uses `--color-teal` with the same hand-drawn line quality; missing-skill points marked with a small `--color-brass` dot.
- **Roadmap timeline:** the connecting spine between roadmap items is rendered as this contour line, ascending left-to-right or top-to-bottom, with milestones as brass dots along it.
- **ATS score gauge:** an arc gauge (not a circular donut with a gradient) where the fill follows the contour-line stroke style.

**Restraint rule:** this motif appears once per screen as a structural element (chart, progress indicator, timeline) — never as decorative background texture scattered across a page. One strong signature, everything else quiet, per the design brief's core discipline.

---

## 5. Components

- **Buttons:** solid `--color-forest` background for primary actions, `--color-ink` text on transparent/outlined for secondary, `--color-clay-alert` reserved only for destructive actions (never for anything else). `rounded-md`, Plex Sans, medium weight, sentence case (never ALL CAPS, never Title Case Everywhere).
- **Cards:** `--color-paper-raised` background, `rounded-xl`, hairline `--color-line` border, `shadow-sm`, `p-6` or `p-8` internal padding.
- **Forms:** labels always visible (never placeholder-only labels), `--color-line` border on inputs, `--color-forest` border/ring on focus — focus states must be clearly visible for keyboard navigation (WCAG requirement carried from BRD/PRD).
- **Badges/tags:** used for skill tags, difficulty levels — `--color-brass-soft` background with `--color-ink` text, `rounded-md` not pill-shaped, Plex Mono for the label if it's a data value (e.g. a skill name) vs Plex Sans if it's a status word.
- **Empty states:** per Section 6's voice guidance — never a generic "No data yet" with a sad illustration. Write the empty state as a direct next action (e.g., resume list empty → "Upload your first resume to get an ATS score and skill-gap report.").
- **Icons:** use `lucide-react` exclusively for UI icons (already an approved dependency) — no emoji, no mismatched icon sets, no custom SVG icons unless they're part of the signature contour-line system itself.

---

## 6. Content & Copy Voice

Per the product's actual job — helping someone make real career decisions — the voice is **direct, competent, and respectful of the user's time**. Not cheerful startup marketing-speak, not clinical/robotic either.

- **Active voice, plain verbs:** "Upload your resume" not "Resume upload functionality." A button that says "Generate roadmap" produces a result described as "Roadmap generated," not "Success!"
- **Name things by what the user controls:** "Your target role," not "target_role parameter." "Skills you're missing," not "Skill deficit vector."
- **No filler, no hype:** Never "Supercharge your career with AI!" — say what the feature actually does. "See which skills employers are asking for that your resume doesn't show yet."
- **Errors describe what happened and what to do**, in the interface's voice, never apologetic: "That file couldn't be read. Upload a PDF or DOCX under 10MB." — not "Oops! Something went wrong 😢."
- **Data-driven copy stays precise:** "72/100 ATS score — formatting is strong, keyword match is weak" rather than vague praise/criticism.
- **Disclaimers (legal/visa/compensation topics in Career Intelligence chat)** stay in this same plain, respectful voice — not a boilerplate legal-sounding insert that breaks tone.

---

## 7. Explicit Anti-Patterns (do not do these)

- Cream/off-white background paired with a serif display and a terracotta/clay accent (a recognizable AI-generated-demo tell)
- Near-black background with a single neon/acid accent color
- Purple-to-blue gradient buttons or backgrounds
- Glassmorphism (frosted blur cards)
- Rounded-full pill buttons everywhere
- Generic 3-icon-in-a-circle feature grids with no relationship to real content
- Stock "AI brain" or robot iconography/illustration
- Numbered (01/02/03) section markers unless the content is a genuine sequence (the roadmap timeline qualifies; a features list does not)
- Placeholder-only form inputs with no visible label
- Emoji in UI copy or error/empty states

---

## 8. Application Across the Four Modules

Use this to keep every module feeling like the same product, not four separate mini-apps:

| Module | How the signature motif appears | Primary accent used |
|---|---|---|
| Resume Intelligence | ATS score arc gauge using the contour-line stroke | `--color-forest` primary, `--color-brass` for score highlight |
| Skill Intelligence | Radar chart in `--color-teal` with brass dots marking gaps | `--color-teal` primary |
| Learning Intelligence | Roadmap timeline spine as the ascending contour line, brass milestone dots | `--color-brass` primary (achievement framing fits milestones) |
| Career Intelligence | Chat UI stays quiet/plain (Plex Sans only, no display type, no motif) — this module's job is conversation clarity, not visual flourish | `--color-forest` for user messages, `--color-paper-raised` for assistant messages |

---

## 9. Tailwind Implementation Notes

- Extend `tailwind.config.ts` with the color tokens (Section 1) as named colors (`forest`, `paper`, `brass`, `teal`, `clay`, `ink`) mapped to the CSS variables, not raw hex — so theming stays centralized in `globals.css`.
- Add `Fraunces`, `IBM Plex Sans`, and `IBM Plex Mono` via `next/font/google` (self-hosted by Next.js, free, no external font-loading dependency) — configure in the root layout, expose as CSS variables (`--font-display`, `--font-body`, `--font-mono`) and reference in `tailwind.config.ts`'s `fontFamily`.
- Do not use shadcn/ui's default theme colors as-is — override the CSS variables shadcn/ui reads (`--primary`, `--background`, etc.) to point at this system's tokens, so shadcn components inherit this palette automatically rather than looking like default shadcn.

---

## 10. Logo / Wordmark Direction

A simple wordmark treatment is sufficient for MVP — no complex logo mark needed yet:
- Product name set in Fraunces (medium weight), with a small contour-line glyph (a minimal ascending squiggle, 2-3 strokes) placed before or above the wordmark in `--color-brass`.
- Keep it monochrome-capable (works in pure `--color-ink` for places a colored logo can't render, e.g. favicons at small sizes).
