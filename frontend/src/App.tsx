import { useEffect, useState } from "react";
import { getHealth, type Health } from "./api/client";

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch((e) => setError(String(e)));
  }, []);

  return (
    <main style={{ fontFamily: "sans-serif", maxWidth: 560, margin: "40px auto" }}>
      <h2>ShopEasy Support Bot</h2>
      {error && <p style={{ color: "crimson" }}>Backend unreachable: {error}</p>}
      {!health && !error && <p>Checking backend…</p>}
      {health && (
        <ul>
          <li>API: {health.status}</li>
          <li>Database: {health.db}</li>
          <li>pgvector: {health.pgvector ? "enabled" : "missing"}</li>
        </ul>
      )}
    </main>
  );
}