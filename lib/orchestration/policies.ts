// ── Execution Policies ──
// Controls how aggressively the orchestrator executes tasks.

export type ExecutionPolicy = "safe" | "balanced" | "aggressive" | "autonomous";

export type ApprovalMode = "auto" | "ask_user" | "never_execute";

export interface ApprovalRule {
  toolId: string;
  mode: ApprovalMode;
  reason: string;
}

export interface PolicyConfig {
  policy: ExecutionPolicy;
  approvalRules: ApprovalRule[];
  maxParallelAgents: number;
  maxTaskDuration: number;    // seconds
  maxCostPerTask: number;     // USD
  requireHumanFor: string[];  // tool IDs that always need approval
}

export const POLICY_PRESETS: Record<ExecutionPolicy, PolicyConfig> = {
  safe: {
    policy: "safe",
    approvalRules: [
      { toolId: "desktop_execute", mode: "ask_user", reason: "Command execution requires review" },
      { toolId: "desktop_file_write", mode: "ask_user", reason: "File writes require review" },
      { toolId: "run_terminal_cmd", mode: "ask_user", reason: "Terminal commands require review" },
      { toolId: "playwright_click", mode: "ask_user", reason: "Browser interaction requires review" },
      { toolId: "desktop_file_read", mode: "auto", reason: "Read-only is safe" },
      { toolId: "file", mode: "auto", reason: "Sandbox file ops are constrained" },
    ],
    maxParallelAgents: 2,
    maxTaskDuration: 300,
    maxCostPerTask: 0.50,
    requireHumanFor: ["desktop_execute", "desktop_file_write", "run_terminal_cmd", "desktop_pty_create"],
  },

  balanced: {
    policy: "balanced",
    approvalRules: [
      { toolId: "desktop_execute", mode: "auto", reason: "Balanced: allow with monitoring" },
      { toolId: "desktop_file_write", mode: "auto", reason: "Balanced: allow with monitoring" },
      { toolId: "run_terminal_cmd", mode: "auto", reason: "Balanced: allow with monitoring" },
    ],
    maxParallelAgents: 4,
    maxTaskDuration: 600,
    maxCostPerTask: 2.00,
    requireHumanFor: ["desktop_pty_create"],
  },

  aggressive: {
    policy: "aggressive",
    approvalRules: [
      { toolId: "desktop_execute", mode: "auto", reason: "Aggressive: auto-execute all" },
      { toolId: "desktop_file_write", mode: "auto", reason: "Aggressive: auto-execute all" },
      { toolId: "run_terminal_cmd", mode: "auto", reason: "Aggressive: auto-execute all" },
    ],
    maxParallelAgents: 8,
    maxTaskDuration: 1200,
    maxCostPerTask: 5.00,
    requireHumanFor: [],
  },

  autonomous: {
    policy: "autonomous",
    approvalRules: [
      { toolId: "desktop_execute", mode: "auto", reason: "Autonomous: full auto" },
      { toolId: "desktop_file_write", mode: "auto", reason: "Autonomous: full auto" },
      { toolId: "run_terminal_cmd", mode: "auto", reason: "Autonomous: full auto" },
    ],
    maxParallelAgents: 16,
    maxTaskDuration: 3600,
    maxCostPerTask: 20.00,
    requireHumanFor: [],
  },
};

export function getPolicy(policy: ExecutionPolicy): PolicyConfig {
  return POLICY_PRESETS[policy];
}

export function requiresApproval(toolId: string, policy: PolicyConfig): boolean {
  const rule = policy.approvalRules.find((r) => r.toolId === toolId);
  if (!rule) return false;
  return rule.mode === "ask_user" || rule.mode === "never_execute";
}

export function isAllowed(toolId: string, policy: PolicyConfig): boolean {
  const rule = policy.approvalRules.find((r) => r.toolId === toolId);
  if (!rule) return true; // No rule → allowed
  return rule.mode !== "never_execute";
}
