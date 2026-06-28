import { NextRequest } from "next/server";
import { addToolEventListener, getRecentToolEvents } from "../tool-events";

export const dynamic = "force-dynamic";

export async function GET(_req: NextRequest) {
  let cleanup: (() => void) | null = null;

  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();

      // Send initial connection event
      controller.enqueue(
        encoder.encode(
          `data: ${JSON.stringify({ type: "connected", source: "tool_stream" })}\n\n`,
        ),
      );

      // Replay recent events
      for (const event of getRecentToolEvents(100)) {
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({ type: "tool_event", ...event })}\n\n`,
          ),
        );
      }

      // Subscribe to new events
      cleanup = addToolEventListener((event) => {
        try {
          controller.enqueue(
            encoder.encode(
              `data: ${JSON.stringify({ type: "tool_event", ...event })}\n\n`,
            ),
          );
        } catch {
          // stream closed
        }
      });

      // Keepalive every 15s
      const keepalive = setInterval(() => {
        try {
          controller.enqueue(encoder.encode(`: keepalive\n\n`));
        } catch {
          clearInterval(keepalive);
        }
      }, 15000);
    },
    cancel() {
      cleanup?.();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}

