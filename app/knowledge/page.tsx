"use client";
import { useState, useEffect } from "react";
export default function KnowledgePage() {
  const [stats, setStats] = useState<any>({});
  const [node, setNode] = useState("");
  const [related, setRelated] = useState<any[]>([]);
  const [startType, setStartType] = useState("agent");
  const [endType, setEndType] = useState("target");
  const [path, setPath] = useState<any[]>([]);
  useEffect(() => { fetch("/api/knowledge-graph").then(r=>r.json()).then(setStats); }, []);
  const queryRelated = async () => {
    const r = await fetch("/api/knowledge-graph", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({action:"related",node}) });
    setRelated(await r.json());
  };
  const findPath = async () => {
    const r = await fetch("/api/knowledge-graph", { method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({action:"path",node:startType,targetType:endType}) });
    setPath(await r.json());
  };
  return <div style={{background:"#0a0a0f",color:"#e0e0e0",minHeight:"100vh",padding:30,fontFamily:"monospace"}}>
    <h1 style={{color:"#aa66ff",marginBottom:20}}>🧠 Knowledge Graph</h1>
    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(200px,1fr))",gap:15,marginBottom:20}}>
      {[{l:"Nodes",v:stats.total_nodes||0,c:"#00ff88"},{l:"Edges",v:stats.total_edges||0,c:"#00d4ff"},{l:"DB Size",v:(stats.db_size_mb||0)+"MB",c:"#ffcc00"},{l:"Node Types",v:stats.node_types?Object.keys(stats.node_types).length:0,c:"#aa66ff"}].map((c,i)=><div key={i} style={{background:"#1a1a2e",border:`1px solid ${c.c}44`,borderRadius:12,padding:20,textAlign:"center"}}><div style={{color:c.c,fontSize:"2em",fontWeight:"bold"}}>{c.v}</div><div style={{color:"#888",fontSize:"0.8em"}}>{c.l}</div></div>)}
    </div>
    <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(300px,1fr))",gap:15}}>
      <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
        <h3 style={{color:"#00d4ff",marginBottom:10}}>Query Related</h3>
        <input value={node} onChange={e=>setNode(e.target.value)} placeholder="Node name" style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,width:"100%",marginBottom:8,fontFamily:"monospace"}} />
        <button onClick={queryRelated} style={{background:"#00d4ff",color:"#000",border:"none",padding:"10px",borderRadius:8,cursor:"pointer",width:"100%",fontFamily:"monospace",fontWeight:"bold"}}>Search</button>
        {related.length>0 && <div style={{marginTop:10}}>{related.map((r:any,i:number)=><div key={i} style={{color:"#888",fontSize:"0.8em",padding:"4px 0",borderBottom:"1px solid #2a2a3e"}}>{r.node?.name} ({r.node?.type}) — <span style={{color:"#00ff88"}}>{r.relationship}</span></div>)}</div>}
      </div>
      <div style={{background:"#1a1a2e",border:"1px solid #2a2a3e",borderRadius:12,padding:20}}>
        <h3 style={{color:"#aa66ff",marginBottom:10}}>Find Best Path</h3>
        <div style={{display:"flex",gap:8,marginBottom:8}}>
          <input value={startType} onChange={e=>setStartType(e.target.value)} placeholder="Start type" style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,flex:1,fontFamily:"monospace"}} />
          <span style={{color:"#888",alignSelf:"center"}}>→</span>
          <input value={endType} onChange={e=>setEndType(e.target.value)} placeholder="End type" style={{background:"#12121a",border:"1px solid #2a2a3e",color:"#e0e0e0",padding:10,borderRadius:8,flex:1,fontFamily:"monospace"}} />
        </div>
        <button onClick={findPath} style={{background:"#aa66ff",color:"#fff",border:"none",padding:"10px",borderRadius:8,cursor:"pointer",width:"100%",fontFamily:"monospace",fontWeight:"bold"}}>Find Path</button>
        {path.length>0 && <div style={{marginTop:10}}>{path.map((n:any,i:number)=><div key={i} style={{color:i<path.length-1?"#00ff88":"#ffcc00",fontSize:"0.8em",padding:"4px 0"}}>{i+1}. {n.name} ({n.type}) {n.next_relationship?`→ ${n.next_relationship}`:""}</div>)}</div>}
      </div>
    </div>
  </div>;
}
