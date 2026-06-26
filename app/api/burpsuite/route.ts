import { NextResponse } from "next/server";
export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const BURP = process.env.BURP_API_URL || "http://127.0.0.1:1337";
const KEY = process.env.BURP_API_KEY || "";

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url);
  const action = searchParams.get("action") || "proxy/history";
  try {
    const r = await fetch(`${BURP}/burp/api/v2/${action}`, { headers: { Authorization: `Bearer ${KEY}` } });
    return NextResponse.json(await r.json());
  } catch (e: any) { return NextResponse.json({ error: e.message }, { status: 500 }); }
}

export async function POST(req: Request) {
  const { action, data } = await req.json();
  try {
    const r = await fetch(`${BURP}/burp/api/v2/${action}`, {
      method: "POST", headers: { "Content-Type":"application/json", Authorization: `Bearer ${KEY}` },
      body: JSON.stringify(data || {})
    });
    return NextResponse.json(await r.json());
  } catch (e: any) { return NextResponse.json({ error: e.message }, { status: 500 }); }
}
