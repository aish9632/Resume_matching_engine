import { useState } from "react";
import "./index.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [candidateId, setCandidateId] = useState("C_RANK_000002");
  const [jobId, setJobId] = useState("J_JSS_000833");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const analyzeMatch = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/matches`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          candidate_id: candidateId,
          job_id: jobId,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Matching failed");
      }

      setResult(data);
    } catch (err) {
      setError(
        `${err.message}. Make sure the FastAPI backend is running on port 8000.`
      );
    } finally {
      setLoading(false);
    }
  };

  const percentage = (value) =>
    `${Math.round(Number(value || 0) * 100)}%`;

  return (
    <div className="app">
      <header className="header">
        <div>
          <p className="eyebrow">THE MATCHING PROBLEM</p>
          <h1>Explainable Resume–Job Matching Engine</h1>
          <p className="subtitle">
            Evidence-aware hybrid matching that explains why a candidate fits
            a job instead of relying on keyword similarity alone.
          </p>
        </div>

        <div className="status">
          <span className="status-dot"></span>
          API Ready
        </div>
      </header>

      <main>
        <section className="input-card">
          <div className="field">
            <label>Candidate ID</label>
            <input
              value={candidateId}
              onChange={(e) => setCandidateId(e.target.value)}
              placeholder="C_RANK_000002"
            />
          </div>

          <div className="field">
            <label>Job ID</label>
            <input
              value={jobId}
              onChange={(e) => setJobId(e.target.value)}
              placeholder="J_JSS_000833"
            />
          </div>

          <button onClick={analyzeMatch} disabled={loading}>
            {loading ? "Analyzing..." : "Analyze Match"}
          </button>
        </section>

        {error && <div className="error">{error}</div>}

        {result && (
          <>
            <section className="job-card">
              <div>
                <span className="label">JOB</span>
                <h2>{result.job_title}</h2>
              </div>
              <div className="recommendation">
                {result.recommendation}
              </div>
            </section>

            <section className="metrics">
              <div className="metric-card">
                <span>Decision Fit</span>
                <strong>{result.fit_score}/100</strong>
              </div>

              <div className="metric-card">
                <span>Raw Fit</span>
                <strong>{result.fit_score_before_guardrails}/100</strong>
              </div>

              <div className="metric-card">
                <span>Confidence</span>
                <strong>{percentage(result.confidence)}</strong>
              </div>

              <div className="metric-card">
                <span>Evidence Coverage</span>
                <strong>{percentage(result.evidence_coverage)}</strong>
              </div>
            </section>

            <section className="explanation-card">
              <div className="section-title">
                <h2>Why this decision?</h2>
              </div>

              <p>{result.explanation?.summary}</p>

              {result.critical_gaps?.length > 0 && (
                <div className="critical">
                  <strong>Critical Gap</strong>

                  {result.critical_gaps.map((gap, index) => (
                    <div key={index}>
                      <b>{gap.requirement}</b>
                      <span>{gap.explanation}</span>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section className="two-column">
              <MatchSection
                title="Strong Matches"
                items={result.strong_matches}
                type="strong"
              />

              <MatchSection
                title="Partial / Transferable"
                items={result.partial_matches}
                type="partial"
              />
            </section>

            <section className="explanation-card">
              <div className="section-title">
                <h2>Missing Requirements</h2>
                <span>{result.missing_requirements?.length || 0}</span>
              </div>

              <div className="missing-list">
                {result.missing_requirements?.map((item, index) => (
                  <div className="missing-item" key={index}>
                    <div>
                      <b>{item.requirement}</b>
                      <span>{item.relationship}</span>
                    </div>
                    <small>
                      Requirement not supported by resume evidence
                    </small>
                  </div>
                ))}
              </div>
            </section>

            <section className="method-card">
              <h2>How the engine reasons</h2>

              <div className="method-grid">
                <div>
                  <b>01</b>
                  <span>Extract requirements</span>
                </div>

                <div>
                  <b>02</b>
                  <span>Find resume evidence</span>
                </div>

                <div>
                  <b>03</b>
                  <span>Classify relationships</span>
                </div>

                <div>
                  <b>04</b>
                  <span>Apply scoring & guardrails</span>
                </div>

                <div>
                  <b>05</b>
                  <span>Generate grounded explanation</span>
                </div>
              </div>
            </section>
          </>
        )}
      </main>

      <footer>
        Explainable Resume–Job Matching Engine • Hybrid semantic + evidence-aware
        architecture
      </footer>
    </div>
  );
}

function MatchSection({ title, items = [], type }) {
  return (
    <section className="explanation-card">
      <div className="section-title">
        <h2>{title}</h2>
        <span>{items.length}</span>
      </div>

      <div className="match-list">
        {items.map((item, index) => (
          <div className={`match-item ${type}`} key={index}>
            <div className="match-top">
              <b>{item.requirement}</b>
              <span>{item.relationship}</span>
            </div>

            <div className="score">
              Score: {Number(item.final_requirement_score || 0).toFixed(2)}
            </div>

            <p>{item.explanation}</p>

            {item.evidence_ids?.length > 0 && (
              <small>
                Evidence: {item.evidence_ids.join(", ")}
              </small>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

export default App;
