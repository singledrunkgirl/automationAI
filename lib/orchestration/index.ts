// ── Orchestration Layer — Public API ──

export { OrchestrationEngine } from "./engine";
export { getOrchestrator } from "./bootstrap";
export { AGENT_REGISTRY, getAgent, getAgentsByRole, getActiveAgents } from "./agents/registry";
export { TEAMS, getTeam } from "./teams/registry";

// Policies
export { getPolicy, requiresApproval, isAllowed, POLICY_PRESETS } from "./policies";
export type { ExecutionPolicy, ApprovalMode, PolicyConfig, ApprovalRule } from "./policies";

// Router
export { routeModel, estimateCost } from "./router";
export type { RoutingContext, RouteDecision } from "./router";

// Recovery
export { executeWithRecovery } from "./recovery";
export type { RecoveryConfig, RecoveryResult } from "./recovery";

// Observability
export { ObservabilityCollector } from "./observability";
export type {
  StepMetrics, TaskMetrics, AgentMetrics,
  ObservabilitySnapshot, ExecutionGraphNode,
} from "./observability";

export type {
  AgentDefinition, AgentRole, TeamDefinition,
  TaskStep, OrchestrationTask, OrchestrationStatus, ExecutionMode,
} from "./types";
