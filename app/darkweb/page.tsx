"use client";
import { useState, useEffect } from "react";
export default function DarkwebPage() {
  const [torStatus, setTorStatus] = useState<any>({});
  const [query, setQuery] = useState("");
  const [onionUrl, setOnionUrl] = useState("");
  const [btcAddr, setBtcAddr] = useState("");
  const [results, setResults] = useState<any>(null);
  const [log, setLog] = useState<string[]>([]);
  useEffect(() => { fetch("/api/darkweb-proxy").then(r=>r.json()).then(setTorStatus); }, []);
  const search = async () => {
    setLog(l=>[...l,`Searching: ${query}`]);
    const r = await fetch("/api/darkweb-proxy", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({action:"search",query}) });
    setResults(await r.json());
  };
  const checkLeaks = async () => {
    setLog(l=>[...l,`Checking: ${query}`]);
    const r = await fetch("/api/darkweb-proxy", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({action:"leaks",query}) });
    setResults(await r.json());
  };
  const scanCrypto = async () => {
    setLog(l=>[...l,`Scanning: ${btcAddr}`]);
    const r = await fetch("/api/darkweb-proxy", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({action:"crypto",query:btcAddr}) });
    setResults(await r.json());
  };
  return <div style={{background:"#0a0a0f",color:"#e0e0e0",minHeight:"100vh",padding:30,fontFamily:"monospace"}}>
    <h1 style={{color:"#ff3355",marginBottom:20}}>🕵️ Dark Web Tools</h1>
    <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:20,background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
      <div style={{width:12,height:12,borderRadius:"50%",background:torStatus.tor_running?"#00ff88":"#ff3355",boxShadow:`0 0 8px ${torStatus.tor_running?"#00ff88":"#ff3355"}`}}></div>
      <span style={{color:torStatus.tor_running?"#00ff88":"#ff3355",fontWeight:"bold"}}>Tor: {torStatus.tor_running ? "RUNNING" : "STOPPED"}</span>
      <span style={{color:"#888",fontSize:"0.8em"}}>Proxy: {torStatus.proxy||"socks5h://127.0.0.1:9050"}</span>
      {torStatus.exit_ip && <span style={{color:"#00d4ff",fontSize:"0.8em"}}>Exit: {torStatus.exit_ip}</span>}
    </div>
    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(300px,1fr))",gap:15,marginBottom:20}}>
      <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
        <h3 style={{color:"#ff3355",marginBottom:10}}>Dark Web Search</h3>
        <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Search dark web..." style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,width:"100%",marginBottom:8,fontFamily:"monospace"}} />
        <button onClick={search} style={{background:"#ff3355",color:"#fff",border:"none",padding:"10px",borderRadius:8,cursor:"pointer",width:"100%",fontFamily:"monospace",fontWeight:"bold",marginBottom:4}}>Search</button>
        <button onClick={checkLeaks} style={{background:"#ffcc00",color:"#000",border:"none",padding:"10px",borderRadius:8,cursor:"pointer",width:"100%",fontFamily:"monospace",fontWeight:"bold"}}>Check Leaks</button>
      </div>
      <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
        <h3 style={{color:"#00ff88",marginBottom:10}}>Crypto Scanner</h3>
        <input value={btcAddr} onChange={e=>setBtcAddr(e.target.value)} placeholder="Bitcoin address" style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,width:"100%",marginBottom:8,fontFamily:"monospace"}} />
        <button onClick={scanCrypto} style={{background:"#00ff88",color:"#000",border:"none",padding:"10px",borderRadius:8,cursor:"pointer",width:"100%",fontFamily:"monospace",fontWeight:"bold"}}>Scan Blockchain</button>
      </div>
    </div>
    {results && <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20,marginBottom:20}}>
      <pre style={{color:"#aaa",fontSize:"0.8em",whiteSpace:"pre-wrap"}}>{JSON.stringify(results, null, 2)}</pre>
    </div>}
    <div style={{background:"#0d1117",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
      <h3 style={{color:"#ff3355",marginBottom:10}}>Activity</h3>
      {log.map((l,i)=><div key={i} style={{color:"#888",fontSize:"0.8em"}}>{l}</div>)}
    </div>
  </div>;
}
