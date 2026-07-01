// ── Failure Recovery ──
// Handles retries, fallbacks, timeouts, and partial completion.

import type { TaskStep } from "./types";
import type { RouteDecision } from "./router";

export interface RecoveryConfig {
  maxRetries: number;
  retryDelay: number;        // ms
  timeoutMs: number;          // ms
  fallbackEnabled: boolean;
  allowPartialCompletion: boolean;
}

export interface RecoveryResult {
  success: boolean;
  output?: string;
  error?: string;
  retriesUsed: number;
  fallbackUsed: boolean;
  duration: number;
}

const DEFAULT_RECOVERY: RecoveryConfig = {
  maxRetries: 2,
  retryDelay: 1000,
  timeoutMs: 300000,
  fallbackEnabled: true,
  allowPartialCompletion: true,
};

export async function executeWithRecovery(
  step: TaskStep,
  primaryFn: () => Promise<string>,
  fallbackFn: () => Promise<string>,
  route: RouteDecision,
  config: Partial<RecoveryConfig> = {},
): Promise<RecoveryResult> {
  const cfg = { ...DEFAULT_RECOVERY, ...config };
  const startTime = Date.now();
  let retriesUsed = 0;
  let fallbackUsed = false;

  // Primary attempt with retries
  for (let attempt = 0; attempt <= cfg.maxRetries; attempt++) {
    try {
      // Timeout wrapper
      const output = await withTimeout(primaryFn(), cfg.timeoutMs);
      return {
        success: true,
        output,
        retriesUsed,
        fallbackUsed,
        duration: Date.now() - startTime,
      };
    } catch (e) {
      retriesUsed = attempt + 1;
      const error = e instanceof Error ? e.message : String(e);

      // Don't retry on certain errors
      if (isPermanentError(error)) break;

      // Retry delay
      if (attempt < cfg.maxRetries) {
        await sleep(cfg.retryDelay * (attempt + 1));
      }
    }
  }

  // Fallback to alternative model/provider
  if (cfg.fallbackEnabled && route.fallbackModel) {
    fallbackUsed = true;
    try {
      const output = await withTimeout(fallbackFn(), cfg.timeoutMs);
      return {
        success: true,
        output,
        retriesUsed,
        fallbackUsed,
        duration: Date.now() - startTime,
      };
    } catch {
      // Fallback also failed
    }
  }

  // Partial completion
  if (cfg.allowPartialCompletion) {
    return {
      success: false,
      error: `Failed after ${retriesUsed} retries${fallbackUsed ? " + fallback" : ""}`,
      retriesUsed,
      fallbackUsed,
      duration: Date.now() - startTime,
    };
  }

  throw new Error(`Step failed after ${retriesUsed} retries${fallbackUsed ? " + fallback" : ""}`);
}

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`Timeout after ${ms}ms`)), ms);
    promise.then(
      (v) => { clearTimeout(timer); resolve(v); },
      (e) => { clearTimeout(timer); reject(e); },
    );
  });
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

function isPermanentError(error: string): boolean {
  const permanent = [
    "not found",
    "unauthorized",
    "forbidden",
    "invalid",
    "not available",
    "Desktop worker not available",
  ];
  return permanent.some((p) => error.toLowerCase().includes(p));
}
