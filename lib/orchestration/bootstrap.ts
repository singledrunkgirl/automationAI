// ── Orchestration Bootstrap ──

import { OrchestrationEngine } from "./engine";

let _engine: OrchestrationEngine | null = null;

export function getOrchestrator(): OrchestrationEngine {
  if (!_engine) {
    _engine = new OrchestrationEngine();
  }
  return _engine;
}
