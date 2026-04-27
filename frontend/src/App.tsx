import { useState } from "react";
import UploadPanel from "./components/UploadPanel";
import ResultCard from "./components/ResultCard";
import { uploadLogFile, type UploadResponse } from "./api";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<UploadResponse | null>(null);

  async function handleAnalyze(file: File) {
    setLoading(true);
    setError(null);
    setResponse(null);
    try {
      const data = await uploadLogFile(file);
      setResponse(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app">
      <h1>Triage Assistant</h1>
      <p className="subtitle">
        Upload a log file. Rule-based scoring runs first; flagged entries are
        then explained by an AI assistant for human review.
      </p>

      <UploadPanel onAnalyze={handleAnalyze} disabled={loading} />

      {loading && (
        <div className="status">
          <span className="spinner" />
          Scoring entries and requesting AI analysis…
        </div>
      )}

      {error && <div className="status error">Error: {error}</div>}

      {response && !loading && (
        <>
          <div className="status">
            Processed <strong>{response.total_entries}</strong> entries.
            {" "}<strong>{response.flagged_count}</strong> exceeded the threshold
            of {response.threshold}.
          </div>

          {response.flagged_count === 0 ? (
            <div className="no-results">
              No entries exceeded the triage threshold. Nothing requires analyst review.
            </div>
          ) : (
            <div className="results">
              {response.results.map((r, i) => (
                <ResultCard key={i} result={r} />
              ))}
            </div>
          )}
        </>
      )}

      <p className="ethics-note">
        This tool is advisory. AI-generated analysis is intended to support — not
        replace — a human analyst's judgment. Every score is traceable to specific
        rules, and benign explanations are surfaced alongside risks to avoid
        anchoring the analyst to a single interpretation.
      </p>
    </div>
  );
}
