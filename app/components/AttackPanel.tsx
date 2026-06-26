"use client";
import { useState } from "react";

export default function AttackPanel() {
  const [target, setTarget] = useState("");
  const [running, setRunning] = useState(false);
  const [phases, setPhases] = useState<any[]>([]);
  const [collapsed, setCollapsed] = useState(true);

  const startAttack = async () => {
    if (!target.trim() || running) return;
    setRunning(true);
    setPhases([]);
    setCollapsed(false);

    try {
      const res = await fetch("/api/attack", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target: target.trim() }),
      });
      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        for (const line of text.split("\n")) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              setPhases(prev => [...prev, data]);
            } catch {}
          }
        }
      }
    } catch (e) {
      setPhases(prev => [...prev, { phase: "error", message: String(e) }]);
    }
    setRunning(false);
  };

  const statusIcon = (p: any) => {
    if (p.status === "complete" || p.phase === "done") return "✅";
    if (p.status === "running") return "🔄";
    return "⏳";
  };

  return (
    <div style={{ margin: "0 0 12px 0", borderTop: "1px solid #ffffff10", paddingTop: 8 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }} onClick={() => !running && setCollapsed(!collapsed)}>
        <span style={{ cursor: "pointer", fontSize: "0.8em" }}>{collapsed ? "▶" : "▼"}</span>
        <span style={{ color: "#ff3355", fontSize: "0.85em", fontWeight: 600 }}>⚡ Attack Cycle</span>
        {running && <span style={{ color: "#ffcc00", fontSize: "0.75em" }}>Running...</span>}
        {phases.some(p => p.winner) && (
          <span style={{ color: "#aa66ff", fontSize: "0.75em", marginLeft: 8 }}>
            Active Module: {phases.findLast(p => p.winner)?.winner}
          </span>
        )}
      </div>

      {!collapsed && (
        <div style={{ marginTop: 8 }}>
          <div style={{ display: "flex", gap: 8, marginBottom: 8 }}>
            <input
              value={target}
              onChange={e => setTarget(e.target.value)}
              onKeyDown={e => e.key === "Enter" && startAttack()}
              placeholder="Target IP or domain..."
              disabled={running}
              style={{
                flex: 1, padding: "8px 12px", background: "#12121a", border: "1px solid #ff335544",
                borderRadius: 8, color: "#e0e0e0", fontFamily: "monospace", fontSize: "0.85em"
              }}
            />
            <button
              onClick={startAttack}
              disabled={running || !target.trim()}
              style={{
                padding: "8px 16px", background: running ? "#333" : "#ff3355", color: "#fff",
                border: "none", borderRadius: 8, cursor: running ? "default" : "pointer",
                fontFamily: "monospace", fontWeight: "bold", fontSize: "0.85em", whiteSpace: "nowrap"
              }}
            >
              {running ? "⚡ Running..." : "⚡ Attack"}
            </button>
          </div>

          {phases.length > 0 && (
            <div style={{
              background: "#0d1117", border: "1px solid #2a2a3e", borderRadius: 8,
              padding: 10, maxHeight: 400, overflowY: "auto", fontFamily: "monospace", fontSize: "0.75em"
            }}>
              {phases.map((p, i) => (
                <div key={i} style={{
                  padding: "4px 6px", borderBottom: "1px solid #ffffff08",
                  color: p.phase === "done" ? "#00ff88" : p.status === "complete" ? "#00d4ff" :
                         p.status === "running" ? "#ffcc00" : "#888",
                  fontWeight: p.phase === "done" ? "bold" : "normal"
                }}>
                  {statusIcon(p)} {p.message}
                  {p.ports && <span style={{ color: "#fff", fontSize: "0.8em" }}> [{p.ports.join(", ")}]</span>}
                  {p.winner && <span style={{ color: "#aa66ff" }}> [{p.winner}]</span>}
                  {p.reportPath && (
                    <a href={p.reportPath} style={{ color: "#00d4ff", marginLeft: 8, fontSize: "0.8em" }}>
                      📥 Download Report
                    </a>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
