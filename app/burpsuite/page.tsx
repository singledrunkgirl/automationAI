"use client";
import { useState } from "react";
export default function BurpSuitePage() {
  const [url, setUrl] = useState(""); const [cfg, setCfg] = useState("light");
  const [scanning, setScanning] = useState(false); const [issues, setIssues] = useState<any[]>([]);
  const [conn, setConn] = useState(false);
  const checkConn = async () => { try { const r = await fetch("/api/burpsuite?action=proxy/history"); setConn(r.ok); } catch { setConn(false); } };
  const startScan = async () => {
    setScanning(true);
    const r = await fetch("/api/burpsuite", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({ action:"scan", data:{url,scanConfiguration:cfg} }) });
    const d = await r.json();
    if (d.scanId) {
      const iv = setInterval(async () => { const s = await (await fetch(`/api/burpsuite?action=scan/${d.scanId}`)).json();
        if (["succeeded","failed"].includes(s.scanStatus)) { clearInterval(iv); const is = await (await fetch(`/api/burpsuite?action=scan/${d.scanId}/issues`)).json(); setIssues(is.issues||[]); setScanning(false); } }, 3000);
    } else setScanning(false);
  };
  return <div style={{background:"#0a0a0f",color:"#e0e0e0",minHeight:"100vh",padding:30,fontFamily:"monospace"}}>
    <h1 style={{color:"#ff6600",marginBottom:10}}>🛡️ BurpSuite Pro</h1>
    <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:20}}><div onClick={checkConn} style={{cursor:"pointer",width:12,height:12,borderRadius:"50%",background:conn?"#00ff88":"#ff3355"}}/> {conn?"Connected":"Disconnected"} — <span style={{color:"#888",fontSize:"0.8em"}}>click dot to check</span></div>
    <div style={{display:"flex",gap:10,marginBottom:20}}>
      <input value={url} onChange={e=>setUrl(e.target.value)} placeholder="https://target.com" style={{flex:1,background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,fontFamily:"monospace"}} />
      <select value={cfg} onChange={e=>setCfg(e.target.value)} style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,fontFamily:"monospace"}}>
        <option value="light">Light</option><option value="crawl_and_audit">Deep</option><option value="sql_injection">SQLi</option><option value="xss">XSS</option>
      </select>
      <button onClick={startScan} disabled={scanning} style={{background:scanning?"#333":"#ff6600",color:"#fff",border:"none",padding:"10px 20px",borderRadius:8,cursor:"pointer",fontWeight:"bold",fontFamily:"monospace"}}>{scanning?"Scanning...":"Scan"}</button>
    </div>
    <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
      <h3 style={{color:"#ff6600",marginBottom:15}}>Vulnerabilities ({issues.length})</h3>
      {issues.map((i:any,x:number) => (
        <div key={x} style={{borderBottom:"1px solid #2a2a3e",padding:"10px 0"}}>
          <div style={{display:"flex",justifyContent:"space-between"}}>
            <span style={{color:"#00d4ff"}}>{i.name}</span>
            <span style={{color:i.severity==="critical"?"#ff3355":i.severity==="high"?"#ff6600":"#ffcc00",fontWeight:"bold"}}>{i.severity}</span>
          </div>
          <div style={{color:"#888",fontSize:"0.8em"}}>{i.url}</div>
          <details><summary style={{color:"#00ff88",cursor:"pointer",fontSize:"0.8em"}}>Details</summary><p style={{color:"#aaa",fontSize:"0.8em"}}>{i.description}</p></details>
        </div>
      ))}
      {issues.length===0 && <div style={{color:"#666",textAlign:"center",padding:30}}>No vulnerabilities found. Run a scan.</div>}
    </div>
  </div>;
}
