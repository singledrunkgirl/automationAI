"use client";

import { useState, useEffect } from "react";

const API = (path: string) => `/api${path}`;

async function call(path: string, opts?: RequestInit) {
  const r = await fetch(API(path), opts);
  return r.json();
}

export default function ControlPanel() {
  const [status, setStatus] = useState<any>(null);
  const [agents, setAgents] = useState<any[]>([]);
  const [c2Status, setC2Status] = useState<any>(null);
  const [zeroday, setZeroday] = useState<any[]>([]);
  const [kgStats, setKgStats] = useState<any>(null);
  const [darkweb, setDarkweb] = useState<any>(null);
  const [logs, setLogs] = useState<string[]>([]);
  const [target, setTarget] = useState("scanme.nmap.org");
  const [c2Port, setC2Port] = useState(8080);
  const [cveQuery, setCveQuery] = useState("");

  const addLog = (msg: string) => setLogs(l => [...l.slice(-99), `[${new Date().toLocaleTimeString()}] ${msg}`]);

  useEffect(() => {
    call("/status").then(setStatus);
    call("/agents-info").then(d => setAgents(d.agents || []));
    call("/knowledge-graph").then(setKgStats);
    call("/darkweb-proxy").then(setDarkweb);
  }, []);

  const startDebate = async () => {
    addLog(`🎯 Starting debate on: ${target}`);
    const r = await call("/agents-info", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target }) });
    addLog(`✅ Winner: ${r.winner} (${Math.round((r.consensus||0)*100)}%)`);
  };

  const startC2 = async () => {
    addLog(`🌐 Starting C2 on port ${c2Port}`);
    await call("/c2-control", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "start", port: c2Port }) });
    const s = await call("/c2-control");
    setC2Status(s);
    addLog(`✅ C2 listener active`);
  };

  const searchCVE = async () => {
    if (!cveQuery) return;
    addLog(`🔍 Searching: ${cveQuery}`);
    const r = await call(`/zeroday-search?q=${encodeURIComponent(cveQuery)}`);
    setZeroday(r || []);
    addLog(`✅ Found ${r.length} CVEs`);
  };

  return (
    <div style={{ background: "#0a0a0a", color: "#00ff88", minHeight: "100vh", fontFamily: "monospace", padding: 20 }}>
      <div style={{ textAlign: "center", marginBottom: 30 }}>
        <h1 style={{ color: "#00ff88", fontSize: "2em" }}>⚡ HackWithAI v2 — Control Panel</h1>
        <p style={{ color: "#888" }}>{status ? `Tools: ${status.tools_total} | Reports: ${status.reports} | Uptime: ${Math.round(status.uptime||0)}s` : "Loading..."}</p>
      </div>

      {/* Navigation Bar */}
      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 8, marginBottom: 20 }}>
        {[
          { label: "🏠 Chat", href: "/", color: "#00ff88" },
          { label: "🤖 Agents", href: "/agents", color: "#00ff88" },
          { label: "🌐 C2", href: "/c2", color: "#00ccff" },
          { label: "🔍 Zero-Day", href: "/zeroday", color: "#ffaa00" },
          { label: "🧠 Knowledge", href: "/knowledge", color: "#aa66ff" },
          { label: "🕵️ Dark Web", href: "/darkweb", color: "#ff3355" },
          { label: "🎭 Playwright", href: "/playwright", color: "#00d4ff" },
          { label: "📋 Reports", href: "/reports", color: "#ffcc00" },
          { label: "🛡️ BurpSuite", href: "/burpsuite", color: "#ff6600" },
        ].map((link, i) => (
          <a key={i} href={link.href} style={{
            background: "#1a1a2e", border: `1px solid ${link.color}44`,
            color: link.color, padding: "8px 14px", borderRadius: 8,
            textDecoration: "none", fontFamily: "monospace", fontSize: "0.85em",
            fontWeight: "bold", transition: "all 0.2s",
          }}>{link.label}</a>
        ))}
      </div>

      {/* Status Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px,1fr))", gap: 15, marginBottom: 30 }}>
        {[
          { label: "Agents Online", value: "5/5", color: "#00ff88" },
          { label: "Tools Available", value: status?.tools_total || "—", color: "#00ccff" },
          { label: "CVE Database", value: status?.cve_db ? "Active" : "Idle", color: "#ffaa00" },
          { label: "Knowledge Graph", value: kgStats ? `${kgStats.total_nodes} nodes` : "—", color: "#ff66aa" },
          { label: "Tor", value: darkweb?.tor_running ? "Running" : "Stopped", color: darkweb?.tor_running ? "#00ff88" : "#ff4444" },
          { label: "Reports", value: status?.reports || 0, color: "#aa88ff" },
        ].map((card, i) => (
          <div key={i} style={{ background: "#111", border: `1px solid ${card.color}33`, borderRadius: 12, padding: 20, textAlign: "center" }}>
            <div style={{ color: "#666", fontSize: "0.8em", marginBottom: 8 }}>{card.label}</div>
            <div style={{ color: card.color, fontSize: "1.8em", fontWeight: "bold" }}>{card.value}</div>
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px,1fr))", gap: 15, marginBottom: 30 }}>
        {/* Debate */}
        <div style={{ background: "#111", border: "1px solid #333", borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: "#00ff88" }}>🗣️ Debate Engine</h3>
          <input value={target} onChange={e => setTarget(e.target.value)} style={{ width: "100%", padding: 10, background: "#222", color: "#fff", border: "1px solid #444", borderRadius: 8, marginBottom: 10, fontFamily: "monospace" }} placeholder="Target" />
          <button onClick={startDebate} style={{ width: "100%", padding: 12, background: "#00ff8822", color: "#00ff88", border: "1px solid #00ff88", borderRadius: 8, cursor: "pointer", fontFamily: "monospace", fontWeight: "bold" }}>Start Debate</button>
        </div>

        {/* C2 */}
        <div style={{ background: "#111", border: "1px solid #333", borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: "#00ccff" }}>🌐 C2 Control</h3>
          <input type="number" value={c2Port} onChange={e => setC2Port(+e.target.value)} style={{ width: "100%", padding: 10, background: "#222", color: "#fff", border: "1px solid #444", borderRadius: 8, marginBottom: 10, fontFamily: "monospace" }} placeholder="Port" />
          <button onClick={startC2} style={{ width: "100%", padding: 12, background: "#00ccff22", color: "#00ccff", border: "1px solid #00ccff", borderRadius: 8, cursor: "pointer", fontFamily: "monospace", fontWeight: "bold" }}>Start HTTP Listener</button>
        </div>

        {/* CVE Search */}
        <div style={{ background: "#111", border: "1px solid #333", borderRadius: 12, padding: 20 }}>
          <h3 style={{ color: "#ffaa00" }}>🔍 Zero-Day Search</h3>
          <input value={cveQuery} onChange={e => setCveQuery(e.target.value)} onKeyDown={e => e.key === "Enter" && searchCVE()} style={{ width: "100%", padding: 10, background: "#222", color: "#fff", border: "1px solid #444", borderRadius: 8, marginBottom: 10, fontFamily: "monospace" }} placeholder="CVE ID or software name" />
          <button onClick={searchCVE} style={{ width: "100%", padding: 12, background: "#ffaa0022", color: "#ffaa00", border: "1px solid #ffaa00", borderRadius: 8, cursor: "pointer", fontFamily: "monospace", fontWeight: "bold" }}>Search CVEs</button>
          {zeroday.length > 0 && <div style={{ marginTop: 10, color: "#888", fontSize: "0.8em" }}>{zeroday.length} results</div>}
        </div>
      </div>

      {/* Agent Cards */}
      <div style={{ marginBottom: 30 }}>
        <h3 style={{ color: "#00ff88", marginBottom: 15 }}>🤖 Agent Roster</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px,1fr))", gap: 15 }}>
          {agents.map((a: any, i: number) => (
            <div key={i} style={{ background: "#111", border: `1px solid ${a.confidence > 0.7 ? "#00ff88" : a.confidence > 0.4 ? "#ffaa00" : "#ff4444"}33`, borderRadius: 12, padding: 15 }}>
              <div style={{ color: "#00ff88", fontWeight: "bold", marginBottom: 5 }}>{a.name}</div>
              <div style={{ color: "#666", fontSize: "0.8em" }}>{a.role} — {a.model}</div>
              <div style={{ marginTop: 10, display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "#00ccff" }}>ELO: {a.elo}</span>
                <span style={{ color: "#aaa" }}>{a.wins}W-{a.losses}L</span>
              </div>
              <div style={{ marginTop: 5, fontSize: "0.7em", color: "#666" }}>
                Tools: {a.tools?.slice(0, 3).join(", ")}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Activity Log */}
      <div style={{ background: "#0d1117", border: "1px solid #333", borderRadius: 12, padding: 20 }}>
        <h3 style={{ color: "#00ff88", marginBottom: 10 }}>📋 Activity Log</h3>
        <div style={{ maxHeight: 300, overflowY: "auto" }}>
          {logs.map((l, i) => (
            <div key={i} style={{ color: l.includes("✅") ? "#00ff88" : l.includes("❌") ? "#ff4444" : "#888", fontSize: "0.85em", padding: "4px 0", borderBottom: "1px solid #ffffff08" }}>{l}</div>
          ))}
          {logs.length === 0 && <div style={{ color: "#444" }}>No activity yet. Use the controls above.</div>}
        </div>
      </div>

      <div style={{ textAlign: "center", marginTop: 30, color: "#444", fontSize: "0.7em" }}>
        HackWithAI v2 — Unrestricted Control Panel | {new Date().getFullYear()}
      </div>
    </div>
  );
}
