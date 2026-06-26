import { NextResponse } from "next/server";

const BURP_BASE = process.env.BURP_API_URL || "http://127.0.0.1:1337";
const BURP_API_KEY = process.env.BURP_API_KEY || "";

async function burpGET(path: string) {
  try {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (BURP_API_KEY) headers["Authorization"] = `Bearer ${BURP_API_KEY}`;
    const res = await fetch(`${BURP_BASE}${path}`, { headers, signal: AbortSignal.timeout(10000) });
    const data = await res.json();
    return data;
  } catch {
    return null;
  }
}

// GET /api/burp/status — unified Burp status dashboard
export async function GET() {
  const [scope, issues, history] = await Promise.all([
    burpGET("/burp/api/v2/target/scope"),
    burpGET("/burp/api/v2/scan/issues"),
    burpGET("/burp/api/v2/proxy/history?limit=20"),
  ]);

  const historyItems = Array.isArray(history?.data)
    ? history.data.map((h: Record<string, unknown>) => ({
        url: h.url,
        method: h.method,
        statusCode: h.statusCode,
        mimeType: h.mimeType,
        hasParams: h.hasParams,
      }))
    : [];

  const issueList = Array.isArray(issues?.issues)
    ? issues.issues.map((i: Record<string, unknown>) => ({
        name: i.name,
        severity: i.severity,
        confidence: i.confidence,
        host: i.host,
        path: i.path,
      }))
    : [];

  return NextResponse.json({
    connected: history !== null || issues !== null,
    scope: scope?.urls || [],
    proxy_history_count: historyItems.length,
    proxy_history: historyItems.slice(0, 10),
    issue_count: issueList.length,
    issues: issueList.slice(0, 10),
    timestamp: new Date().toISOString(),
  });
}
