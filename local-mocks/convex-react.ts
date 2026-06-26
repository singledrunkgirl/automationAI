"use client";

/**
 * Runtime mock for `convex/react` used in LOCAL_ONLY_MODE.
 * Provides localStorage-backed persistence for chats and messages.
 */

import React, { createContext, useContext, ReactNode, useCallback } from "react";
import {
  getStoredChats,
  upsertStoredChat,
  deleteStoredChat,
  getStoredMessages,
  appendStoredMessage,
} from "@/lib/utils/client-storage";

// ── Mock Convex auth context ──────────────────────────────────────────────
type ConvexAuthState = "authenticated" | "unauthenticated" | "loading";

const MockConvexAuthCtx = createContext<ConvexAuthState>("authenticated") as any;

export function ConvexAuthProvider({ children }: { children: ReactNode }) {
  return (
    <MockConvexAuthCtx.Provider value="authenticated">
      {children}
    </MockConvexAuthCtx.Provider>
  );
}

// ── ConvexReactClient ─────────────────────────────────────────────────────
export class ConvexReactClient {
  constructor(_url: string) {
    // no-op
  }
}

// ── Auth components ───────────────────────────────────────────────────────
export function Authenticated({ children }: { children: ReactNode }) {
  const state = useContext(MockConvexAuthCtx);
  if (state !== "authenticated") return null;
  return <>{children}</>;
}

export function Unauthenticated({ children }: { children: ReactNode }) {
  const state = useContext(MockConvexAuthCtx);
  if (state !== "unauthenticated") return null;
  return <>{children}</>;
}

export function AuthLoading({ children }: { children: ReactNode }) {
  const state = useContext(MockConvexAuthCtx);
  if (state !== "loading") return null;
  return <>{children}</>;
}

// ── Mock hooks (localStorage-backed) ──────────────────────────────────────
export function useQuery(_query: unknown, args?: Record<string, unknown>) {
  // Return a chat by ID if args has an id field
  if (args && typeof args.id === "string") {
    const chats = getStoredChats();
    const chat = chats.find((c) => c.id === args.id);
    return chat ?? null;
  }
  return undefined;
}

export function useMutation(_mutation: unknown) {
  const mutate = useCallback(async (args?: Record<string, unknown>) => {
    if (!args) return undefined;
    // Persist chat saves
    if ("id" in args && "title" in args && typeof args.id === "string") {
      upsertStoredChat({
        _id: args.id as string,
        id: args.id as string,
        title: (args.title as string) || "New Chat",
        update_time: Date.now(),
        user_id: args.userId as string | undefined,
      });
    }
    // Persist message saves
    if ("chatId" in args && "role" in args && "parts" in args) {
      appendStoredMessage(args.chatId as string, {
        _id: (args.id as string) || "",
        id: (args.id as string) || "",
        chatId: args.chatId as string,
        role: args.role as string,
        parts: (args.parts as unknown[]) || [],
        content: args.content as string | undefined,
        update_time: Date.now(),
        model: args.model as string | undefined,
        mode: args.mode as string | undefined,
        finish_reason: args.finish_reason as string | undefined,
        usage: args.usage,
      });
    }
    return undefined;
  }, []);
  return mutate;
}

export function useAction() {
  return async () => {};
}

export function useConvex() {
  return {
    query: async () => undefined,
    mutation: async (args?: Record<string, unknown>) => {
      // Re-use same persistence logic for direct Convex client calls
      if (!args) return undefined;
      if ("id" in args && "title" in args && typeof args.id === "string") {
        upsertStoredChat({
          _id: args.id as string,
          id: args.id as string,
          title: (args.title as string) || "New Chat",
          update_time: Date.now(),
        });
      }
      return undefined;
    },
    action: async () => undefined,
  };
}

export function usePaginatedQuery(_query: unknown, args?: Record<string, unknown> | "skip") {
  if (args === "skip") {
    return {
      results: [] as unknown[],
      status: "Exhausted" as const,
      loadMore: () => {},
      isLoading: false,
    };
  }
  // If args has chatId, return messages for that chat
  if (args && typeof args === "object" && "chatId" in args) {
    const messages = getStoredMessages(args.chatId as string);
    return {
      results: messages,
      status: "Exhausted" as const,
      loadMore: () => {},
      isLoading: false,
    };
  }
  // Otherwise return all stored chats (for sidebar)
  const chats = getStoredChats();
  return {
    results: chats,
    status: "Exhausted" as const,
    loadMore: () => {},
    isLoading: false,
  };
}

// ── Provider wrapper ──────────────────────────────────────────────────────
export function ConvexProvider({ children }: { children: ReactNode }) {
  return <ConvexAuthProvider>{children}</ConvexAuthProvider>;
}

export function ConvexProviderWithAuth({
  children,
}: {
  children: ReactNode;
  client: any;
  useAuth: any;
}) {
  return <ConvexAuthProvider>{children}</ConvexAuthProvider>;
}
