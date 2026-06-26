import type { SubscriptionTier } from "@/types/chat";

export const MODEL_ACCESS_STORAGE_KEY = "hwai:model-access-code";
export const MODEL_ACCESS_GRANTED_EVENT = "hwai:model-access-granted";

const DEFAULT_MODEL_ACCESS_CODES = [
  "QR-MODEL-2026",
  "QR-ADMIN-ACCESS",
  "3210-3002",
];

function normalizeCode(code: string | null | undefined): string {
  return (code ?? "").trim().toUpperCase();
}

function parseCodes(value: string | null | undefined): string[] {
  return (value ?? "").split(",").map(normalizeCode).filter(Boolean);
}

export function getConfiguredModelAccessCodes(): string[] {
  const configuredCodes = parseCodes(
    process.env.MODEL_ACCESS_CODES ??
      process.env.NEXT_PUBLIC_MODEL_ACCESS_CODES,
  );

  return configuredCodes.length > 0
    ? configuredCodes
    : DEFAULT_MODEL_ACCESS_CODES;
}

export function isModelAccessCodeValid(
  code: string | null | undefined,
): boolean {
  const normalized = normalizeCode(code);
  if (!normalized) return false;

  return getConfiguredModelAccessCodes().includes(normalized);
}

export function readStoredModelAccessCode(): string | undefined {
  if (typeof window === "undefined") return undefined;
  const code = window.localStorage.getItem(MODEL_ACCESS_STORAGE_KEY);
  return isModelAccessCodeValid(code) ? normalizeCode(code) : undefined;
}

export function storeModelAccessCode(code: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(MODEL_ACCESS_STORAGE_KEY, normalizeCode(code));
  window.dispatchEvent(new Event(MODEL_ACCESS_GRANTED_EVENT));
}

export function hasStoredModelAccess(): boolean {
  return Boolean(readStoredModelAccessCode());
}

export function getEffectiveSubscriptionForModelAccess({
  subscription,
  modelAccessCode,
}: {
  subscription: SubscriptionTier;
  modelAccessCode?: string;
}): SubscriptionTier {
  if (subscription !== "free") return subscription;
  return isModelAccessCodeValid(modelAccessCode) ? "pro" : subscription;
}
