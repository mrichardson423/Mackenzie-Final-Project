Build a full-stack AI-powered security log triage application with the following architecture:

---

## PROJECT OVERVIEW

An automated security log triage tool that:
1. Accepts uploaded log files (JSON or CSV) via a React/Vite frontend
2. Parses and scores logs using rule-based Python logic in a FastAPI backend
3. Sends enriched results to OpenAI for transparent, plain-language explanations
4. Returns structured analysis back to the frontend for display

The core design philosophy is **transparency** — every score must be explainable, and the AI reasoning must be visible to the analyst.

---

## STACK

- **Frontend**: React + Vite (TypeScript preferred)
- **Backend**: FastAPI (Python 3.11+)
- **AI**: OpenAI API (`gpt-4o` or `gpt-4-turbo`)
- **Communication**: REST (JSON over HTTP, CORS enabled for localhost dev)

---

## BACKEND (`/backend`)

### FastAPI App (`main.py`)
- `POST /upload` — accepts a multipart file upload (JSON or CSV log file)
  - Parses the file
  - Runs rule-based triage to assign a risk score (0–100 or LOW/MEDIUM/HIGH/CRITICAL) to each log entry
  - Filters to entries that scored above a configurable threshold
  - For each flagged entry, calls OpenAI with a structured prompt (see below)
  - Returns a list of enriched triage results as JSON

### Log Parser (`parser.py`)
- Support both JSON (array of log objects) and CSV formats
- Normalize each log entry into a consistent internal dict schema with fields like:
  - `timestamp`, `source_ip`, `dest_ip`, `event_type`, `user`, `status_code`, `action`, `raw` (original entry)

### Rule-Based Triage Engine (`triage.py`)
- Score each log entry 0–100 based on rules such as:
  - Failed login attempts (especially repeated)
  - Privilege escalation events
  - Unusual access hours (e.g., 2–5 AM)
  - Access to sensitive paths/resources
  - Anomalous source IPs or geolocation mismatches
  - High-volume requests from a single source
  - Known bad event types (e.g., `EXEC`, `DELETE`, `AUTH_FAIL`)
- Each rule that fires should be recorded with a label and weight
- Output per entry: `{ score: int, risk_level: str, triggered_rules: list[str], log_entry: dict }`

### OpenAI Integration (`explainer.py`)
- For each flagged entry, call OpenAI with a structured system + user prompt
- The system prompt should instruct the model to act as a senior SOC (Security Operations Center) analyst providing structured analysis
- The user prompt should include:
  - The raw log entry
  - The triggered rule labels and their weights
  - The final risk score
- Request a JSON-structured response with exactly these fields:
```json
  {
    "summary": "One sentence summary of what happened",
    "triggered_fields": ["field1", "field2"],
    "reasoning": "Why this was scored the way it was",
    "ruled_out": "What the model considered and dismissed",
    "benign_explanations": "Plausible innocent explanations, if any",
    "confidence_reasoning": "Why the confidence is high/medium/low",
    "recommended_actions": ["action1", "action2"]
  }
```
- Use `response_format: { type: "json_object" }` in the OpenAI call to enforce structured output
- Load the OpenAI API key from a `.env` file using `python-dotenv`

### Dependencies (`requirements.txt`)
- fastapi
- uvicorn
- python-multipart
- openai
- python-dotenv
- pandas

---

## FRONTEND (`/frontend`)

### React/Vite App
Bootstrap with `npm create vite@latest frontend -- --template react-ts`

### UI Flow
1. **Upload Screen** — A clean drag-and-drop or file input that accepts `.json` or `.csv` log files, plus an "Analyze" button
2. **Loading State** — Show a spinner/progress indicator while the backend processes
3. **Results Screen** — For each flagged log entry, display a card showing:
   - Risk level badge (color-coded: green/yellow/orange/red)
   - Risk score
   - Triggered rule tags
   - Expandable AI analysis panel with all 7 OpenAI fields rendered cleanly
   - The raw log entry in a collapsible code block
4. **No results state** — friendly message if no entries exceeded the threshold

### API Communication
- Use `fetch` or `axios` to `POST` to `http://localhost:8000/upload` with `FormData`
- Handle and display error states from the API

---

## PROJECT STRUCTURE
project-root/  
├── backend/  
│   ├── main.py  
│   ├── parser.py  
│   ├── triage.py  
│   ├── explainer.py  
│   ├── .env           # OPENAI_API_KEY=sk-...  
│   └── requirements.txt  
├── frontend/  
│   ├── src/  
│   │   ├── App.tsx  
│   │   ├── components/  
│   │   │   ├── UploadPanel.tsx  
│   │   │   ├── ResultCard.tsx  
│   │   │   └── AIAnalysisPanel.tsx  
│   │   └── api.ts     # fetch wrapper  
│   └── package.json  
└── README.md  

---

## SAMPLE LOG FORMAT TO SUPPORT

JSON:
```json
[
  {
    "timestamp": "2024-01-15T02:34:11Z",
    "source_ip": "192.168.1.55",
    "dest_ip": "10.0.0.1",
    "user": "jsmith",
    "event_type": "AUTH_FAIL",
    "action": "LOGIN",
    "status_code": 401,
    "resource": "/admin/panel"
  }
]
```

CSV: same fields as column headers.   

---

## ETHICAL DESIGN NOTES (important — bake this into the system prompt and README)

This tool is designed around **transparency and human oversight**:
- The AI never makes final decisions — it provides reasoning, and a human analyst retains authority
- Every score is traceable to specific fired rules
- Benign explanations are always surfaced so analysts are not anchored to the AI's framing
- The model is explicitly instructed to reason about what it ruled out, not just what it flagged

Include a brief comment block in `explainer.py` documenting this ethical design intent.

---

## NOTES

- CORS should be configured to allow `http://localhost:5173` (Vite default)
- The triage threshold (minimum score to pass to OpenAI) should be a configurable constant, default 40
- Do not hardcode the OpenAI API key anywhere — `.env` only
- README should include setup instructions for both backend and frontend