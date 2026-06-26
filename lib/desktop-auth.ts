import { Redis } from "@upstash/redis";
import { createClient, type RedisClientType } from "redis";

const TRANSFER_TOKEN_TTL_SECONDS = 300;
const OAUTH_STATE_TTL_SECONDS = 300;
const TRANSFER_TOKEN_PREFIX = "desktop-auth-transfer:";
const OAUTH_STATE_PREFIX = "desktop-oauth-state:";
const TOKEN_FORMAT_REGEX = /^[a-f0-9]{64}$/;
const NODE_REDIS_URL = process.env.REDIS_URL;

type DesktopAuthStore = {
  set(key: string, value: string, ttlSeconds: number): Promise<void>;
  getdel(key: string): Promise<string | null>;
};

type TransferTokenData = {
  sealedSession: string;
  createdAt: number;
  returnPath?: string;
  desktopAuthState?: string;
};

let nodeRedisClient: RedisClientType | null = null;
let nodeRedisConnectPromise: Promise<RedisClientType> | null = null;

function getUpstashRedis(): Redis | null {
  const redisUrl = process.env.UPSTASH_REDIS_REST_URL;
  const redisToken = process.env.UPSTASH_REDIS_REST_TOKEN;

  if (!redisUrl || !redisToken) {
    return null;
  }

  return new Redis({
    url: redisUrl,
    token: redisToken,
  });
}

async function getNodeRedisClient(): Promise<RedisClientType | null> {
  if (!NODE_REDIS_URL) {
    return null;
  }

  if (nodeRedisClient?.isOpen) {
    return nodeRedisClient;
  }

  if (!nodeRedisConnectPromise) {
    const client = createClient({ url: NODE_REDIS_URL });
    client.on("error", (err) => {
      console.error("[Desktop Auth] Redis client error:", err);
    });
    nodeRedisConnectPromise = client.connect().then(() => {
      nodeRedisClient = client as RedisClientType;
      return nodeRedisClient;
    });
  }

  try {
    return await nodeRedisConnectPromise;
  } catch (err) {
    console.error("[Desktop Auth] Failed to connect to Redis:", err);
    nodeRedisClient = null;
    nodeRedisConnectPromise = null;
    return null;
  }
}

async function getDesktopAuthStore(): Promise<DesktopAuthStore | null> {
  const upstashRedis = getUpstashRedis();
  if (upstashRedis) {
    return {
      async set(key, value, ttlSeconds) {
        await upstashRedis.set(key, value, { ex: ttlSeconds });
      },
      async getdel(key) {
        const value = await upstashRedis.getdel<string>(key);
        if (typeof value === "string") {
          return value;
        }
        return value == null ? null : JSON.stringify(value);
      },
    };
  }

  const nodeRedis = await getNodeRedisClient();
  if (!nodeRedis) {
    return null;
  }

  return {
    async set(key, value, ttlSeconds) {
      await nodeRedis.sendCommand([
        "SET",
        key,
        value,
        "EX",
        String(ttlSeconds),
      ]);
    },
    async getdel(key) {
      return await nodeRedis.sendCommand(["GETDEL", key]);
    },
  };
}

function generateTransferToken(): string {
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  return Array.from(array, (byte) => byte.toString(16).padStart(2, "0")).join(
    "",
  );
}

export async function createDesktopTransferToken(
  sealedSession: string,
  options?: { returnPath?: string; desktopAuthState?: string },
): Promise<string | null> {
  const store = await getDesktopAuthStore();
  if (!store) {
    console.error(
      "[Desktop Auth] Redis not configured, cannot create transfer token",
    );
    return null;
  }

  const transferToken = generateTransferToken();
  const key = `${TRANSFER_TOKEN_PREFIX}${transferToken}`;

  const data: TransferTokenData = {
    sealedSession,
    createdAt: Date.now(),
  };
  if (options?.returnPath) {
    data.returnPath = options.returnPath;
  }
  if (options?.desktopAuthState) {
    data.desktopAuthState = options.desktopAuthState;
  }

  try {
    await store.set(key, JSON.stringify(data), TRANSFER_TOKEN_TTL_SECONDS);
  } catch (err) {
    console.error(
      "[Desktop Auth] Failed to store transfer token in Redis:",
      err,
    );
    return null;
  }

  return transferToken;
}

