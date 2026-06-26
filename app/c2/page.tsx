"use client";
import { useState, useEffect } from "react";
const A = (p: string) => `/api${p}`;
export default function C2Page() {
  const [port, setPort] = useState(8080);
  const [c2Status, setC2Status] = useState<any>(null);
  const [agentId, setAgentId] = useState("");
  const [command, setCommand] = useState("");
  const [log, setLog] = useState<string[]>([]);
  const fetchStatus = () => fetch(A("/c2-control")).then(r=>r.json()).then(setC2Status);
  useEffect(() => { fetchStatus(); }, []);
  const start = async () => {
    await fetch(A("/c2-control"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "start", port }) });
    setLog(l=>[...l, `C2 HTTP listener started on :${port}`]);
    fetchStatus();
  };
  const generate = async () => {
    const r = await fetch(A("/c2-control"), { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ action: "generate", port }) });
    const d = await r.json();
    setLog(l=>[...l, `Agents generated: ${Object.keys(d).join(", ")}`]);
  };
  return <div style={{background:"#0a0a0f",color:"#e0e0e0",minHeight:"100vh",padding:30,fontFamily:"monospace"}}>
    <h1 style={{color:"#00d4ff",marginBottom:20}}>🌐 C2 Dashboard</h1>
    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(300px,1fr))",gap:15,marginBottom:20}}>
      <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
        <h3 style={{color:"#00ff88",marginBottom:10}}>Listener Control</h3>
        <input type="number" value={port} onChange={e=>setPort(+e.target.value)} style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,width:"100%",marginBottom:10,fontFamily:"monospace"}} placeholder="Port" />
        <button onClick={start} style={{background:"#00ff88",color:"#000",border:"none",padding:"10px 20px",borderRadius:8,cursor:"pointer",fontFamily:"monospace",fontWeight:"bold",width:"100%"}}>Start HTTP Listener</button>
      </div>
      <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
        <h3 style={{color:"#aa66ff",marginBottom:10}}>Payload Generator</h3>
        <button onClick={generate} style={{background:"#aa66ff",color:"#fff",border:"none",padding:"10px 20px",borderRadius:8,cursor:"pointer",fontFamily:"monospace",fontWeight:"bold",width:"100%"}}>Generate Agents</button>
      </div>
      <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
        <h3 style={{color:"#ffcc00",marginBottom:10}}>Send Task</h3>
        <input value={agentId} onChange={e=>setAgentId(e.target.value)} placeholder="Agent ID" style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,width:"100%",marginBottom:8,fontFamily:"monospace"}} />
        <input value={command} onChange={e=>setCommand(e.target.value)} placeholder="Command" style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,width:"100%",marginBottom:8,fontFamily:"monospace"}} />
        <button onClick={() => setLog(l=>[...l, `Task queued: ${command}`])} style={{background:"#ffcc00",color:"#000",border:"none",padding:"8px 16px",borderRadius:8,cursor:"pointer",fontFamily:"monospace",fontWeight:"bold",width:"100%"}}>Send Task</button>
      </div>
    </div>
    {c2Status && <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20,marginBottom:20}}>
      <pre style={{color:"#aaa",fontSize:"0.8em"}}>{JSON.stringify(c2Status, null, 2)}</pre>
    </div>}
    <div style={{background:"#0d1117",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
      <h3 style={{color:"#00ff88",marginBottom:10}}>Activity</h3>
      {log.map((l,i)=><div key={i} style={{color:"#888",fontSize:"0.8em",padding:"2px 0"}}>{l}</div>)}
    </div>
  </div>;
}
