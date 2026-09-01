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
MARKETING_API_URL=http://127.0.0.1:8080
MARKETING_API_KEY=
```

Never put `SUPABASE_KEY`, `GEMINI_API_KEY`, or `RESEND_API_KEY` here. Those belong to Transit Intelligence and Marketing Backend.

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
