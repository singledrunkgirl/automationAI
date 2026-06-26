import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const query = searchParams.get("q") || "";
  const product = searchParams.get("product") || "";
  try {
    const { stdout } = await execAsync(`cd /home/kali/HackWithAI && python3 -c "
import sys, json; sys.path.insert(0,'.')
from tools.zeroday_scanner import CVEDatabase
db = CVEDatabase()
results = db.search(query='${query}', product='${product}', min_score=5.0, limit=20)
print(json.dumps(results))
"`, { timeout: 15000 });
    return NextResponse.json(JSON.parse(stdout));
  } catch {
    return NextResponse.json([]);
  }
}

export async function POST(req: Request) {
  const { product, version } = await req.json();
  try {
    const { stdout } = await execAsync(`cd /home/kali/HackWithAI && python3 -c "
import sys, json; sys.path.insert(0,'.')
from tools.zeroday_scanner import ZeroDayScanner
s = ZeroDayScanner()
results = s.full_scan('', [{'product': '${product || ''}', 'version': '${version || ''}'}])
print(json.dumps({'cve_matches': len(results['cve_matches']), 'exploits': len(results['exploit_suggestions']), 'anomalies': len(results['anomalies'])}))
"`, { timeout: 30000 });
    return NextResponse.json(JSON.parse(stdout));
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
