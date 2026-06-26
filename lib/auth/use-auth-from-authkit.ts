"use client";

import { useCallback, useEffect, useRef, useMemo, useState } from "react";
import { useAuth, useAccessToken } from "@workos-inc/authkit-nextjs/components";
import { CrossTabMutex } from "@/lib/auth/cross-tab-mutex";
import {
  clearExpiredSharedToken,
  getFreshSharedTokenWithFallback,
  TOKEN_FRESHNESS_MS,
} from "@/lib/auth/shared-token";
import { isCrossTabTokenSharingEnabled } from "@/lib/auth/feature-flags";

// Singleton mutex shared across all hook instances in this tab
const refreshMutex = new CrossTabMutex({
  lockKey: "hwai-token-refresh",
  lockTimeoutMs: 15000,
  onLog: (msg) => console.log(`[Convex Auth] ${msg}`),
});

const TOKEN_FETCH_TIMEOUT_MS = 7000;
const AUTH_LOADING_MAX_MS = 8000;

async function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
): Promise<T | null> {
  return await Promise.race([
    promise,
    new Promise<null>((resolve) => setTimeout(() => resolve(null), timeoutMs)),
  ]);
}

export function useSharedTokenCleanup(enabled: boolean): void {
  useEffect(() => {
    if (!enabled) return;
    const interval = setInterval(clearExpiredSharedToken, TOKEN_FRESHNESS_MS);
    return () => clearInterval(interval);
  }, [enabled]);
}

export type ConvexAuthState = {
  isLoading: boolean;
  isAuthenticated: boolean;
  fetchAccessToken: (args?: {
    forceRefreshToken?: boolean;
  }) => Promise<string | null>;
};

export type AuthKitDeps = {
  useAuth: typeof useAuth;
  useAccessToken: typeof useAccessToken;
  mutex: CrossTabMutex;
  isCrossTabEnabled?: (userId: string | undefined) => boolean;
};

const defaultDeps: AuthKitDeps = {
  useAuth,
  useAccessToken,
  mutex: refreshMutex,
  isCrossTabEnabled: isCrossTabTokenSharingEnabled,
};

export function useAuthFromAuthKit(
  deps: AuthKitDeps = defaultDeps,
): ConvexAuthState {
  const {
    user,
    loading: isLoading,
    organizationId,
    refreshAuth,
  } = deps.useAuth();
  const { getAccessToken, accessToken, refresh } = deps.useAccessToken();
  const accessTokenRef = useRef<string | undefined>(undefined);
  const lastRefreshErrorAt = useRef<number>(0);
  const hasResolvedOrgRef = useRef(false);
  const [loadingTimedOut, setLoadingTimedOut] = useState(false);

  const isCrossTabEnabled = useMemo(
    () => (deps.isCrossTabEnabled ?? isCrossTabTokenSharingEnabled)(user?.id),
    [deps.isCrossTabEnabled, user?.id],
  );
  useSharedTokenCleanup(isCrossTabEnabled);

  // Eagerly ensure session is scoped to the user's organization so JWTs
  // include entitlements (e.g. "pro-plus-plan"). Running this in an effect
  // (rather than inside fetchAccessToken) avoids a mid-auth-flow state
  // change that would cause Convex to briefly flip isLoading back to true,
  // producing a visible loading-screen flash.
  useEffect(() => {
    if (organizationId && !hasResolvedOrgRef.current && refreshAuth) {
      refreshAuth({ organizationId })
        .then(() => {
          hasResolvedOrgRef.current = true;
        })
        .catch(() => {
          // Non-fatal: the token may still include entitlements if the
          // session was already org-scoped.
        });
    }
  }, [organizationId, refreshAuth]);

  useEffect(() => {
    accessTokenRef.current = accessToken;
  }, [accessToken]);

  useEffect(() => {
    if (!isLoading) {
      // Reset timeout state asynchronously to satisfy `set-state-in-effect`.
      const resetTimer = setTimeout(() => setLoadingTimedOut(false), 0);
      return () => clearTimeout(resetTimer);
    }

    const timer = setTimeout(() => {
      setLoadingTimedOut(true);
      console.warn(
        `[Convex Auth] Auth loading exceeded ${AUTH_LOADING_MAX_MS}ms; forcing loading=false fallback`,
      );
    }, AUTH_LOADING_MAX_MS);

    return () => clearTimeout(timer);
  }, [isLoading]);

  const isAuthenticated = !!user;

  const fetchAccessToken = useCallback(
    async ({
      forceRefreshToken,
    }: { forceRefreshToken?: boolean } = {}): Promise<string | null> => {
      if (!user) {
        return null;
      }

      try {
        if (forceRefreshToken) {
          // Cooldown: skip refresh if we recently hit an error (e.g., rate limit)
          // to prevent Convex retry loops from hammering the server
          const REFRESH_COOLDOWN_MS = 10_000;
          if (Date.now() - lastRefreshErrorAt.current < REFRESH_COOLDOWN_MS) {
            console.log(
              "[Convex Auth] Skipping refresh during cooldown, using cached token",
            );
            return accessTokenRef.current ?? null;
          }

          // Use new cross-tab coordination if feature flag is enabled
          if (isCrossTabEnabled) {
            // Convex is asking for a fresh token (current one was rejected).
            // Coordinate refresh across tabs to avoid redundant API calls.
            const refreshWithLock = async () => {
              const token = await deps.mutex.withLock(async () => {
                // Double-check after acquiring lock - another tab may have refreshed while we waited
                return getFreshSharedTokenWithFallback(async () =>
                  withTimeout(refresh(), TOKEN_FETCH_TIMEOUT_MS),
                );
              });
              // If lock timed out, fall back to getAccessToken
              return (
                token ??
                (await getFreshSharedTokenWithFallback(async () =>
                  withTimeout(getAccessToken(), TOKEN_FETCH_TIMEOUT_MS),
                ))
              );
            };

            return getFreshSharedTokenWithFallback(refreshWithLock);
          }

          // Legacy behavior: direct refresh without cross-tab coordination
          const newToken = await withTimeout(refresh(), TOKEN_FETCH_TIMEOUT_MS);
          return newToken ?? null;
        }
        return (
          (await withTimeout(getAccessToken(), TOKEN_FETCH_TIMEOUT_MS)) ?? null
        );
      } catch {
        // On network errors during laptop wake, fall back to cached token.
        // Even if expired, Convex will treat it like null and clear auth.
        // AuthKit's tokenStore schedules automatic retries in the background.
        lastRefreshErrorAt.current = Date.now();
        console.log("[Convex Auth] Using cached token during network issues");
        return accessTokenRef.current ?? null;
      }
    },
    [user, getAccessToken, refresh, deps.mutex, isCrossTabEnabled],
  );

  return {
    isLoading: isLoading && !loadingTimedOut,
    isAuthenticated,
    fetchAccessToken,
  };
}
