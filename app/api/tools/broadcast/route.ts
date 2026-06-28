import { NextRequest, NextResponse } from "next/server";
import { pushToolEvent, getRecentToolEvents } from "../tool-events";

// POST — tools push events here
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { source, message, timestamp } = body;

    if (!source || !message) {
      return NextResponse.json(
        { error: "source and message required" },
        { status: 400 },
      );
    }

    pushToolEvent({
      source,
      message,
      timestamp: timestamp || new Date().toISOString(),
    });

    return NextResponse.json({ success: true });
  } catch {
    return NextResponse.json({ error: "Invalid request" }, { status: 400 });
  }
}

// GET — consumer reads recent events
export async function GET() {
  const events = getRecentToolEvents(100);
  return NextResponse.json({
    events,
    total: events.length,
  });
}

