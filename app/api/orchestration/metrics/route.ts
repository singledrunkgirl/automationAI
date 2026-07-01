// ── Orchestration Metrics API ──
// GET /api/orchestration/metrics → agent + task metrics

import { NextResponse } from "next/server";
import { getOrchestrator } from "@/lib/orchestration/bootstrap";

export async function GET() {
  try {
    const engine = getOrchestrator();
    const collector = engine.getCollector();
    const status = engine.status();
    const policy = engine.getPolicy();

    return NextResponse.json({
      agents: collector.getAgentMetrics(),
      tasks: collector.getTaskMetrics().slice(-20),
      overview: {
        totalTasks: status.completedTasks + status.failedTasks + status.activeTasks,
        completedTasks: status.completedTasks,
        failedTasks: status.failedTasks,
        activeTasks: status.activeTasks,
        uptime: status.uptime,
      },
      policies: policy,
    });
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : "Internal error" });
  }
}
