// In-memory event store shared with SSE consumers
const eventStore: Array<{ source: string; message: string; timestamp: string }> = [];
const MAX_EVENTS = 500;
const listeners = new Set<(event: unknown) => void>();

export function addToolEventListener(fn: (event: unknown) => void) {
  listeners.add(fn);
  return () => listeners.delete(fn);
}

export function pushToolEvent(event: { source: string; message: string; timestamp: string }) {
  eventStore.push(event);
  if (eventStore.length > MAX_EVENTS) eventStore.shift();
  for (const listener of listeners) {
    try { listener(event); } catch {}
  }
}

export function getRecentToolEvents(count = 100) {
  return eventStore.slice(-count);
}

export function getToolEventTotal() {
  return eventStore.length;
}
