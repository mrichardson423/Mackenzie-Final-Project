import type { TriageResult } from "../api";
import AIAnalysisPanel from "./AIAnalysisPanel";

interface Props {
  result: TriageResult;
}

// One card per flagged log entry.
// Shows: risk badge + score, AI summary line, triggered rule tags,
// expandable AI analysis, and a collapsible raw-log block.
export default function ResultCard({ result }: Props) {
  const { score, risk_level, triggered_rules, log_entry, ai_analysis, ai_error } = result;

  return (
    <div className="result-card">
      <div className="header">
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", gap: 2 }}>
          <span className={`badge ${risk_level}`}>{risk_level}</span>
          {typeof ai_analysis?.confidence === "number" && (
            <span style={{ fontSize: 11, color: "#000000", marginTop: 2 }}>
              AI confidence: {ai_analysis.confidence}%
            </span>
          )}
        </div>
        <span className="score">Score: {score}/100</span>
        {log_entry.event_type ? (
          <span className="score" style={{ color: "#000000" }}>
            {String(log_entry.event_type)} · {String(log_entry.user ?? "—")} · {String(log_entry.source_ip ?? "—")}
          </span>
        ) : null}
      </div>

      {ai_analysis?.summary && <p className="summary">{ai_analysis.summary}</p>}

      <div style={{ marginTop: 10 }}>
        <div style={{
          fontSize: 12,
          fontWeight: 600,
          color: "#000000",
          textTransform: "uppercase",
          letterSpacing: 0.5,
          marginBottom: 6,
        }}>
          Score Breakdown
        </div>
        <div className="tags">
          {triggered_rules.map((rule, i) => (
            <span key={i} className="tag">{rule}</span>
          ))}
        </div>
      </div>

      <details>
        <summary>AI analysis</summary>
        <AIAnalysisPanel analysis={ai_analysis} error={ai_error} />
      </details>

      <details>
        <summary>Raw log entry</summary>
        <pre className="raw">{JSON.stringify(log_entry.raw ?? log_entry, null, 2)}</pre>
      </details>
    </div>
  );
}
