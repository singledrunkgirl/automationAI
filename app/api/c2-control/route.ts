import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const { stdout } = await execAsync(`cd /home/kali/HackWithAI && python3 -c "
import sys, json; sys.path.insert(0,'.')
from tools.c2_framework import C2Framework
c2 = C2Framework()
print(json.dumps(c2.status()))
"`, { timeout: 10000 });
    return NextResponse.json(JSON.parse(stdout));
  } catch {
    return NextResponse.json({ server: { running: false, agents: 0, listeners: [] } });
  }
}

export async function POST(req: Request) {
  const { action, port } = await req.json();
  try {
    if (action === "start") {
      await execAsync(`cd /home/kali/HackWithAI && python3 -c "
from tools.c2_framework import C2Framework
c2 = C2Framework()
c2.start(${port || 8080})
"`, { timeout: 5000 });
      return NextResponse.json({ ok: true, action: "started", port: port || 8080 });
    }
    if (action === "generate") {
      const { stdout } = await execAsync(`cd /home/kali/HackWithAI && python3 -c "
import sys, json; sys.path.insert(0,'.')
from tools.c2_framework import AgentGenerator
g = AgentGenerator('127.0.0.1', ${port || 8080})
print(json.dumps(g.generate_all()))
"`, { timeout: 10000 });
      return NextResponse.json(JSON.parse(stdout));
    }
    return NextResponse.json({ error: "unknown action" }, { status: 400 });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
