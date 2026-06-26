import type { ChatMode } from "@/types";

const HWAI_DESKTOP_USER_AGENT_TOKEN = "HackWithAI-Desktop";

export const LEGACY_DESKTOP_AGENT_UPDATE_MESSAGE =
  "Agent mode now requires the latest HackWithAI v2 Desktop app. Please update HackWithAI v2 Desktop, then try again.";

export function isHackWithAIDesktopUserAgent(
  userAgent: string | null | undefined = getBrowserUserAgent(),
): boolean {
  return userAgent?.includes(HWAI_DESKTOP_USER_AGENT_TOKEN) ?? false;
}

export function isLegacyDesktopAgentClient({
  mode,
  isTauri,
  userAgent,
}: {
  mode: ChatMode | string;
  isTauri: boolean;
  userAgent?: string | null;
}): boolean {
  return (
    mode === "agent" && isTauri && !isHackWithAIDesktopUserAgent(userAgent)
  );
}

export function shouldUseAgentLongForAgent({
  mode,
  isTauri,
  userAgent,
}: {
  mode: ChatMode | string;
  subscription?: string | null;
  isTauri: boolean;
  userAgent?: string | null;
}): boolean {
  if (mode !== "agent") return false;
  if (process.env.NEXT_PUBLIC_ENABLE_AGENT_LONG !== "true") return false;

  return !isLegacyDesktopAgentClient({ mode, isTauri, userAgent });
}

function getBrowserUserAgent(): string {
  if (typeof navigator === "undefined") return "";
  return navigator.userAgent;
}
