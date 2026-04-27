"""
Log parser. Accepts JSON (array of objects) or CSV files and normalizes
each entry into a consistent internal dict schema so the triage engine
can apply rules without worrying about input format differences.
"""

import io
import json
import pandas as pd

# Canonical fields we try to populate on every log entry.
CANONICAL_FIELDS = [
    "timestamp",
    "source_ip",
    "dest_ip",
    "event_type",
    "user",
    "status_code",
    "action",
    "resource",
]


def normalize_entry(entry: dict) -> dict:
    """Return a dict with all canonical fields plus the raw original entry."""
    normalized = {field: entry.get(field) for field in CANONICAL_FIELDS}
    normalized["raw"] = entry
    return normalized


def parse_json(content: bytes) -> list[dict]:
    data = json.loads(content.decode("utf-8"))
    # Allow either a list of objects or a single object.
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("JSON file must be an array of log objects or a single object.")
    return [normalize_entry(item) for item in data]


def parse_csv(content: bytes) -> list[dict]:
    # Use pandas for robust CSV handling (quotes, mixed types, etc).
    df = pd.read_csv(io.BytesIO(content))
    # Convert NaN to None so JSON serialization stays clean.
    df = df.where(pd.notnull(df), None)
    records = df.to_dict(orient="records")
    return [normalize_entry(rec) for rec in records]


def parse_log_file(filename: str, content: bytes) -> list[dict]:
    """Dispatch based on filename extension."""
    name = filename.lower()
    if name.endswith(".json"):
        return parse_json(content)
    if name.endswith(".csv"):
        return parse_csv(content)
    raise ValueError("Unsupported file type. Use .json or .csv.")
