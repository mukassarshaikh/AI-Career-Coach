# AI Career Coach — Frontend Web App

Next.js 14 web application for the AI Career Coach platform, offering user interfaces for resume upload and management, real-time ATS scoring, keyword gap visualization, personalized learning roadmaps, skill gap analytics, and conversational career advice.

---

## 🛠️ Tech Stack

- **Framework**: Next.js 14 (App Router) + React 18 + TypeScript
- **Styling**: Tailwind CSS + PostCSS + Autoprefixer
- **State & Data Fetching**: TanStack React Query v5 (with Devtools)
- **Charts & Visualizations**: Recharts
- **Icons**: Lucide React
- **Authentication**: NextAuth.js
- **UI Helpers**: `clsx` + `tailwind-merge`

---

## 📋 Prerequisites

- **Node.js**: 18.17.0 or higher
- **npm** (or `pnpm` / `yarn`)

---

## 🚀 Quick Setup & Configuration

### 1. Install Dependencies

Navigate to the `frontend` directory and install packages:

```bash
cd frontend
npm install
```

---

### 2. Environment Variables Setup

Copy the `.env.example` file to create your local `.env.local`:

```bash
cp .env.example .env.local
```

Ensure the following variables are configured in `.env.local`:

```ini
# --- Auth (NextAuth.js) ---
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your_shared_nextauth_secret

# --- Backend API Connection ---
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000

# --- Environment ---
ENVIRONMENT=development
```

> ⚠️ **Important**: Ensure `NEXTAUTH_SECRET` matches the `NEXTAUTH_SECRET` configured in `backend/.env`.

---

## 💻 Commands Reference

### 1. Run Development Server

Start the local Next.js development server with hot reload:

```bash
npm run dev
```

- Open [http://localhost:3000](http://localhost:3000) in your web browser.

---

### 2. Code Quality & Linting

Run ESLint to check for code style issues and TypeScript errors:

```bash
npm run lint
```

---

### 3. Production Build

Build the optimized application bundle for production:

```bash
npm run build
```

---

### 4. Run Production Server

Start the built production server locally:

```bash
npm run start
```

---

## 📁 Directory Structure

```
frontend/
├── app/                    # Next.js 14 App Router pages, layouts, and API routes
├── components/             # Reusable UI components (buttons, cards, navigation, charts)
├── lib/                    # API client utilities, query client, NextAuth configuration
├── styles/                 # Global styles and Tailwind CSS configurations
├── types/                  # TypeScript interfaces and type definitions
├── middleware.ts           # Route protection & authentication middleware
├── next.config.mjs         # Next.js configuration
├── tailwind.config.ts      # Tailwind CSS design system configuration
├── .env.example            # Environment variables template
└── package.json            # Scripts and dependencies
```
