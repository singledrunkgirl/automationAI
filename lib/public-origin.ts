export function getPublicOrigin(requestUrl?: string): string {
  const configuredBaseUrl = process.env.NEXT_PUBLIC_BASE_URL;
  if (configuredBaseUrl) {
    try {
      return new URL(configuredBaseUrl).origin;
    } catch {
      console.warn("[Public Origin] Invalid NEXT_PUBLIC_BASE_URL");
    }
  }

  if (requestUrl) {
    return new URL(requestUrl).origin;
  }

  return "http://localhost:3000";
}
