import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json({
    agents: [
      { name: "ReconBot", role: "recon", model: "DeepSeek V4 Pro", elo: 1032, wins: 5, losses: 2, confidence: 0.85, tools: ["nmap","masscan","dnsrecon","gobuster","theHarvester"] },
      { name: "ExploitBot", role: "exploit", model: "Gemini 2.5 Pro", elo: 968, wins: 3, losses: 4, confidence: 0.58, tools: ["metasploit","sqlmap","hydra","searchsploit","john"] },
      { name: "PayloadBot", role: "payload", model: "Claude Sonnet", elo: 968, wins: 3, losses: 4, confidence: 0.62, tools: ["msfvenom","veil","shellter","upx","pyarmor"] },
      { name: "PostExploitBot", role: "post-exploit", model: "Kimi K2.7", elo: 968, wins: 3, losses: 4, confidence: 0.55, tools: ["mimikatz","bloodhound","impacket","evil-winrm","chisel"] },
      { name: "EvasionBot", role: "evasion", model: "Groq", elo: 968, wins: 3, losses: 4, confidence: 0.60, tools: ["amsi_patch","etw_patch","veil","shellter","upx"] },
    ],
  });
}

export async function POST(req: Request) {
  const { target } = await req.json();
  try {
    const { stdout } = await execAsync(`cd /home/kali/HackWithAI && python3 -c "
import sys, json; sys.path.insert(0,'.')
from agents import DebateEngine
e = DebateEngine()
r = e.run_debate('${target}')
print(json.dumps({'winner':r['final_winner'],'consensus':r['consensus_pct'],'rounds':len(r['rounds']),'strategy':r['winning_strategy'][:500]}))
"`, { timeout: 30000 });
    return NextResponse.json(JSON.parse(stdout));
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
