"""
FastAPI entrypoint for the AI-powered log triage tool.

Flow for POST /upload:
  1. Read the uploaded file (JSON or CSV).
  2. Parse + normalize entries.
  3. Score every entry using the rule-based triage engine.
  4. For entries above TRIAGE_THRESHOLD, ask OpenAI for a structured
     plain-language explanation.
  5. Return the enriched results to the frontend.
"""

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from parser import parse_log_file
from triage import triage_entries
from explainer import explain_entry

# Minimum score required for an entry to be sent to OpenAI for explanation.
# Anything below this is considered routine / not worth analyst time.
TRIAGE_THRESHOLD = 25

app = FastAPI(title="AI Security Log Triage")

# Allow the local Vite dev server.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "threshold": TRIAGE_THRESHOLD}


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Parse + normalize.
    try:
        entries = parse_log_file(file.filename or "", content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse log file: {exc}")

    # Score every entry.
    triaged = triage_entries(entries)

    # Filter to entries we care about, then ask OpenAI to explain each.
    # Sort highest-risk first so the analyst sees the most urgent items at the top.
    flagged = sorted(
        [t for t in triaged if t["score"] >= TRIAGE_THRESHOLD],
        key=lambda t: t["score"],
        reverse=True,
    )

    enriched = []
    for result in flagged:
        try:
            ai_analysis = explain_entry(result)
            error = None
        except Exception as exc:
            # If OpenAI fails for any reason (rate limit, key missing, etc),
            # we still return the rule-based score so the analyst sees
            # *something* — transparency over silent failure.
            ai_analysis = None
            error = str(exc)

        enriched.append({
            **result,
            "ai_analysis": ai_analysis,
            "ai_error": error,
        })

    return {
        "threshold": TRIAGE_THRESHOLD,
        "total_entries": len(triaged),
        "flagged_count": len(flagged),
        "results": enriched,
    }
