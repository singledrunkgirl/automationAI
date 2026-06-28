import { NextResponse } from "next/server";

export interface ToolEvent {
  source: string;
  message: string;
  timestamp: string;
}

const eventStore: ToolEvent[] = [];
const MAX_EVENTS = 500;
const listeners = new Set<(event: ToolEvent) => void>();

export function addToolEventListener(fn: (event: ToolEvent) => void) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function pushToolEvent(event: ToolEvent) {
  eventStore.push(event);
  if (eventStore.length > MAX_EVENTS) eventStore.shift();

  for (const listener of listeners) {
    try {
      listener(event);
    } catch {
      // ignore listener errors
    }
  }
}

export function getRecentToolEvents(count = 100) {
  return eventStore.slice(-count);
}

export function createEventStreamResponse(events: ToolEvent[]) {
  const encoder = new TextEncoder();
  let cleanup: (() => void) | null = null;

  const stream = new ReadableStream({
    start(controller) {
      // Send existing events
      for (const event of events) {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
      }

      // Listen for new events
      cleanup = addToolEventListener((event) => {
        try {
          controller.enqueue(encoder.encode(`data: ${JSON.stringify(event)}\n\n`));
        } catch {
          // controller closed
        }
      });
    },
    cancel() {
      cleanup?.();
    },
  });

  return new NextResponse(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}

