// ── Orchestration API ──
// GET  /api/orchestration          → status
// POST /api/orchestration          → execute task
// GET  /api/orchestration?task=id  → task status
// POST /api/orchestration/execute  → execute (alias)

import { NextRequest, NextResponse } from "next/server";
import { getOrchestrator } from "@/lib/orchestration/bootstrap";

export async function GET(request: NextRequest) {
  const engine = getOrchestrator();
  const taskId = request.nextUrl.searchParams.get("task");

  if (taskId) {
    const task = engine.getTask(taskId);
    if (!task) {
      return NextResponse.json({ error: "Task not found" }, { status: 404 });
    }
    return NextResponse.json(task);
  }

  return NextResponse.json(engine.status());
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  const { description, teamId } = body as { description?: string; teamId?: string };

  if (!description || !teamId) {
    return NextResponse.json(
      { error: "Required: description, teamId" },
      { status: 400 },
    );
  }

  const engine = getOrchestrator();
  const task = await engine.execute(description, teamId);

  return NextResponse.json(task);
}
