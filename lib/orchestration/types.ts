// ── Agent Types ──
// Shared types for the orchestration layer.

export type AgentRole =
  | "planner"
  | "researcher"
  | "coder"
  | "reviewer"
  | "critic"
  | "consensus"
  | "debate"
  | "optimizer"
  | "self_improvement"
  | "orchestrator";

export type ExecutionMode = "sequential" | "parallel" | "debate" | "consensus";

export interface AgentDefinition {
  id: string;
  name: string;
  role: AgentRole;
  description: string;
  capabilities: string[];
  supportedTools: string[];
  supportedModels: string[];
  executionMode: ExecutionMode;
  timeout: number;          // seconds
  costClass: "cheap" | "standard" | "expensive";
  dependencies: string[];   // agent IDs this agent depends on
  pythonModule: string;     // Python module that implements this agent
  active: boolean;
}

export interface TeamDefinition {
  id: string;
  name: string;
  description: string;
  agents: string[];         // agent IDs
  executionMode: ExecutionMode;
  triggerDescription: string;
}

export interface TaskStep {
  id: string;
  taskId: string;
  agentId: string;
  teamId: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  input: string;
  output?: string;
  toolsUsed: string[];
  startedAt?: number;
  completedAt?: number;
  error?: string;
}

export interface OrchestrationTask {
  id: string;
  description: string;
  teamId: string;
  status: "planning" | "running" | "debating" | "reviewing" | "completed" | "failed";
  steps: TaskStep[];
  createdAt: number;
  completedAt?: number;
  finalOutput?: string;
}

export interface OrchestrationStatus {
  activeTasks: number;
  completedTasks: number;
  failedTasks: number;
  currentTask?: OrchestrationTask;
  teamsAvailable: string[];
  agentsAvailable: string[];
  uptime: number;
}
