# AI Career Coach — Backend Service

FastAPI-powered backend service providing core intelligence capabilities for the AI Career Coach platform: resume parsing, ATS scoring, local vector embedding generation (`sentence-transformers`), keyword gap analysis, skill gap calculation, market reference data seeding, and asynchronous background job execution with Arq and Redis.

---

## 🛠️ Tech Stack

- **Framework**: FastAPI + Uvicorn
- **Database**: Neon PostgreSQL with `pgvector` extension
- **ORM & Migrations**: SQLAlchemy (AsyncIO) + Alembic
- **Async Queue**: Arq + Redis
- **Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional vectors, cached locally)
- **LLM Provider**: Groq API (`llama-3.3-70b-versatile`)
- **Storage**: Cloudinary API (free-tier PDF/Docx storage)
- **Testing**: Pytest + Pytest-AsyncIO

---

## 📋 Prerequisites

- **Python**: 3.10 or higher
- **Redis**: Local installation, Docker container, or Upstash instance (port `6379`)
- **PostgreSQL**: Neon DB or any Postgres instance with `pgvector` enabled

---

## 🚀 Quick Setup & Configuration

### 1. Set Up Virtual Environment

#### Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows (PowerShell)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Windows (CMD)
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

---

### 2. Install Dependencies

```bash
python -m pip install -r requirements.txt
```

---

### 3. Environment Variables Setup

Copy the template file to create your local `.env`:

```bash
cp .env.example .env
```

Ensure the following variables are set inside `.env`:

```ini
DATABASE_URL=postgresql://<user>:<password>@<host>/neondb?sslmode=require
REDIS_URL=redis://localhost:6379
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
CLOUDINARY_CLOUD_NAME=your_cloudinary_cloud_name
CLOUDINARY_API_KEY=your_cloudinary_api_key
CLOUDINARY_API_SECRET=your_cloudinary_api_secret
NEXTAUTH_SECRET=your_shared_nextauth_secret
BACKEND_CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development
```

---

## 💻 Commands Reference (Using `python -m`)

> 💡 **Note**: All commands use `python -m <module>` so they run directly with Python even if executable binaries (like `uvicorn`, `pytest`, `alembic`) are not in your system environment PATH.

### 1. Database Migrations (Alembic)

- **Apply all migrations to latest schema**:
  ```bash
  python -m alembic upgrade head
  ```

- **Generate a new migration script**:
  ```bash
  python -m alembic revision --autogenerate -m "describe_your_changes"
  ```

- **Roll back the latest migration**:
  ```bash
  python -m alembic downgrade -1
  ```

---

### 2. Market Skill Reference Data Seeding

Seed default taxonomy and market skill vectors into Postgres:

```bash
python -m app.db.seeds.market_skill_reference_seed
```

> ℹ️ **Note on First Run**: The seed script downloads `all-MiniLM-L6-v2` (~80MB) from Hugging Face on its initial run. Subsequent runs will use the locally cached embedding model.

---

### 3. Run FastAPI Web Server (Uvicorn via Python)

- **Start server in hot-reload development mode**:
  ```bash
  python -m uvicorn app.main:app --reload
  ```

- **Start server on custom host and port**:
  ```bash
  python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```

- **Interactive API Documentation**:
  - **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
  - **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### 4. Run Async Background Queue (Redis & Arq Worker)

The background worker handles asynchronous tasks (`parse_resume`, `score_resume`, `analyze_keywords`, `generate_skill_vector`, `compute_skill_gap`).

- **Start Redis**:
  - *Native / Service*:
    ```bash
    redis-server
    ```
  - *Using Docker*:
    ```bash
    docker run -d -p 6379:6379 redis:7-alpine
    ```

- **Start Arq Worker Process via Python**:
  ```bash
  python -m app.workers.worker_settings
  ```
  *Alternative CLI method via Python*:
  ```bash
  python -m arq app.workers.worker_settings.WorkerSettings
  ```

---

### 5. Running Tests (Pytest via Python)

- **Run full test suite**:
  ```bash
  python -m pytest
  ```

- **Run tests with verbose logs & standard output**:
  ```bash
  python -m pytest -v -s
  ```

- **Run a specific test file**:
  ```bash
  python -m pytest tests/test_parse_resume_job.py
  ```

---

## 📁 Directory Structure

```
backend/
├── alembic/                # Database migration scripts & env configuration
├── alembic.ini             # Alembic migration configuration
├── app/
│   ├── api/                # FastAPI routers and route handlers
│   ├── core/               # App configuration, security, CORS settings
│   ├── db/                 # Database connection sessions & seed scripts
│   ├── models/             # SQLAlchemy ORM models
│   ├── schemas/            # Pydantic schemas (request/response)
│   ├── services/           # Business logic, embedding, LLM client, parsing
│   ├── workers/            # Arq worker settings and async background jobs
│   └── main.py             # FastAPI entry point
├── tests/                  # Pytest async test suite
├── .env.example            # Environment variables template
└── requirements.txt        # Python package dependencies
```
