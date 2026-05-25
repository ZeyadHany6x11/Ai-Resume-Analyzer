# AI Resume Analyzer & Job Matcher

Production-style resume analysis service for comparing a CV against a job
description using skill extraction, NLP preprocessing, semantic similarity, and
weighted ranking.

The project keeps the original Streamlit experience while adding a clean service
architecture and a FastAPI backend suitable for SaaS-style evolution.

## Features

- Streamlit UI for uploading a PDF or pasting resume text
- FastAPI backend with asynchronous background analysis jobs
- PDF/text parsing layer
- Skill extraction service backed by the existing skills catalog
- SentenceTransformers semantic similarity with TF-IDF fallback
- Weighted ranking and improvement suggestions
- SQLite repositories for job and result persistence
- In-memory TTL cache for expensive similarity operations
- Environment-based configuration
- Structured logging and typed application errors
- Deterministic pytest suite with fake providers for expensive dependencies

## Architecture

```text
resume_analyzer/
├── api/             # FastAPI routes and request/response schemas
├── cache/           # Cache interfaces and in-memory TTL adapter
├── database/        # SQLite connection and schema bootstrap
├── embeddings/      # Similarity providers and cache wrapper
├── parsers/         # PDF/text document parsing
├── ranking/         # Match scoring and report generation
├── repositories/    # Persistence boundaries for jobs/results
├── services/        # Business workflows and background job orchestration
└── utils/           # Logging and typed exceptions
```

`app.py` is intentionally thin: it handles Streamlit UI concerns and delegates
analysis work to the service layer.

## Local Setup

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

For a lighter CPU-only PyTorch install:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

## Run Streamlit

```bash
streamlit run app.py
```

Open `http://localhost:8501`.

## Run FastAPI

```bash
uvicorn resume_analyzer.api.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API docs.

### API Flow

- `GET /health`
- `POST /analyses/text`
- `POST /analyses/file`
- `GET /analyses/{analysis_id}/status`
- `GET /analyses/{analysis_id}`

Submission endpoints create a queued job, schedule background processing, and
return:

```json
{
  "analysis_id": "uuid",
  "status": "queued"
}
```

## Configuration

Copy `.env.example` to `.env` and adjust values as needed.

| Variable | Default | Description |
|---|---:|---|
| `RESUME_ANALYZER_APP_NAME` | `AI Resume Analyzer` | Application display name |
| `RESUME_ANALYZER_ENVIRONMENT` | `local` | Runtime environment |
| `RESUME_ANALYZER_LOG_LEVEL` | `INFO` | Python logging level |
| `RESUME_ANALYZER_DATABASE_PATH` | `resume_analyzer.db` | SQLite database path |
| `RESUME_ANALYZER_EMBEDDING_MODEL_NAME` | `all-MiniLM-L6-v2` | SentenceTransformer model |
| `RESUME_ANALYZER_CACHE_ENABLED` | `true` | Enable similarity cache |
| `RESUME_ANALYZER_CACHE_TTL_SECONDS` | `3600` | Cache TTL |
| `RESUME_ANALYZER_SEMANTIC_WEIGHT` | `0.6` | Semantic score weight |
| `RESUME_ANALYZER_SKILL_WEIGHT` | `0.4` | Skill overlap weight |
| `RESUME_ANALYZER_MAX_UPLOAD_SIZE_MB` | `10` | Intended upload size limit |

SQLite tables are created automatically when repository-backed workflows run.

## Testing

```bash
pytest
python -m compileall .
```

Tests use deterministic fakes for model-heavy behavior and an inline background
runner for reproducible job processing.

## Scoring

```text
Match Score = (0.6 x Semantic Similarity) + (0.4 x Skill Overlap Ratio)
```

The default weights can be adjusted through environment variables.

## Sample Job Description

```text
We are looking for a Senior Python Developer / Machine Learning Engineer.
Requirements:
- 5+ years of Python development experience
- Strong experience with Django or FastAPI for building REST APIs
- Machine learning experience using PyTorch, TensorFlow, or scikit-learn
- NLP or computer vision project experience is a strong plus
- Proficiency with PostgreSQL and Redis
- Experience with Docker, Kubernetes, and CI/CD pipelines
- Cloud experience on AWS or GCP
```
