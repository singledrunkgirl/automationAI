// ── Dynamic Model Router ──
// Selects optimal AI provider/model based on task characteristics.
// Reuses existing providers from lib/ai/providers.ts.

import type { AgentDefinition } from "./types";

export interface RoutingContext {
  taskComplexity: "low" | "medium" | "high" | "critical";
  estimatedTokens: number;
  needsVision: boolean;
  needsToolCalling: boolean;
  needsStreaming: boolean;
  budget: "minimal" | "standard" | "premium";
  latency: "low" | "normal" | "batch";
}

export interface RouteDecision {
  provider: string;
  model: string;
  fallbackModel?: string;
  fallbackProvider?: string;
  estimatedCost: number;
  maxRetries: number;
  reasoning: string;
}

const COST_PER_1K = {
  "openai/gpt-4o": { input: 0.005, output: 0.015 },
  "openai/gpt-4o-mini": { input: 0.00015, output: 0.0006 },
  "anthropic/claude-sonnet-4-20250514": { input: 0.003, output: 0.015 },
  "anthropic/claude-3.5-sonnet": { input: 0.003, output: 0.015 },
  "google/gemini-2.5-flash": { input: 0.00015, output: 0.0006 },
  "google/gemini-2.5-pro": { input: 0.00125, output: 0.005 },
};

export function routeModel(
  agent: AgentDefinition,
  context: RoutingContext,
): RouteDecision {
  const models = agent.supportedModels.length > 0
    ? agent.supportedModels
    : ["openai/gpt-4o"];

  const primary = models[0];
  const fallback = models.length > 1 ? models[1] : "openai/gpt-4o-mini";

  // Determine provider from model ID
  const provider = primary.includes("anthropic") ? "anthropic"
    : primary.includes("google") || primary.includes("gemini") ? "gemini"
    : "openrouter";

  const fallbackProvider = fallback.includes("anthropic") ? "anthropic"
    : fallback.includes("google") || fallback.includes("gemini") ? "gemini"
    : "openrouter";

  // Cost estimate
  const costData = COST_PER_1K[primary as keyof typeof COST_PER_1K] || COST_PER_1K["openai/gpt-4o"];
  const estimatedCost = ((context.estimatedTokens / 1000) * costData.input * 1.5);

  // Retry logic based on complexity
  const maxRetries = context.taskComplexity === "critical" ? 3
    : context.taskComplexity === "high" ? 2
    : 1;

  // Routing decision
  let reasoning = `Selected ${primary} (${provider}) for ${agent.name}`;

  // Budget optimization
  if (context.budget === "minimal" && costData.input > 0.001) {
    reasoning += ` — budget constrained, consider ${fallback}`;
  }

  // Latency optimization
  if (context.latency === "low" && primary.includes("claude")) {
    reasoning += " — Claude selected for fast response";
  }

  return {
    provider,
    model: primary,
    fallbackModel: fallback,
    fallbackProvider,
    estimatedCost,
    maxRetries,
    reasoning,
  };
}

export function estimateCost(modelId: string, inputTokens: number, outputTokens: number): number {
  const cost = COST_PER_1K[modelId as keyof typeof COST_PER_1K];
  if (!cost) return (inputTokens / 1000) * 0.005 + (outputTokens / 1000) * 0.015;
  return (inputTokens / 1000) * cost.input + (outputTokens / 1000) * cost.output;
}
