# Setup & Run

## 1. Backend (FastAPI)

```bash
cd backend

# Pick one — venv or conda:
python -m venv .venv && source .venv/bin/activate
# OR: conda create -n logtriage python=3.11 && conda activate logtriage

pip install -r requirements.txt
```

Edit `backend/.env` and set your key:

```
OPENAI_API_KEY=sk-...
```

Run the API:

```bash
uvicorn main:app --reload --port 8000
```

Health check: http://localhost:8000/health

## 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

## 3. Try it

Use the files in `sample_logs/`:

- `sample.json` — mixed entries; expect several flagged (3 AM brute-force,
  privilege escalation, malware upload, sensitive-path access).
- `sample.csv` — same format as columns; includes a brute-force burst and
  a sudo on `/etc/passwd`.

Drop one in the upload panel and click **Analyze**.

## Configuration

- Triage threshold: edit `TRIAGE_THRESHOLD` in `backend/main.py` (default `40`).
- Model: set `OPENAI_MODEL` in `.env` (defaults to `gpt-4o`).
- CORS origin: `backend/main.py` allows `http://localhost:5173` by default.
