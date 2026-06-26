export const OPENROUTER_APP_REFERER = "https://localhost:3006";
export const OPENROUTER_APP_TITLE = "HackWithAI v2";
export const OPENROUTER_APP_CATEGORIES = "cloud-agent,cli-agent";

export const openrouterAttributionHeaders = {
  "HTTP-Referer": OPENROUTER_APP_REFERER,
  "X-OpenRouter-Title": OPENROUTER_APP_TITLE,
  "X-OpenRouter-Categories": OPENROUTER_APP_CATEGORIES,
} as const;
