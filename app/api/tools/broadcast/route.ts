import { NextRequest, NextResponse } from "next/server";

// In-memory event store shared with SSE consumers
const eventStore: Array<{ source: string; message: string; timestamp: string }> = [];
const MAX_EVENTS = 500;
const listeners = new Set<(event: unknown) => void>();

export function addToolEventListener(fn: (event: unknown) => void) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

// POST — tools push events here
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { source, message, timestamp } = body;

    if (!source || !message) {
      return NextResponse.json({ error: "source and message required" }, { status: 400 });
    }

    const event = { source, message, timestamp: timestamp || new Date().toISOString() };
    eventStore.push(event);
    if (eventStore.length > MAX_EVENTS) eventStore.shift();

    // Notify SSE listeners
    for (const listener of listeners) {
      try { listener(event); } catch {}
    }

    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }
}

// GET — consumer reads recent events
export async function GET() {
  return NextResponse.json({
    events: eventStore.slice(-100),
    total: eventStore.length,
  });
}
