# Transit Dashboard

Streamlit UI for monthly Jyotiṣa transit reports. It talks only to Transit Intelligence FastAPI.

This package does **not** calculate transits, query Supabase, or call Gemini.

```text
STREAMLIT
  → POST /v1/transits/monthly
  → POST /v1/transits/monthly/rules
  → POST /v1/reports/monthly
```

The three steps stay separate. Do not merge them.

# Setup

```bash
cd "StreamLit Package"
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

# Environment

```env
TRANSIT_API_URL=http://127.0.0.1:8000
MARKETING_API_URL=
MARKETING_API_KEY=
```

`MARKETING_API_URL` defaults to `TRANSIT_API_URL`. The FastAPI route is `POST /v1/marketing/monthly-broadcasts` (creates a Resend draft, never sends). Never put `SUPABASE_KEY`, `GEMINI_API_KEY`, or `RESEND_API_KEY` here.

# Streamlit Cloud secrets

App settings → Secrets. Remote Marketing URLs require a key:

```toml
TRANSIT_API_URL = "https://your-transit-intelligence.a.run.app"
MARKETING_API_URL = "https://your-transit-intelligence.a.run.app"
MARKETING_API_KEY = "same-as-INGEST_API_KEY"
```

Keep the Streamlit app private. Anyone who can open Studio can create Resend drafts (not send them).

# Run locally

Terminal 1 — API (`Transit Intelligence`):

```bash
uvicorn app.main:app --reload --port 8000
```

Terminal 2 — dashboard:

```bash
streamlit run app/Home.py
```

Dashboard: http://localhost:8501  
API docs: http://127.0.0.1:8000/docs

# Tests

```bash
pytest
```
