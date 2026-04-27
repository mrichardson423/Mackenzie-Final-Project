import type { AIAnalysis } from "../api";

interface Props {
  analysis: AIAnalysis | null;
  error: string | null;
}

// Renders the 7-field structured AI analysis. Each section is labeled so
// the analyst can see exactly what reasoning the model produced.
export default function AIAnalysisPanel({ analysis, error }: Props) {
  if (error) {
    return (
      <div className="ai-panel">
        <h4>AI analysis unavailable</h4>
        <p>{error}</p>
      </div>
    );
  }

  if (!analysis) return null;

  return (
    <div className="ai-panel">
      {analysis.summary && (
        <>
          <h4>Summary</h4>
          <p>{analysis.summary}</p>
        </>
      )}

      {analysis.triggered_fields && analysis.triggered_fields.length > 0 && (
        <>
          <h4>Triggered fields</h4>
          <p>{analysis.triggered_fields.join(", ")}</p>
        </>
      )}

      {analysis.reasoning && (
        <>
          <h4>Reasoning</h4>
          <p>{analysis.reasoning}</p>
        </>
      )}

      {analysis.ruled_out && (
        <>
          <h4>Ruled out</h4>
          <p>{analysis.ruled_out}</p>
        </>
      )}

      {analysis.benign_explanations && (
        <>
          <h4>Benign explanations</h4>
          <p>{analysis.benign_explanations}</p>
        </>
      )}

      {(typeof analysis.confidence === "number" || analysis.confidence_reasoning) && (
        <>
          <h4>Confidence</h4>
          {typeof analysis.confidence === "number" && (
            <p><strong>{analysis.confidence}%</strong></p>
          )}
          {analysis.confidence_reasoning && <p>{analysis.confidence_reasoning}</p>}
        </>
      )}

      {analysis.recommended_actions && analysis.recommended_actions.length > 0 && (
        <>
          <h4>Recommended actions</h4>
          <ul>
            {analysis.recommended_actions.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
