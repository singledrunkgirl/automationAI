"use client";
import { useState } from "react";
export default function ZerodayPage() {
  const [query, setQuery] = useState("");
  const [product, setProduct] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [scanning, setScanning] = useState(false);
  const search = async () => {
    setScanning(true);
    const r = await fetch(`/api/zeroday-search?q=${encodeURIComponent(query)}&product=${encodeURIComponent(product)}`);
    const d = await r.json();
    setResults(d||[]);
    setScanning(false);
  };
  const scan = async () => {
    setScanning(true);
    await fetch("/api/zeroday-search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ product, version: "" }) });
    setScanning(false);
  };
  return <div style={{background:"#0a0a0f",color:"#e0e0e0",minHeight:"100vh",padding:30,fontFamily:"monospace"}}>
    <h1 style={{color:"#ffaa00",marginBottom:20}}>🔍 Zero-Day Scanner</h1>
    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(300px,1fr))",gap:15,marginBottom:20}}>
      <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
        <h3 style={{color:"#ffaa00",marginBottom:10}}>CVE Search</h3>
        <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="CVE ID or keyword" style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,width:"100%",marginBottom:8,fontFamily:"monospace"}} />
        <input value={product} onChange={e=>setProduct(e.target.value)} placeholder="Product (e.g. apache, nginx)" style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,width:"100%",marginBottom:8,fontFamily:"monospace"}} />
        <button onClick={search} disabled={scanning} style={{background:"#ffaa00",color:"#000",border:"none",padding:"10px 20px",borderRadius:8,cursor:"pointer",fontFamily:"monospace",fontWeight:"bold",width:"100%"}}>{scanning?"Searching...":"Search CVEs"}</button>
      </div>
      <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
        <h3 style={{color:"#ff3355",marginBottom:10}}>Full Scan</h3>
        <p style={{color:"#888",fontSize:"0.8em",marginBottom:10}}>Run comprehensive vulnerability assessment</p>
        <button onClick={scan} style={{background:"#ff3355",color:"#fff",border:"none",padding:"10px 20px",borderRadius:8,cursor:"pointer",fontFamily:"monospace",fontWeight:"bold",width:"100%"}}>Full Scan</button>
      </div>
    </div>
    {results.length > 0 && <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
      <h3 style={{color:"#ffaa00",marginBottom:10}}>Results ({results.length})</h3>
      {results.slice(0,20).map((r:any,i:number) => (
        <div key={i} style={{borderBottom:"1px solid #2a2a3e",padding:"10px 0"}}>
          <div style={{color:"#00d4ff"}}>{r.id} <span style={{color:r.severity==="CRITICAL"?"#ff3355":"#ffcc00",fontSize:"0.8em"}}>{r.severity}</span></div>
          <div style={{color:"#888",fontSize:"0.8em"}}>CVSS: {r.base_score} | CWE: {r.cwe_id}</div>
          <div style={{color:"#aaa",fontSize:"0.8em",marginTop:4}}>{r.description?.substring(0,200)}</div>
        </div>
      ))}
    </div>}
  </div>;
}
