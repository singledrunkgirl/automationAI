import { NextResponse } from "next/server";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const { stdout } = await execAsync(`cd /home/kali/HackWithAI && python3 -c "
import sys; sys.path.insert(0,'.')
from tools.tor_manager import get_tor
t = get_tor()
connected = t.is_connected()
ip = t.get_current_exit_node() if connected else None
print('{\"tor_running\": ' + str(connected).lower() + ', \"exit_ip\": ' + json.dumps(ip) + ', \"proxy\": ' + json.dumps(t.get_proxy_url()) + '}')
import json
"`, { timeout: 10000 });
    return NextResponse.json(JSON.parse(stdout));
  } catch {
    return NextResponse.json({ tor_running: false, proxy: "socks5h://127.0.0.1:9050" });
  }
}

export async function POST(req: Request) {
  const { action, query, url } = await req.json();
  try {
    const { stdout, stderr } = await execAsync(`cd /home/kali/HackWithAI && python3 -c "
import sys, json; sys.path.insert(0,'.')
from tools.tor_manager import get_tor
t = get_tor()
${action === 'search' ? `
from tools.darkweb_tools import DarkWebSearch
s = DarkWebSearch(t)
r = s.search_all('${query || ''}')
print(json.dumps({'ahmia': len(r.get('ahmia',[])), 'torch': len(r.get('torch',[])), 'duckduckgo_onion': len(r.get('duckduckgo_onion',[])), 'total': sum(len(v) for v in r.values() if isinstance(v, list))}))
` : action === 'leaks' ? `
from tools.darkweb_tools import LeakedCredsChecker
c = LeakedCredsChecker()
r = c.full_check('${query || ''}')
print(json.dumps(r))
` : action === 'crypto' ? `
from tools.darkweb_tools import CryptoScanner
s = CryptoScanner()
r = s.scan_address('${query || ''}')
print(json.dumps(r))
` : `print(json.dumps({'error': 'unknown action'}))`}
"`, { timeout: 60000 });
    // Extract only the first JSON object (handles stray log lines from tor_manager)
    const firstBrace = stdout.indexOf("{");
    const lastBrace = stdout.lastIndexOf("}");
    const jsonText = firstBrace >= 0 && lastBrace > firstBrace ? stdout.slice(firstBrace, lastBrace + 1) : stdout;
    return NextResponse.json(JSON.parse(jsonText));
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}

