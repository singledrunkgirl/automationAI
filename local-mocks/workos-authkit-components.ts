"use client";

/**
 * Runtime mock for `@workos-inc/authkit-nextjs/components` used in LOCAL_ONLY_MODE.
 * Provides a fake WorkOS auth context so the app runs without WorkOS credentials.
 */

import React, { createContext, useContext, ReactNode, useCallback } from "react";

// ── Mock user ─────────────────────────────────────────────────────────────
const MOCK_USER = {
  id: "local-kali-user",
  email: "local@hackwithai.local",
  firstName: "Local",
  lastName: "User",
};

// ── Auth context ──────────────────────────────────────────────────────────
type AuthContextValue = {
  user: typeof MOCK_USER | null;
  entitlements: string[];
  loading: boolean;
  organizationId?: string;
  refreshAuth: ((opts?: { organizationId?: string }) => Promise<void>) | null;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue>({
  user: MOCK_USER,
  entitlements: ["ent_pro"],
  loading: false,
  organizationId: "org_local",
  refreshAuth: null,
  signOut: async () => {},
});

// ── AuthKitProvider ───────────────────────────────────────────────────────
export function AuthKitProvider({
  children,
}: {
  children: ReactNode;
  onSessionExpired?: () => void;
}) {
  return (
    <AuthContext.Provider
      value={{
        user: MOCK_USER,
        entitlements: ["ent_pro"],
        loading: false,
        organizationId: "org_local",
        refreshAuth: null,
        signOut: async () => {},
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ── useAuth hook ──────────────────────────────────────────────────────────
export function useAuth() {
  return {
    user: MOCK_USER,
    entitlements: ["ent_pro"],
    loading: false,
    organizationId: "org_local",
    refreshAuth: null,
    signOut: async () => {},
    isAuthenticated: true,
  };
}

// ── useAccessToken hook ───────────────────────────────────────────────────
export function useAccessToken() {
  return {
    getAccessToken: async () => "mock-access-token",
    accessToken: "mock-access-token",
    refresh: async () => "mock-access-token",
  };
}

// ── Default export ────────────────────────────────────────────────────────
const WorkosAuthComponents = {
  AuthKitProvider,
  useAuth,
  useAccessToken,
};

export default WorkosAuthComponents;
