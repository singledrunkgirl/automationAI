import { NextRequest } from "next/server";
import { addToolEventListener } from "../broadcast/route";

export const dynamic = "force-dynamic";

export async function GET(_req: NextRequest) {
  let cleanup: (() => void) | null = null;

  const stream = new ReadableStream({
    start(controller) {
      const encoder = new TextEncoder();
      // Send initial connection event
      controller.enqueue(
        encoder.encode(`data: ${JSON.stringify({ type: "connected", source: "tool_stream" })}\n\n`),
      );

      cleanup = addToolEventListener((event) => {
        try {
          controller.enqueue(
            encoder.encode(`data: ${JSON.stringify({ type: "tool_event", ...event as object })}\n\n`),
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
      if (cleanup) cleanup();
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
