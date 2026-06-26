import { NextRequest, NextResponse } from "next/server";

const BURP_BASE = process.env.BURP_API_URL || "http://127.0.0.1:1337";
const BURP_API_KEY = process.env.BURP_API_KEY || "";

async function burpRequest(path: string, method: string = "GET", body?: unknown) {
  try {
    const headers: Record<string, string> = {
      Accept: "application/json",
      "Content-Type": "application/json",
    };
    if (BURP_API_KEY) {
      headers["Authorization"] = `Bearer ${BURP_API_KEY}`;
    }

    const options: RequestInit = { method, headers };
    if (body && method !== "GET") {
      options.body = JSON.stringify(body);
    }

    const res = await fetch(`${BURP_BASE}${path}`, options);
    const text = await res.text();

    try {
      return NextResponse.json(JSON.parse(text));
    } catch {
      return new NextResponse(text, { status: res.status });
    }
  } catch (error) {
    return NextResponse.json(
      { error: "Burp Suite connection failed", details: String(error) },
      { status: 502 },
    );
  }
}

// Proxy all Burp API calls: /api/burp/proxy/* → Burp REST API
export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const burpPath = url.pathname.replace("/api/burp/proxy", "");
  const query = url.search;
  return burpRequest(`${burpPath}${query}`);
}

export async function POST(req: NextRequest) {
  const url = new URL(req.url);
  const burpPath = url.pathname.replace("/api/burp/proxy", "");
  const body = await req.json().catch(() => null);
  return burpRequest(burpPath, "POST", body);
}

export async function PUT(req: NextRequest) {
  const url = new URL(req.url);
  const burpPath = url.pathname.replace("/api/burp/proxy", "");
  const body = await req.json().catch(() => null);
  return burpRequest(burpPath, "PUT", body);
}
