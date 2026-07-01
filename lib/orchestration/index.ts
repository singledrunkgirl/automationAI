// ── Orchestration Layer — Public API ──

export { OrchestrationEngine } from "./engine";
export { getOrchestrator } from "./bootstrap";
export { AGENT_REGISTRY, getAgent, getAgentsByRole, getActiveAgents } from "./agents/registry";
export { TEAMS, getTeam } from "./teams/registry";

export type {
  AgentDefinition,
  AgentRole,
  TeamDefinition,
  TaskStep,
  OrchestrationTask,
  OrchestrationStatus,
  ExecutionMode,
} from "./types";
