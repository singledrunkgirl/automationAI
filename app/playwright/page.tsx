"use client";
import { useState } from "react";
export default function PlaywrightPage() {
  const [url, setUrl] = useState("");
  const [action, setAction] = useState("navigate");
  const [results, setResults] = useState<any>(null);
  const [log, setLog] = useState<string[]>([]);
  const execute = async () => {
    setLog(l=>[...l, `${action}: ${url}`]);
    const r = await fetch("/api/playwright-proxy", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({url,action}) });
    setResults(await r.json());
  };
  return <div style={{background:"#0a0a0f",color:"#e0e0e0",minHeight:"100vh",padding:30,fontFamily:"monospace"}}>
    <h1 style={{color:"#00d4ff",marginBottom:20}}>🎭 Browser Automation</h1>
    <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20,marginBottom:20}}>
      <div style={{display:"flex",gap:10,marginBottom:10}}>
        <input value={url} onChange={e=>setUrl(e.target.value)} placeholder="URL (e.g. http://example.com)" style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,flex:1,fontFamily:"monospace"}} />
        <select value={action} onChange={e=>setAction(e.target.value)} style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,fontFamily:"monospace"}}>
          <option value="navigate">Navigate</option>
          <option value="crawl">Crawl</option>
          <option value="xss">Test XSS</option>
          <option value="forms">Extract Forms</option>
        </select>
      </div>
      <button onClick={execute} style={{background:"#00d4ff",color:"#000",border:"none",padding:"10px 20px",borderRadius:8,cursor:"pointer",fontFamily:"monospace",fontWeight:"bold",width:"100%"}}>Execute</button>
    </div>
    {results && <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20,marginBottom:20}}>
      <pre style={{color:"#aaa",fontSize:"0.8em",whiteSpace:"pre-wrap"}}>{JSON.stringify(results, null, 2)}</pre>
    </div>}
    <div style={{background:"#0d1117",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
      <h3 style={{color:"#00d4ff",marginBottom:10}}>Activity</h3>
      {log.map((l,i)=><div key={i} style={{color:"#888",fontSize:"0.8em"}}>{l}</div>)}
    </div>
  </div>;
}
