"""
OpenAI integration: turns a flagged log entry + its triggered rules into
a structured, plain-language explanation.

ETHICAL DESIGN INTENT
---------------------
This module is the AI surface of the triage tool. It is designed for
TRANSPARENCY and HUMAN OVERSIGHT, not autonomous action:

  1. The model is framed as a senior SOC analyst PROVIDING REASONING,
     not as a decision-maker. The human analyst always retains
     authority over what to do with the alert.
  2. Every score the model sees is already traceable to specific
     fired rules — the model is asked to reason about those rules,
     not to invent new ones.
  3. The model is REQUIRED to surface benign explanations and what it
     ruled out, so the analyst is not anchored to a single (possibly
     wrong) framing.
  4. The model is asked to state its own confidence and the reason for
     that confidence, so the analyst can weight its output accordingly.
  5. Output is a strict JSON schema, which makes the reasoning legible
     to both the UI and to downstream review.

If you change this prompt, preserve those properties.
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Build the client once at import time. If the key is missing we still
# import successfully — main.py will surface a clear error at request time.
_api_key = os.getenv("OPENAI_API_KEY")
_client = OpenAI(api_key=_api_key) if _api_key else None

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

SYSTEM_PROMPT = """You are a senior Security Operations Center (SOC) analyst.
You review pre-scored security log entries and produce structured analysis
for a junior analyst to act on.

Important constraints:
- You are advisory, not authoritative. A human analyst makes the final call.
- Be transparent: explain your reasoning, including what you ruled out.
- Always offer plausible benign explanations if any exist, so the human
  analyst is not anchored to a single framing.
- State your confidence and why.
- Respond ONLY with a single JSON object matching the requested schema.
"""

# We ask the model to fill in exactly these fields. Listed in the prompt so
# the schema is reproducible if the response_format hint is dropped.
RESPONSE_SCHEMA_FIELDS = [
    "summary",
    "triggered_fields",
    "reasoning",
    "ruled_out",
    "benign_explanations",
    "confidence",
    "confidence_reasoning",
    "recommended_actions",
]


def _build_user_prompt(triage_result: dict) -> str:
    log_entry = triage_result["log_entry"]
    return f"""Analyze the following security log entry.

Raw log entry (normalized):
{json.dumps(log_entry, indent=2, default=str)}

Pre-computed triage:
- Risk score: {triage_result['score']} / 100
- Risk level: {triage_result['risk_level']}
- Triggered rules (label and weight):
{json.dumps(triage_result['triggered_rules'], indent=2)}

Respond with a JSON object containing exactly these fields:
- summary: One-sentence summary of what happened.
- triggered_fields: Array of log field names that drove this score
  (e.g. ["event_type", "resource", "timestamp"]).
- reasoning: Why this entry was scored the way it was, in plain language.
- ruled_out: What alternative interpretations you considered and dismissed,
  and why.
- benign_explanations: Plausible innocent explanations for this entry.
  If genuinely none, say so explicitly.
- confidence: Integer 0-100 representing your confidence (as a percentage)
  that this entry represents genuine malicious or anomalous activity
  (NOT your confidence in the rule score). 100 = certain malicious,
  0 = certain benign, 50 = genuinely ambiguous.
- confidence_reasoning: Why your confidence percentage is what it is.
- recommended_actions: Array of concrete next steps for the human analyst.
"""


def explain_entry(triage_result: dict) -> dict:
    """Call OpenAI for one flagged entry and return parsed JSON analysis."""
    if _client is None:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Add it to backend/.env before uploading logs."
        )

    response = _client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(triage_result)},
        ],
    )

    raw = response.choices[0].message.content or "{}"
    parsed = json.loads(raw)

    # Ensure every expected field is present, even if the model omitted one.
    for field in RESPONSE_SCHEMA_FIELDS:
        parsed.setdefault(field, None)
    return parsed
