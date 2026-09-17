# CodeGuard AI

AI-assisted code quality and defect-risk analysis for Python code.

## Problem

Developers usually discover code problems during code review, testing, or
after bugs appear in production. Traditional tools detect individual issues
(complexity, style, security) in isolation, spread across separate reports.

## Solution

CodeGuard AI runs one analysis and answers, in one place:

1. How good is this code? → **Code Quality Score (0–100)**
2. What problems exist? → **Code smells + security findings**
3. Which functions are risky? → **Function-level risk table**
4. What's the predicted defect risk? → **ML-based risk model (LOW/MEDIUM/HIGH/CRITICAL)**
5. Why did it get this score? → **Explainable sub-scores + contributing factors**
6. What should I fix first? → **Prioritized recommendations**

Paste code → get metrics, code smells, security findings, a defect-risk
prediction, an AI explanation, and a downloadable PDF report.

**Important framing:** CodeGuard AI does **not** claim to predict whether
code will contain bugs. It estimates *Predicted Defect Risk* from measurable
code-quality signals. See [Limitations](#limitations).

## Features

- Paste-and-analyze workflow for Python source code
- Deterministic, explainable Code Quality Score (0–100) across 5 dimensions
- Code smell detection (long functions, high complexity, deep nesting, too
  many parameters, duplicate logic, large classes, poor naming, excessive
  comments)
- Basic Security Pattern Analysis (hardcoded secrets — masked, `eval`/`exec`,
  unsafe `subprocess`, weak hashes, SQL-injection-shaped string building)
- Explainable ML defect-risk model (scikit-learn) with per-feature
  contributions
- Prioritized, finding-based recommendations
- Optional LLM explanation (OpenAI-compatible) with a deterministic fallback
  that always works, even with no API key configured
- SHA-256-based analysis caching
- Background analysis jobs (QUEUED → RUNNING → COMPLETED/FAILED), non-blocking API
- Downloadable PDF report
- JWT authentication, per-user data isolation
- Dashboard with quality trend and risk-distribution charts, analysis history

## Architecture

```
        ┌───────────────────────┐
        │   Next.js Frontend    │
        │ Dashboard / Analyze / │
        │   Results / History   │
        └───────────┬───────────┘
                     │ REST (JWT)
                     ▼
        ┌───────────────────────┐
        │     FastAPI Backend   │
        └───────────┬───────────┘
                     │
      ┌──────────────┼──────────────┐
      ▼              ▼              ▼
 Code Metrics   Code Smells     Security
 (ast + radon)   (ast rules)   (ast + regex)
      │              │              │
      └──────────────┼──────────────┘
                      ▼
         Deterministic Quality Score
                      │
                      ▼
     scikit-learn Explainable Risk Model
                      │
                      ▼
       Recommendations + AI Explanation
                      │
                      ▼
              SQLite / PostgreSQL
```

The LLM is an **optional explanation layer only** — it never computes the
quality score or risk level; those come from the deterministic engine and
the ML model.

## Tech Stack

**Frontend:** Next.js 14 (App Router), TypeScript, Tailwind CSS, Recharts
**Backend:** FastAPI, SQLAlchemy, Pydantic, PyJWT
**Database:** SQLite by default (works with zero setup); swap to PostgreSQL
via `DATABASE_URL`
**Analysis:** Python `ast`, Radon (complexity + maintainability index)
**ML:** scikit-learn `LogisticRegression`
**Reports:** ReportLab (PDF)
**Testing:** pytest (41 tests)

> **Deviation from the original brief:** shadcn/ui component primitives were
> approximated directly with Tailwind utility classes rather than installing
> the shadcn CLI, to keep the dependency footprint small and the build
> reliable in network-restricted environments. Visual language (dark
> developer-tool theme, cards, badges) is equivalent.
>
> **Deviation:** the frontend uses system font stacks instead of
> `next/font/google` (Space Grotesk / Inter / IBM Plex Mono), because some
> build environments cannot reach `fonts.googleapis.com` at build time,
> which fails the Next.js build outright. See `frontend/app/layout.tsx` for
> a one-line note on restoring Google Fonts when you have build-time
> internet access.

## ML Approach

There is no bundled real-world labeled defect dataset. Rather than fake a
benchmark, `app/ml/risk_model.py`:

1. Generates a synthetic dataset where the training label is produced by a
   documented, weighted heuristic formula over normalized code features
   (complexity, function length, nesting, params, smell severity, security
   severity) plus Gaussian noise — so the model must genuinely learn the
   relationship, not memorize a lookup table.
2. Trains a scikit-learn `LogisticRegression` on that dataset (reproducible,
   fixed random seed).
3. Uses the model's predicted probability as the risk score, and reports
   per-feature contributions (`coefficient × normalized value`) for
   explainability.
4. Reports real accuracy **on the synthetic holdout set** — `tests/test_risk_model.py`
   asserts this is above 70%. This is explicitly a synthetic-data
   benchmark, not a real-world one. No fabricated accuracy numbers are used.

This is a clearly labeled heuristic/ML hybrid, per the project's core design
principle: never claim to predict real bugs with certainty.

## Code Quality Score Calculation

Deterministic and pure — same input always produces the same output
(`app/services/quality_score.py`). Five sub-scores are computed directly
from metrics and findings (no ML, no randomness):

| Dimension | Derived from |
|---|---|
| Maintainability | Radon maintainability index − smell penalties |
| Complexity | avg/max cyclomatic complexity |
| Security | severity-weighted security findings |
| Readability | naming issues, comment ratio |
| Structure | nesting depth, function length, parameter count |

Overall score = weighted average (`0.25 / 0.25 / 0.20 / 0.15 / 0.15`).

## Defect Risk Calculation

`RiskModel.predict()` normalizes 8 features into `[0,1]`, runs them through
the trained `LogisticRegression`, and maps the resulting probability to a
0–100 risk score and a LOW/MEDIUM/HIGH/CRITICAL band (25/50/75 thresholds).
Per-feature contributions are stored and can be surfaced for "why is this
risky" explanations.

## AI Explanation

`app/services/llm_service.py` calls an OpenAI-compatible
`/chat/completions` endpoint (configurable via `OPENAI_BASE_URL` /
`OPENAI_MODEL`, so OpenAI, OpenRouter, or any compatible provider works),
passing it **already-computed findings only** — it is instructed not to
invent new issues, scores, or line numbers. If `OPENAI_API_KEY` is unset,
the request times out, or the call fails for any reason, a deterministic
template explanation is used instead. The analysis pipeline never blocks
on or crashes because of the LLM.

## Database Schema

- `users` — id, email, hashed_password (PBKDF2 + salt)
- `analyses` — one row per analysis: status, code_hash, metrics, findings,
  security_findings, function_risk, sub_scores, recommendations,
  ai_explanation, risk fields, source_code, timestamps, user_id (FK)
- `analysis_cache` — code_hash → cached result JSON

Source code is stored per-analysis so results and the PDF can be
regenerated/viewed later; document this if you deploy with sensitive code
(see Limitations).

## API Documentation

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account, returns JWT |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/analysis` | Create analysis (cache-checked, queues background job) |
| GET | `/api/analysis` | List current user's analyses |
| GET | `/api/analysis/{id}` | Full analysis detail |
| GET | `/api/analysis/{id}/status` | Poll status only |
| GET | `/api/analysis/{id}/report` | Download PDF report |
| GET | `/health` | Health check |

All `/api/analysis*` routes require `Authorization: Bearer <token>` and are
scoped to the authenticated user (verified in `tests/test_api.py::test_history_isolated_per_user`).

Interactive docs: `http://localhost:8000/docs` (FastAPI auto-generated).

## Authentication

JWT bearer tokens (PyJWT, HS256), passwords hashed with PBKDF2-HMAC-SHA256
(100,000 iterations) + random salt. No plaintext passwords are ever stored
or logged.

## Background Jobs

`POST /api/analysis` returns immediately (`202 Accepted`) with status
`QUEUED`; the actual analysis runs in a background thread
(`app/services/analysis_service.py::execute_analysis_job`), moving through
`QUEUED → RUNNING → COMPLETED/FAILED`. The frontend polls
`GET /api/analysis/{id}/status` every ~900ms. This keeps the demo reliable
without adding Redis/Celery infrastructure — documented as an intentional
simplification for a local-dev-scale MVP (see Limitations).

## Caching

`app/services/cache_service.py` hashes `analysis_version:language:code`
with SHA-256. If an identical hash has been analyzed before by *any* user,
the cached result is returned instantly (`from_cache: true`, status
immediately `COMPLETED`) instead of re-running the pipeline.

## PDF Reports

`app/services/pdf_service.py` (ReportLab) generates a report with quality
score, sub-scores, metrics, code smells, security findings, and
recommendations. Secrets are never included (they're masked before they
ever reach the database). Download via the results page or
`GET /api/analysis/{id}/report`.

## Installation

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # edit if needed (defaults work out of the box)
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local # defaults to http://localhost:8000
```

## Running

**Backend** (from `backend/`, with venv active):
```bash
uvicorn app.main:app --reload --port 8000
```

**Frontend** (from `frontend/`, in a second terminal):
```bash
npm run dev
```

Then open **http://localhost:3000**.

By default the backend uses a local SQLite file (`backend/codeguard.db`),
created automatically on first run — no separate database setup required.
To use PostgreSQL instead, set `DATABASE_URL=postgresql://user:pass@host/db`
in `backend/.env` before starting the backend.

## Environment Variables

**backend/.env** (see `.env.example`):
```
DATABASE_URL=sqlite:///./codeguard.db
JWT_SECRET=change-me-to-a-long-random-string
JWT_EXPIRE_MINUTES=1440
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
MAX_CODE_LENGTH_CHARS=50000
```

**frontend/.env.local** (see `.env.local.example`):
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing

```bash
cd backend
source .venv/bin/activate
pytest -q
```

**Result: 41 passed.** Covers metric calculation, complexity, smell
detection, security pattern detection, quality score determinism, risk
classification, caching, auth (register/login/duplicate/isolation), full
analysis lifecycle (queued→completed and queued→failed), PDF generation,
LLM fallback (forced, no API key), invalid syntax, empty input, and
oversized input.

Frontend:
```bash
cd frontend
npm run build   # type-checks + production build
npm run lint    # ESLint
```

## Demo Workflow

1. Register / log in
2. Go to **Analyze**, click **"Load risky sample"** (or paste your own
   Python file)
3. Click **Analyze** → watch status go QUEUED → RUNNING → COMPLETED
4. Review quality score, defect risk, sub-scores, metrics, code smells,
   security findings, function-level risk, AI explanation, recommendations
5. Download the PDF report
6. Click **Analyze** again with the *same* code → note "Result loaded from
   cache" and instant completion
7. Load the **"good-quality sample"** and compare — verified in this repo:
   `sample_risky.py` scores **43.6/100, HIGH risk (63.8/100)** with 9 code
   smells and 6 security findings, vs. `sample_good.py` at **89.9/100, LOW
   risk (0/100)** with zero findings
8. Check **Dashboard** for the quality trend and risk distribution charts,
   and **History** for all past analyses

## Capstone Concepts Mapping

| Concept | Where |
|---|---|
| API Endpoints | `backend/app/routers/auth_router.py`, `backend/app/routers/analysis_router.py` |
| Database | `backend/app/models.py`, `backend/app/database.py` |
| Authentication | `backend/app/auth.py` (JWT + PBKDF2) |
| Background Jobs | `backend/app/services/analysis_service.py::execute_analysis_job` |
| PDF Reports | `backend/app/services/pdf_service.py` |
| Caching | `backend/app/services/cache_service.py` (SHA-256) |
| AI/ML | `backend/app/ml/risk_model.py` (scikit-learn), `backend/app/services/llm_service.py` (LLM explanation) |

## Limitations

- **Python only.** Other languages are not supported in this MVP.
- **No real-world defect dataset.** The risk model is trained on synthetic
  data derived from a documented heuristic — it demonstrates a genuine ML
  pipeline (feature engineering → training → explainable inference), not a
  production-grade bug predictor. See [ML Approach](#ml-approach).
- **Basic Security Pattern Analysis**, not a full security audit — it
  catches a small set of high-confidence patterns via AST + regex, and will
  miss anything subtler (no CVE database, no dataflow analysis). It never
  executes analyzed code, and never assume this replaces a real security audit.
- **Background jobs use an in-process thread**, not a real task queue
  (Celery/RQ). Fine for local-dev/demo scale; a production deployment
  behind multiple workers would need a shared queue instead.
- **Duplicate-logic detection** is a structural-hash heuristic (identical
  AST body across functions) — it will miss near-duplicates with minor
  variations.
- **Rate limiting is in-memory**, per-process — resets on restart and isn't
  shared across multiple backend instances.
- Source code is stored in the database per analysis (needed for the code
  viewer and PDF regeneration); don't paste highly sensitive code into a
  publicly deployed instance without reviewing this trade-off.

## Future Improvements

- Multi-language support (JavaScript/TypeScript/Java) via pluggable analyzers
- Real-world labeled training data (e.g. mined from public issue trackers)
- Transformer-based code embeddings as an additional ML feature
- Before/after comparison view for re-analyzed files
- Project/ZIP (multi-file) analysis
- Real background task queue (Celery/RQ + Redis) for horizontal scaling
- Restore `next/font/google` when build-time internet access is guaranteed

## Project Structure

```
codeguard-ai/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   ├── analyzers/       # metrics.py, smells.py, security.py
│   │   ├── ml/               # risk_model.py
│   │   ├── services/         # quality_score.py, recommendations.py,
│   │   │                       llm_service.py, pdf_service.py,
│   │   │                       cache_service.py, analysis_service.py
│   │   └── routers/          # auth_router.py, analysis_router.py
│   ├── tests/                # 41 pytest tests
│   ├── sample-data/           # sample_risky.py, sample_good.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/                   # /, /login, /register, /dashboard,
│   │   │                        /analyze, /analysis/[id], /history
│   ├── components/
│   ├── lib/api.ts
│   ├── package.json
│   └── .env.local.example
├── .gitignore
└── README.md
```

## Screenshots

Run the app locally and visit `/analyze` → `/analysis/[id]` to see the
results dashboard (quality dial, sub-scores, metrics grid, function risk
table, findings, and AI explanation) and `/dashboard` for the trend/risk
charts described above.

## GitHub Setup

```bash
cd codeguard-ai
git init
git add .
git commit -m "CodeGuard AI: initial capstone submission"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```
