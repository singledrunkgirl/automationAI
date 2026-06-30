const LOCAL_ORIGINS = new Set(["localhost", "127.0.0.1", "[::1]", "[::1]:"]);

export function isLocalOrigin(requestUrl: string | URL): boolean {
  let hostname: string;
  try {
    const url = typeof requestUrl === "string" ? new URL(requestUrl) : requestUrl;
    hostname = url.hostname.toLowerCase();
  } catch {
    return false;
  }
  return LOCAL_ORIGINS.has(hostname) || hostname.startsWith("[::1]");
}

export function isSecureOrigin(requestUrl?: string | URL): boolean {
  if (!requestUrl) return false;
  try {
    const url = typeof requestUrl === "string" ? new URL(requestUrl) : requestUrl;
    return url.protocol === "https:";
  } catch {
    return false;
  }
}

export function shouldUseSecureCookie(requestUrl?: string | URL): boolean {
  if (!requestUrl) return false;
  if (isSecureOrigin(requestUrl)) return true;
  if (isLocalOrigin(requestUrl)) return false;
  return isSecureOrigin(requestUrl);
}

export function cookieSecurityOptions(requestUrl?: string | URL) {
  return {
    secure: shouldUseSecureCookie(requestUrl),
    httpOnly: true as const,
    sameSite: "lax" as const,
  };
}
