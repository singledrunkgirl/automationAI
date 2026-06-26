"use client";
import { useState, useEffect } from "react";
const A = (p: string) => `/api${p}`;
export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [target, setTarget] = useState("");
  const [result, setResult] = useState<any>(null);
  const [log, setLog] = useState<string[]>([]);
  useEffect(() => { fetch(A("/agents-info")).then(r => r.json()).then(d => setAgents(d.agents||[])); }, []);
  const debate = async () => {
    setLog(l => [...l, `Debating: ${target}`]);
    const r = await fetch(A("/agents-info"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ target }) });
    const d = await r.json();
    setResult(d);
    setLog(l => [...l, `Winner: ${d.winner} (${Math.round((d.consensus||0)*100)}%)`]);
  };
  return <div style={{background:"#0a0a0f",color:"#e0e0e0",minHeight:"100vh",padding:30,fontFamily:"monospace"}}>
    <h1 style={{color:"#00ff88",marginBottom:20}}>🤖 Agent Management</h1>
    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(260px,1fr))",gap:15,marginBottom:30}}>
      {agents.map((a:any,i:number) => (
        <div key={i} style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
          <div style={{color:"#00ff88",fontWeight:"bold",fontSize:"1.1em"}}>{a.name}</div>
          <div style={{color:"#888",fontSize:"0.8em",marginBottom:10}}>{a.role} — {a.model}</div>
          <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
            <span style={{color:"#00d4ff"}}>ELO: {a.elo}</span>
            <span style={{color:"#aaa"}}>{a.wins}W-{a.losses}L</span>
          </div>
          <div style={{color:"#ffcc00",fontSize:"0.85em"}}>Confidence: {(a.confidence*100).toFixed(0)}%</div>
          <div style={{color:"#666",fontSize:"0.7em",marginTop:8}}>Tools: {a.tools?.join(", ")}</div>
        </div>
      ))}
    </div>
    <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20,marginBottom:20}}>
      <h3 style={{color:"#00ff88",marginBottom:10}}>🗣️ Start Debate</h3>
      <input value={target} onChange={e => setTarget(e.target.value)} placeholder="Target (e.g. scanme.nmap.org)" style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,width:"100%",marginBottom:10,fontFamily:"monospace"}} />
      <button onClick={debate} style={{background:"#00ff88",color:"#000",border:"none",padding:"10px 20px",borderRadius:8,cursor:"pointer",fontFamily:"monospace",fontWeight:"bold"}}>Start Debate</button>
    </div>
    {result && <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20,marginBottom:20}}>
      <h3 style={{color:"#00d4ff",marginBottom:10}}>Debate Result</h3>
      <pre style={{color:"#aaa",whiteSpace:"pre-wrap",fontSize:"0.85em"}}>{JSON.stringify(result, null, 2)}</pre>
    </div>}
    <div style={{background:"#0d1117",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
      <h3 style={{color:"#00ff88",marginBottom:10}}>Activity Log</h3>
      {log.map((l,i) => <div key={i} style={{color:"#888",fontSize:"0.8em",padding:"2px 0"}}>{l}</div>)}
    </div>
  </div>;
}
