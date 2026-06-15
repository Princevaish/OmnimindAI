// RagDebugPanel.jsx — RAG diagnostic panel for development
import { useState } from "react";

const API = "http://localhost:8000/api/v1";

function Section({ title, children }) {
  return (
    <div className="mb-4">
      <p className="text-xs font-semibold uppercase tracking-widest mb-2"
         style={{ color: "#52525b" }}>{title}</p>
      {children}
    </div>
  );
}

function StatRow({ label, value, highlight }) {
  return (
    <div className="flex items-center justify-between py-1.5 border-b"
         style={{ borderColor: "#1f1f23" }}>
      <span className="text-xs" style={{ color: "#71717a" }}>{label}</span>
      <span className="text-xs font-medium tabular-nums"
            style={{ color: highlight ? "#8b5cf6" : "#e4e4e7" }}>
        {value ?? "—"}
      </span>
    </div>
  );
}

export default function RagDebugPanel() {
  const [stats,     setStats]     = useState(null);
  const [query,     setQuery]     = useState("");
  const [results,   setResults]   = useState(null);
  const [loading,   setLoading]   = useState(false);
  const [error,     setError]     = useState("");

  const fetchStats = async () => {
    setLoading(true); setError("");
    try {
      const res = await fetch(`${API}/debug/rag/stats`);
      setStats(await res.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  const runRetrieval = async () => {
    if (!query.trim()) return;
    setLoading(true); setError(""); setResults(null);
    try {
      const res = await fetch(
        `${API}/debug/rag/retrieve?q=${encodeURIComponent(query)}&k=4`
      );
      setResults(await res.json());
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  };

  return (
    <div
      className="flex flex-col gap-4 p-4 rounded-2xl overflow-y-auto"
      style={{ backgroundColor: "#0f0f11", border: "1px solid #1f1f23",
               maxHeight: "90vh", minWidth: "340px" }}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold" style={{ color: "#f4f4f5" }}>
          RAG Debug Panel
        </h3>
        <span className="text-xs px-2 py-0.5 rounded-full"
              style={{ backgroundColor: "#1a1a1d", color: "#52525b" }}>
          Dev Only
        </span>
      </div>

      {/* Vector store stats */}
      <Section title="Vector Store">
        <button
          onClick={fetchStats}
          disabled={loading}
          className="w-full py-2 rounded-xl text-xs font-medium mb-3 disabled:opacity-50"
          style={{ backgroundColor: "#1a1a1d", border: "1px solid #27272a",
                   color: "#a1a1aa" }}
        >
          {loading ? "Loading…" : "Refresh Stats"}
        </button>

        {stats && !stats.error && (
          <div className="rounded-xl overflow-hidden"
               style={{ border: "1px solid #1f1f23" }}>
            <StatRow label="Collection"      value={stats.collection_name} />
            <StatRow label="Documents"       value={stats.document_count} highlight />
            <StatRow label="Persist Dir"     value={stats.persist_dir} />
          </div>
        )}
        {stats?.error && (
          <p className="text-xs p-2 rounded-lg"
             style={{ backgroundColor: "#1a0000", color: "#ef4444" }}>
            {stats.error}
          </p>
        )}

        {/* Sample docs */}
        {stats?.sample_docs?.length > 0 && (
          <div className="mt-3">
            <p className="text-xs mb-1" style={{ color: "#52525b" }}>Stored chunks (sample):</p>
            {stats.sample_docs.map((d, i) => (
              <div key={i} className="mb-2 p-2 rounded-lg"
                   style={{ backgroundColor: "#141417", border: "1px solid #1f1f23" }}>
                <p className="text-xs mb-1" style={{ color: "#71717a" }}>
                  📄 {d.metadata?.source ?? "unknown"}
                </p>
                <p className="text-xs leading-relaxed" style={{ color: "#a1a1aa" }}>
                  {d.preview}
                </p>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Retrieval tester */}
      <Section title="Test Retrieval">
        <div className="flex gap-2 mb-3">
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === "Enter" && runRetrieval()}
            placeholder="Enter test query…"
            className="flex-1 bg-transparent outline-none text-xs px-3 py-2 rounded-xl"
            style={{ border: "1px solid #27272a", color: "#e4e4e7",
                     backgroundColor: "#141417", caretColor: "#8b5cf6" }}
          />
          <button
            onClick={runRetrieval}
            disabled={loading || !query.trim()}
            className="px-3 py-2 rounded-xl text-xs font-medium disabled:opacity-40"
            style={{ backgroundColor: "#8b5cf6", color: "#fff" }}
          >
            Run
          </button>
        </div>

        {results && (
          <div>
            <div className="flex items-center justify-between mb-2">
              <p className="text-xs" style={{ color: "#52525b" }}>
                {results.count} result{results.count !== 1 ? "s" : ""} for{" "}
                <span style={{ color: "#8b5cf6" }}>{results.query}</span>
              </p>
            </div>

            {results.count === 0 && (
              <div className="p-3 rounded-xl"
                   style={{ backgroundColor: "#1a1400", border: "1px solid #f59e0b33" }}>
                <p className="text-xs" style={{ color: "#f59e0b" }}>
                  ⚠ No chunks retrieved. Possible causes:
                </p>
                <ul className="text-xs mt-1 list-disc list-inside"
                    style={{ color: "#a1a1aa" }}>
                  <li>No documents ingested yet</li>
                  <li>Query not semantically similar to stored content</li>
                  <li>Collection name mismatch</li>
                </ul>
              </div>
            )}

            {results.results?.map((r, i) => (
              <div key={i} className="mb-2 p-3 rounded-xl"
                   style={{ backgroundColor: "#141417", border: "1px solid #1f1f23" }}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs" style={{ color: "#71717a" }}>
                    📄 {r.source}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs" style={{ color: "#52525b" }}>
                      dist: {r.score}
                    </span>
                    <span
                      className="text-xs px-1.5 py-0.5 rounded-full tabular-nums"
                      style={{
                        backgroundColor: r.similarity > 0.6 ? "#22c55e18" : "#f59e0b18",
                        color: r.similarity > 0.6 ? "#22c55e" : "#f59e0b",
                      }}
                    >
                      {Math.round(r.similarity * 100)}% match
                    </span>
                  </div>
                </div>
                <p className="text-xs leading-relaxed" style={{ color: "#a1a1aa" }}>
                  {r.preview}
                </p>
              </div>
            ))}
          </div>
        )}
      </Section>

      {error && (
        <p className="text-xs p-2 rounded-lg"
           style={{ backgroundColor: "#1a0000", color: "#ef4444" }}>
          {error}
        </p>
      )}
    </div>
  );
}