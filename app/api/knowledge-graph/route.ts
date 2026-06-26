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
from core.knowledge_graph import get_knowledge_graph
kg = get_knowledge_graph()
print(json.dumps(kg.stats()))
"`, { timeout: 5000 });
    return NextResponse.json(JSON.parse(stdout));
  } catch {
    return NextResponse.json({ total_nodes: 0, total_edges: 0 });
  }
}

export async function POST(req: Request) {
  const { action, node, nodeType, targetType } = await req.json();
  try {
    const { stdout } = await execAsync(`cd /home/kali/HackWithAI && python3 -c "
import sys, json; sys.path.insert(0,'.')
from core.knowledge_graph import get_knowledge_graph
kg = get_knowledge_graph()
${action === 'recommend' ? `r = kg.get_recommendations('${targetType || 'target'}'); print(json.dumps(r))` :
  action === 'related' ? `r = kg.query_related('${node || ''}'); print(json.dumps(r))` :
  action === 'path' ? `r = kg.find_best_path('${node || 'agent'}', '${targetType || 'target'}'); print(json.dumps(r))` :
  `print(json.dumps(kg.stats()))`}
"`, { timeout: 10000 });
    return NextResponse.json(JSON.parse(stdout));
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
