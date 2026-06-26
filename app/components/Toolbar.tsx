"use client";
import { useState } from "react";
import { ToolsFloatingBar } from "./ToolsFloatingBar";

export default function Toolbar() {
  const [expanded, setExpanded] = useState(false);
  const [activePanel, setActivePanel] = useState("");

  const tools = [
    { id: "attack", label: "⚡ Attack", color: "#ff3355" },
    { id: "c2", label: "🌐 C2", color: "#00ccff" },
    { id: "zeroday", label: "🔍 Zero-Day", color: "#ffaa00" },
    { id: "darkweb", label: "🕵️ Dark Web", color: "#ff3355" },
    { id: "burpsuite", label: "🛡️ BurpSuite", color: "#ff6600" },
    { id: "agents", label: "🤖 Agents", color: "#00ff88" },
    { id: "playwright", label: "🎭 Browser", color: "#00d4ff" },
    { id: "reports", label: "📋 Reports", color: "#ffcc00" },
    { id: "knowledge", label: "🧠 Graph", color: "#aa66ff" },
  ];

  const handleTool = (id: string) => {
    setActivePanel(activePanel === id ? "" : id);
    setExpanded(true);
  };

  return (
    <div style={{ borderBottom: "1px solid #ffffff10", padding: "4px 0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 4, flexWrap: "wrap" }}>
        <span
          onClick={() => { setExpanded(!expanded); if (expanded) setActivePanel(""); }}
          style={{ cursor: "pointer", color: "#666", fontSize: "0.8em", padding: "2px 4px" }}
        >
          {expanded ? "▼" : "▶"} Tools
        </span>
        {expanded && tools.map(t => (
          <button
            key={t.id}
            onClick={() => handleTool(t.id)}
            style={{
              background: activePanel === t.id ? `${t.color}22` : "transparent",
              border: `1px solid ${activePanel === t.id ? t.color : "transparent"}`,
              color: t.color, padding: "3px 8px", borderRadius: 6,
              cursor: "pointer", fontFamily: "monospace", fontSize: "0.75em",
              fontWeight: activePanel === t.id ? "bold" : "normal",
              transition: "all 0.15s",
            }}
          >
            {t.label}
          </button>
        ))}
        {expanded && (
          <button
            onClick={() => { setExpanded(false); setActivePanel(""); }}
            style={{ color: "#666", background: "none", border: "none", cursor: "pointer", fontSize: "0.7em" }}
          >
            ✕
          </button>
        )}
      </div>
      {activePanel && expanded && (
        <InlinePanel id={activePanel} />
      )}
      <ToolsFloatingBar />
    </div>
  );
}

function InlinePanel({ id }: { id: string }) {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    if (!input.trim() || loading) return;
    setLoading(true);
    setResult(null);

    const endpoints: Record<string, { url: string; body?: object }> = {
      attack: { url: "/api/attack", body: { target: input } },
      c2: { url: `/api/c2-control`, body: { action: "start", port: parseInt(input) || 8080 } },
      zeroday: { url: `/api/zeroday-search?q=${encodeURIComponent(input)}` },
      darkweb: { url: "/api/darkweb-proxy", body: { action: "search", query: input } },
      burpsuite: { url: `/api/burpsuite?action=proxy/history&limit=10` },
      agents: { url: `/api/agents-info` },
      playwright: { url: "/api/playwright-proxy", body: { url: input, action: "navigate" } },
      reports: { url: "/api/reports-gen" },
      knowledge: { url: "/api/knowledge-graph" },
    };

    const cfg = endpoints[id];
    if (!cfg) { setLoading(false); return; }

    try {
      const opts: RequestInit = cfg.body
        ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cfg.body) }
        : {};
      const r = await fetch(cfg.url, opts);
      const d = await r.json();
      setResult(d);
    } catch (e: any) {
      setResult({ error: e.message });
    }
    setLoading(false);
  };

  const colors: Record<string, string> = {
    attack: "#ff3355", c2: "#00ccff", zeroday: "#ffaa00", darkweb: "#ff3355",
    burpsuite: "#ff6600", agents: "#00ff88", playwright: "#00d4ff",
    reports: "#ffcc00", knowledge: "#aa66ff",
  };

  return (
    <div style={{
      marginTop: 6, background: "#0d1117", border: `1px solid ${(colors[id] || "#333")}44`,
      borderRadius: 8, padding: 10, fontSize: "0.78em", fontFamily: "monospace",
    }}>
      {id !== "reports" && id !== "agents" && id !== "knowledge" && (
        <div style={{ display: "flex", gap: 6, marginBottom: 8 }}>
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && run()}
            placeholder={id === "attack" ? "Target IP/domain" : id === "c2" ? "Port" : "URL or query"}
            disabled={loading}
            style={{
              flex: 1, padding: "6px 10px", background: "#12121a", border: "1px solid #2a2a3e",
              borderRadius: 6, color: "#e0e0e0", fontFamily: "monospace",
            }}
          />
          <button
            onClick={run}
            disabled={loading}
            style={{
              padding: "6px 14px", background: loading ? "#333" : (colors[id] || "#333"),
              color: "#fff", border: "none", borderRadius: 6, cursor: "pointer", fontWeight: "bold",
            }}
          >
            {loading ? "..." : "Run"}
          </button>
        </div>
      )}
      {result && (
        <pre style={{ color: "#aaa", whiteSpace: "pre-wrap", maxHeight: 200, overflowY: "auto", margin: 0 }}>
          {JSON.stringify(result, null, 2).substring(0, 2000)}
        </pre>
      )}
      {!result && !loading && (
        <div style={{ color: "#444" }}>
          {id === "reports" ? "Click Run to load reports" :
           id === "agents" ? "Click Run to load agent status" :
           id === "knowledge" ? "Click Run to view knowledge graph" :
           `Enter details and click Run`}
        </div>
      )}
    </div>
  );
}
