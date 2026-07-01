// ── Team Definitions ──
// Pre-configured agent teams for common security workflows.
// All agents already exist in the Python ecosystem.

import type { TeamDefinition } from "../types";

export const TEAMS: TeamDefinition[] = [
  // ── Planning Team ──
  {
    id: "planning-team",
    name: "Planning Team",
    description: "Analyzes a target and produces a structured attack plan with phases, tools, and execution order.",
    agents: ["planner-agent", "optimizer-agent"],
    executionMode: "sequential",
    triggerDescription: "Triggered when a new security engagement begins. Produces the initial attack plan.",
  },

  // ── Reconnaissance Team ──
  {
    id: "recon-team",
    name: "Reconnaissance Team",
    description: "Gathers intelligence on targets. Runs network scans, web recon, OSINT collection.",
    agents: ["researcher-agent", "researcher-agent", "researcher-agent"],
    executionMode: "parallel",
    triggerDescription: "Triggered after planning. Runs multiple recon agents in parallel for speed.",
  },

  // ── Exploitation Team ──
  {
    id: "exploit-team",
    name: "Exploitation Team",
    description: "Develops and executes exploit code. Generates payloads, runs exploitation modules.",
    agents: ["coder-agent", "researcher-agent"],
    executionMode: "sequential",
    triggerDescription: "Triggered after reconnaissance identifies vulnerabilities.",
  },

  // ── Development Team ──
  {
    id: "dev-team",
    name: "Development Team",
    description: "Writes and tests security tools, scripts, and automation code.",
    agents: ["coder-agent", "coder-agent", "reviewer-agent"],
    executionMode: "sequential",
    triggerDescription: "Triggered for custom tool development or script generation.",
  },

  // ── Review Team ──
  {
    id: "review-team",
    name: "Review Team",
    description: "Reviews and validates outputs from other teams. Scores quality, detects errors.",
    agents: ["reviewer-agent", "critic-agent"],
    executionMode: "parallel",
    triggerDescription: "Triggered after any team produces output that needs validation.",
  },

  // ── Consensus Team ──
  {
    id: "consensus-team",
    name: "Consensus Team",
    description: "Runs debate and consensus when multiple agents disagree on approach.",
    agents: ["debate-engine", "consensus-engine"],
    executionMode: "debate",
    triggerDescription: "Triggered when agents produce conflicting recommendations.",
  },

  // ── Operations Team ──
  {
    id: "ops-team",
    name: "Operations Team",
    description: "Executes operational security tasks. Post-exploitation, persistence, cleanup.",
    agents: ["coder-agent", "researcher-agent"],
    executionMode: "sequential",
    triggerDescription: "Triggered for post-exploitation and persistence operations.",
  },

  // ── Full Pipeline ──
  {
    id: "full-pipeline",
    name: "Full Security Pipeline",
    description: "Complete end-to-end security engagement. Plan → Recon → Exploit → Review → Report.",
    agents: ["hermes-coordinator", "planner-agent", "researcher-agent", "coder-agent", "reviewer-agent", "critic-agent", "self-improvement"],
    executionMode: "sequential",
    triggerDescription: "Triggered by 'full audit' or 'complete penetration test' requests.",
  },
];

export function getTeam(id: string): TeamDefinition | undefined {
  return TEAMS.find((t) => t.id === id);
}

export function getTeamNames(): string[] {
  return TEAMS.map((t) => t.name);
}
