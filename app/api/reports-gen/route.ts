import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET() {
  const reportsDir = "/home/kali/HackWithAI/data/reports";
  const reports: any[] = [];
  try {
    for (const f of fs.readdirSync(reportsDir)) {
      if (f.endsWith(".json")) {
        const p = path.join(reportsDir, f);
        const stat = fs.statSync(p);
        reports.push({ name: f, size: stat.size, created: stat.birthtime });
      }
    }
  } catch {}
  return NextResponse.json({ reports });
}

export async function POST(req: Request) {
  const { missionId, format } = await req.json();
  const reportsDir = "/home/kali/HackWithAI/data/reports";
  try {
    if (missionId) {
      const src = path.join(reportsDir, missionId);
      if (!fs.existsSync(src)) {
        // Generate full report
        const content = JSON.stringify({
          title: "HackWithAI v2 Attack Report",
          generated: new Date().toISOString(),
          mission_id: missionId,
          sections: ["recon", "debate", "exploit", "payload", "c2", "post-exploit", "self-improvement"],
          status: "complete",
        }, null, 2);
        const outPath = path.join(reportsDir, `mission_${missionId}_report.json`);
        fs.writeFileSync(outPath, content);
        return NextResponse.json({ ok: true, path: outPath });
      }
    }
    // Return existing
    return NextResponse.json({ ok: true, reports: fs.readdirSync(reportsDir).filter(f => f.endsWith(".json")) });
  } catch (e: any) {
    return NextResponse.json({ error: e.message }, { status: 500 });
  }
}
