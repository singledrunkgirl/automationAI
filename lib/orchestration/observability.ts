// ── Observability & Metrics ──
// Tracks every execution for monitoring, cost analysis, and debugging.

import type { OrchestrationTask, TaskStep } from "./types";
import type { RouteDecision } from "./router";

export interface StepMetrics {
  taskId: string;
  stepId: string;
  agentId: string;
  provider: string;
  model: string;
  status: "completed" | "failed" | "skipped";
  duration: number;         // ms
  retries: number;
  fallbackUsed: boolean;
  tokensUsed: number;
  estimatedCost: number;
  error?: string;
}

export interface TaskMetrics {
  taskId: string;
  description: string;
  teamId: string;
  status: string;
  totalDuration: number;    // ms
  stepCount: number;
  successCount: number;
  failureCount: number;
  totalCost: number;
  totalTokens: number;
  policies: string;
  createdAt: number;
  completedAt?: number;
}

export interface AgentMetrics {
  agentId: string;
  name: string;
  role: string;
  successRate: number;       // 0-1
  failureRate: number;
  averageDuration: number;   // ms
  averageCost: number;       // USD
  totalExecutions: number;
  totalRetries: number;
  lastExecutedAt?: number;
}

export interface ObservabilitySnapshot {
  timestamp: number;
  activeTask?: OrchestrationTask;
  currentAgent?: string;
  currentModel?: string;
  currentProvider?: string;
  currentTool?: string;
  tokenUsage: number;
  costEstimate: number;
  recentSteps: StepMetrics[];
  executionGraph: ExecutionGraphNode[];
}

export interface ExecutionGraphNode {
  id: string;
  agent: string;
  status: string;
  duration: number;
  children: ExecutionGraphNode[];
}

export class ObservabilityCollector {
  private stepMetrics: StepMetrics[] = [];
  private taskMetrics: TaskMetrics[] = [];
  private agentStats = new Map<string, AgentMetrics>();
  private totalTokens = 0;
  private totalCost = 0;

  recordStep(step: TaskStep, route: RouteDecision, metrics: { duration: number; retries: number; fallbackUsed: boolean; tokensUsed: number; error?: string }): void {
    const m: StepMetrics = {
      taskId: step.taskId,
      stepId: step.id,
      agentId: step.agentId,
      provider: route.provider,
      model: route.model,
      status: step.status === "completed" ? "completed" : "failed",
      duration: metrics.duration,
      retries: metrics.retries,
      fallbackUsed: metrics.fallbackUsed,
      tokensUsed: metrics.tokensUsed,
      estimatedCost: route.estimatedCost,
      error: metrics.error || step.error,
    };
    this.stepMetrics.push(m);
    this.totalTokens += metrics.tokensUsed;
    this.totalCost += route.estimatedCost;
  }

  recordTask(task: OrchestrationTask): void {
    const completed = task.steps.filter((s) => s.status === "completed");
    const failed = task.steps.filter((s) => s.status === "failed");
    const duration = (task.completedAt || Date.now()) - task.createdAt;

    this.taskMetrics.push({
      taskId: task.id,
      description: task.description,
      teamId: task.teamId,
      status: task.status,
      totalDuration: duration,
      stepCount: task.steps.length,
      successCount: completed.length,
      failureCount: failed.length,
      totalCost: this.stepMetrics.filter((s) => s.taskId === task.id).reduce((sum, s) => sum + s.estimatedCost, 0),
      totalTokens: 0,
      policies: "balanced",
      createdAt: task.createdAt,
      completedAt: task.completedAt,
    });
  }

  updateAgentStats(agentId: string, success: boolean, duration: number, cost: number): void {
    let stats = this.agentStats.get(agentId);
    if (!stats) {
      stats = {
        agentId,
        name: agentId,
        role: "unknown",
        successRate: 0,
        failureRate: 0,
        averageDuration: 0,
        averageCost: 0,
        totalExecutions: 0,
        totalRetries: 0,
      };
      this.agentStats.set(agentId, stats);
    }
    stats.totalExecutions++;
    if (success) {
      stats.successRate = ((stats.successRate * (stats.totalExecutions - 1)) + 1) / stats.totalExecutions;
    }
    stats.failureRate = 1 - stats.successRate;
    stats.averageDuration = ((stats.averageDuration * (stats.totalExecutions - 1)) + duration) / stats.totalExecutions;
    stats.averageCost = ((stats.averageCost * (stats.totalExecutions - 1)) + cost) / stats.totalExecutions;
    stats.lastExecutedAt = Date.now();
  }

  snapshot(task?: OrchestrationTask): ObservabilitySnapshot {
    return {
      timestamp: Date.now(),
      activeTask: task,
      currentAgent: task?.steps.find((s) => s.status === "running")?.agentId,
      currentModel: undefined,
      currentProvider: undefined,
      currentTool: undefined,
      tokenUsage: this.totalTokens,
      costEstimate: this.totalCost,
      recentSteps: this.stepMetrics.slice(-10),
      executionGraph: this.buildGraph(task),
    };
  }

  getAgentMetrics(): AgentMetrics[] {
    return Array.from(this.agentStats.values());
  }

  getTaskMetrics(): TaskMetrics[] {
    return this.taskMetrics;
  }

  private buildGraph(task?: OrchestrationTask): ExecutionGraphNode[] {
    if (!task) return [];
    return task.steps.map((s) => ({
      id: s.id,
      agent: s.agentId,
      status: s.status,
      duration: (s.completedAt || Date.now()) - (s.startedAt || Date.now()),
      children: [],
    }));
  }
}
