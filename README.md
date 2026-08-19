# AI Career Coach

A free-tier, self-bootstrapped platform unifying four intelligence engines — **Resume**, **Skill**, **Learning**, and **Career Intelligence** — to help job seekers optimize resumes, close skill gaps, follow personalized learning roadmaps, and get conversational career guidance.

---

## 📚 Documentation Index

- **Backend Documentation**: [`backend/README.md`](./backend/README.md)
- **Frontend Documentation**: [`frontend/README.md`](./frontend/README.md)
- **Business Requirements Document (BRD)**: [`docs/brd.md`](./docs/brd.md)
- **Product Requirements Document (PRD)**: [`docs/prd.md`](./docs/prd.md)
- **Technical Specification (Data Models, APIs)**: [`docs/spec.md`](./docs/spec.md)
- **Agent Configuration & Rules**: [`GEMINI.md`](./GEMINI.md)

---

## 🛠️ Architecture & Tech Stack

- **Frontend**: Next.js 14 + React + TypeScript + Tailwind CSS + TanStack Query + Recharts (Hosted on Vercel)
- **Backend**: Python 3.10+ (FastAPI) + Uvicorn + SQLAlchemy AsyncIO + Alembic
- **Async Queue & Jobs**: Arq + Redis
- **Database**: Neon (PostgreSQL) + `pgvector` for embeddings
- **Local Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2` - 384 dimensions)
- **LLM Engine**: Groq API (`llama-3.3-70b-versatile`)
- **Authentication**: NextAuth.js
- **Cloud Storage**: Cloudinary (free tier)

---

## 🚀 Separate Quick Start Guides & Commands

Detailed guides are available in [`backend/README.md`](./backend/README.md) and [`frontend/README.md`](./frontend/README.md). Below is the complete command summary for both components.

> 💡 **Note**: All Python commands use `python -m <module>` so they run directly with Python even if executable binaries (like `uvicorn`, `pytest`, `alembic`) are not in system PATH.

---

### 🐍 1. Backend Setup & Commands

All commands below should be executed from the `backend/` directory.

#### Environment Setup
```bash
cd backend

# Create & activate virtual environment (Linux / macOS)
python3 -m venv venv
source venv/bin/activate

# Create & activate virtual environment (Windows PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Create & activate virtual environment (Windows CMD)
python -m venv venv
venv\Scripts\activate.bat

# Install backend dependencies
python -m pip install -r requirements.txt

# Copy environment variables template
cp .env.example .env
```

#### Database Migrations (Alembic)
```bash
# Run latest database migrations
python -m alembic upgrade head

# Generate a new migration script
python -m alembic revision --autogenerate -m "migration_description"

# Roll back the previous migration
python -m alembic downgrade -1
```

#### Market Skill Reference Data Seeding
```bash
# Seed initial skill reference data & download vector model (~80MB first time)
python -m app.db.seeds.market_skill_reference_seed
```

#### Running FastAPI Web Server (Uvicorn via Python)
```bash
# Start dev server with auto-reload (http://localhost:8000)
python -m uvicorn app.main:app --reload

# Start dev server on specific host and port
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

#### Background Queue Worker (Redis & Arq)
```bash
# Step A: Start Redis locally (Native)
redis-server

# OR using Docker:
docker run -d -p 6379:6379 redis:7-alpine

# Step B: Start Arq worker via Python in a separate backend terminal
python -m app.workers.worker_settings
# OR via Arq CLI module:
python -m arq app.workers.worker_settings.WorkerSettings
```
#### Running Backend Tests (Pytest via Python)
```bash
# Run all tests
python -m pytest

# Run tests with verbose output and console print statements
python -m pytest -v -s

# Run a specific test file
python -m pytest tests/test_parse_resume_job.py
```

---

### ⚛️ 2. Frontend Setup & Commands

All commands below should be executed from the `frontend/` directory.

#### Environment Setup & Dependencies Installation
```bash
cd frontend

# Install Node modules
npm install

# Copy environment variables template
cp .env.example .env.local
```

#### Development & Build Commands
```bash
# Start Next.js development server (http://localhost:3000)
npm run dev

# Run ESLint check
npm run lint

# Create production build
npm run build

# Start production server
npm run start
```

---

## 🧭 Build Phases

| Phase | Scope |
|---|---|
| **Phase 1** | Auth, resume upload/parsing, ATS scoring, keyword gap analysis, skill-gap report |
| **Phase 2** | Learning roadmap generation, progress tracking |
| **Phase 3** | Career Intelligence chat advisor, mock interviews |
| **Phase 4** | Live market data ingestion, notifications, scale-readiness |

---

## 📌 Status

🚧 **Active Development** — see [`docs/spec.md`](./docs/spec.md) for current build progress and technical roadmap.
