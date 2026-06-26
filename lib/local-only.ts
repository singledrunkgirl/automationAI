export const LOCAL_ONLY_USER_ID = "local-kali-user";

export function isLocalOnlyMode(): boolean {
  return (
    process.env.LOCAL_ONLY_MODE === "true" ||
    process.env.NEXT_PUBLIC_LOCAL_ONLY_MODE === "true"
  );
}

export function isLocalOnlyModeClient(): boolean {
  return process.env.NEXT_PUBLIC_LOCAL_ONLY_MODE === "true";
}
