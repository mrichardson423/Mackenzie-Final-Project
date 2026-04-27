"""
Rule-based triage engine. Each rule is a small function that inspects a
single log entry (and optionally aggregate context like per-IP counts)
and returns a (label, weight) tuple if it fires, else None.

Scores are clamped to 0-100. Risk levels map from the final score.
Every rule that fires is recorded so the analyst can trace the score
back to specific evidence — this is core to the transparency goal.
"""

from collections import Counter
from datetime import datetime

# Event types we treat as inherently suspicious.
SUSPICIOUS_EVENT_TYPES = {
    "AUTH_FAIL": 25,
    "EXEC": 30,
    "DELETE": 20,
    "PRIV_ESC": 40,
    "MALWARE": 45,
    "BRUTE_FORCE": 40,
}

# Path fragments we treat as sensitive.
SENSITIVE_PATH_FRAGMENTS = [
    "/admin",
    "/etc/passwd",
    "/etc/shadow",
    "/root",
    "/.ssh",
    "/wp-admin",
    "/config",
    "/secret",
]

# Threshold for "high volume from single IP" rule.
HIGH_VOLUME_REQUEST_THRESHOLD = 20

# Map score -> risk label.
def risk_level_for(score: int) -> str:
    if score >= 80:
        return "CRITICAL"
    if score >= 60:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    return "LOW"


def _parse_hour(timestamp) -> int | None:
    """Best-effort parse of an hour value from a timestamp string."""
    if not timestamp:
        return None
    try:
        # Handle trailing Z (UTC).
        ts = str(timestamp).replace("Z", "+00:00")
        return datetime.fromisoformat(ts).hour
    except (ValueError, TypeError):
        return None


def build_context(entries: list[dict]) -> dict:
    """Aggregate context across all entries (e.g. per-IP request counts)."""
    ip_counts = Counter()
    fail_counts_by_user = Counter()
    for entry in entries:
        ip = entry.get("source_ip")
        if ip:
            ip_counts[ip] += 1
        if entry.get("event_type") == "AUTH_FAIL" and entry.get("user"):
            fail_counts_by_user[entry["user"]] += 1
    return {
        "ip_counts": ip_counts,
        "fail_counts_by_user": fail_counts_by_user,
    }


def evaluate_entry(entry: dict, context: dict) -> tuple[int, list[str]]:
    """Run all rules against one entry. Return (score, list_of_rule_labels)."""
    triggered: list[str] = []
    score = 0

    event_type = (entry.get("event_type") or "").upper()
    user = entry.get("user")
    source_ip = entry.get("source_ip")
    status_code = entry.get("status_code")
    resource = (entry.get("resource") or "").lower()
    action = (entry.get("action") or "").upper()

    # Rule: known-bad event types.
    if event_type in SUSPICIOUS_EVENT_TYPES:
        weight = SUSPICIOUS_EVENT_TYPES[event_type]
        triggered.append(f"suspicious_event_type:{event_type} (+{weight})")
        score += weight

    # Rule: repeated auth failures by same user (>= 3 across the file).
    if event_type == "AUTH_FAIL" and user:
        fails = context["fail_counts_by_user"].get(user, 0)
        if fails >= 3:
            weight = 20
            triggered.append(f"repeated_auth_failures:{user}={fails} (+{weight})")
            score += weight

    # Rule: privilege escalation hints in action field.
    if "SUDO" in action or "PRIV" in action or "ESCALATE" in action:
        weight = 30
        triggered.append(f"privilege_escalation_action:{action} (+{weight})")
        score += weight

    # Rule: unusual access hours (2-5 AM local to the timestamp).
    hour = _parse_hour(entry.get("timestamp"))
    if hour is not None and 2 <= hour <= 5:
        weight = 10
        triggered.append(f"unusual_hour:{hour:02d}:00 (+{weight})")
        score += weight

    # Rule: access to sensitive resource paths.
    for fragment in SENSITIVE_PATH_FRAGMENTS:
        if fragment in resource:
            weight = 20
            triggered.append(f"sensitive_resource:{fragment} (+{weight})")
            score += weight
            break  # don't double-count overlapping fragments

    # Rule: unauthorized / forbidden HTTP responses.
    if status_code in (401, 403):
        weight = 10
        triggered.append(f"http_denied:{status_code} (+{weight})")
        score += weight

    # Rule: high-volume requests from a single IP across the file.
    if source_ip:
        count = context["ip_counts"].get(source_ip, 0)
        if count >= HIGH_VOLUME_REQUEST_THRESHOLD:
            weight = 15
            triggered.append(f"high_volume_ip:{source_ip}={count} (+{weight})")
            score += weight

    # Clamp.
    if score > 100:
        score = 100

    return score, triggered


def triage_entries(entries: list[dict]) -> list[dict]:
    """Score every entry. Returns a list of triage result dicts."""
    context = build_context(entries)
    results = []
    for entry in entries:
        score, triggered = evaluate_entry(entry, context)
        results.append({
            "score": score,
            "risk_level": risk_level_for(score),
            "triggered_rules": triggered,
            "log_entry": entry,
        })
    return results