export async function exchangeDesktopTransferToken(
  transferToken: string,
  options?: { desktopAuthState?: string },
): Promise<{
  sealedSession: string;
  returnPath?: string;
} | null> {
  if (!TOKEN_FORMAT_REGEX.test(transferToken)) {
    console.warn("[Desktop Auth] Invalid transfer token format");
    return null;
  }

  const store = await getDesktopAuthStore();
  if (!store) {
    console.error(
      "[Desktop Auth] Redis not configured, cannot exchange transfer token",
    );
    return null;
  }

  const key = `${TRANSFER_TOKEN_PREFIX}${transferToken}`;

  let rawData: string | null;
  try {
    // Use getdel for atomic get-and-delete to prevent race conditions
    rawData = await store.getdel(key);
  } catch (err) {
    console.error(
      "[Desktop Auth] Failed to retrieve transfer token from Redis:",
      err,
    );
    return null;
  }

  if (!rawData) {
    console.warn("[Desktop Auth] Transfer token not found or expired");
    return null;
  }

  let data: TransferTokenData;
  try {
    data = JSON.parse(rawData) as TransferTokenData;
  } catch (err) {
    console.error("[Desktop Auth] Failed to parse transfer token data:", err);
    return null;
  }

  if (
    !data ||
    typeof data.sealedSession !== "string" ||
    data.sealedSession.length === 0
  ) {
    console.error("[Desktop Auth] Invalid transfer token payload");
    return null;
  }

  if (data.desktopAuthState && !options?.desktopAuthState) {
    console.warn("[Desktop Auth] Desktop auth state required but not provided");
    return null;
  }

  if (
    options?.desktopAuthState &&
    data.desktopAuthState !== options.desktopAuthState
  ) {
    console.warn("[Desktop Auth] Desktop auth state mismatch");
    return null;
  }

  const result: { sealedSession: string; returnPath?: string } = {
    sealedSession: data.sealedSession,
  };
  if (typeof data.returnPath === "string") {
    result.returnPath = data.returnPath;
  }
  return result;
}

export type OAuthStateMetadata = {
  devCallbackPort?: number;
  returnPath?: string;
  desktopAuthState?: string;
};

export async function createOAuthState(
  metadata?: OAuthStateMetadata,
): Promise<string | null> {
  const store = await getDesktopAuthStore();
  if (!store) {
    console.error(
      "[Desktop Auth] Redis not configured, cannot create OAuth state",
    );
    return null;
  }

  const state = generateTransferToken();
  const key = `${OAUTH_STATE_PREFIX}${state}`;

  const value = metadata ? JSON.stringify(metadata) : "1";

  try {
    await store.set(key, value, OAUTH_STATE_TTL_SECONDS);
  } catch (err) {
    console.error("[Desktop Auth] Failed to store OAuth state in Redis:", err);
    return null;
  }

  return state;
}

export async function verifyAndConsumeOAuthState(
  state: string,
): Promise<{ valid: boolean; metadata?: OAuthStateMetadata }> {
  if (!TOKEN_FORMAT_REGEX.test(state)) {
    console.warn("[Desktop Auth] Invalid OAuth state format");
    return { valid: false };
  }

  const store = await getDesktopAuthStore();
  if (!store) {
    console.error(
      "[Desktop Auth] Redis not configured, cannot verify OAuth state",
    );
    return { valid: false };
  }

  const key = `${OAUTH_STATE_PREFIX}${state}`;

  try {
    const value = await store.getdel(key);
    if (!value) {
      return { valid: false };
    }

    if (value === "1") {
      return { valid: true };
    }

    try {
      const metadata =
        typeof value === "object"
          ? (value as unknown as OAuthStateMetadata)
          : (JSON.parse(value) as OAuthStateMetadata);
      return { valid: true, metadata };
    } catch {
      // If we can't parse metadata, state is still valid
      return { valid: true };
    }
  } catch (err) {
    console.error("[Desktop Auth] Failed to verify OAuth state:", err);
    return { valid: false };
  }
}
