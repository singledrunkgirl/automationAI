"use client";
import { useState, useEffect } from "react";
export default function ReportsPage() {
  const [reports, setReports] = useState<any[]>([]);
  useEffect(() => { fetch("/api/reports-gen").then(r=>r.json()).then(d=>setReports(d.reports||[])); }, []);
  return <div style={{background:"#0a0a0f",color:"#e0e0e0",minHeight:"100vh",padding:30,fontFamily:"monospace"}}>
    <h1 style={{color:"#ffcc00",marginBottom:20}}>📋 Reports</h1>
    <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20,marginBottom:20}}>
      <h3 style={{color:"#ffcc00",marginBottom:10}}>Attack Reports</h3>
      {reports.length === 0 && <div style={{color:"#888"}}>No reports generated yet. Run a mission to generate one.</div>}
      {reports.map((r:any,i:number)=>(
        <div key={i} style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"12px 0",borderBottom:"1px solid #2a2a3e"}}>
          <div>
            <div style={{color:"#00d4ff"}}>{r.name}</div>
            <div style={{color:"#888",fontSize:"0.75em"}}>{r.size} bytes · {new Date(r.created).toLocaleString()}</div>
          </div>
          <button onClick={()=>window.open(`/data/reports/${r.name}`)} style={{background:"#ffcc00",color:"#000",border:"none",padding:"8px 16px",borderRadius:8,cursor:"pointer",fontFamily:"monospace",fontWeight:"bold"}}>Download</button>
        </div>
      ))}
    </div>
  </div>;
}
