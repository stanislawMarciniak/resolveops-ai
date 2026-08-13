import { useEffect, useState } from "react";
import "./index.css";

interface HealthResponse {
  status: string;
  service: string;
}

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        return response.json() as Promise<HealthResponse>;
      })
      .then(setHealth)
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : "Unknown error");
      });
  }, []);

  return (
    <main className="page">
      <section className="card">
        <span className="eyebrow">ResolveOps AI</span>

        <h1>Enterprise Case Resolution</h1>

        <p>
          Production-oriented agentic workflow for investigating and resolving
          enterprise support cases.
        </p>

        <div className="status">
          <span className={`dot ${health?.status === "ok" ? "online" : ""}`} />

          {health && <span>Backend connected — {health.service}</span>}

          {!health && !error && <span>Connecting...</span>}

          {error && <span>Backend unavailable — {error}</span>}
        </div>
      </section>
    </main>
  );
}

export default App;
