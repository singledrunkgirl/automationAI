# HackWithAI v2 — Architecture Report

> **Generated:** 2026-06-18  
> **Scope:** Full codebase analysis of `/home/kali/HackWithAI`  
> **Policy:** No files modified, no dependencies changed.

---

## Table of Contents

1. [Folder Structure](#1-folder-structure)
2. [Tech Stack](#2-tech-stack)
3. [Entry Points](#3-entry-points)
4. [Authentication Flow](#4-authentication-flow)
5. [APIs and Database](#5-apis-and-database)
6. [External Integrations](#6-external-integrations)
7. [Build System](#7-build-system)
8. [Known Issues and Suspicious Areas](#8-known-issues-and-suspicious-areas)
9. [Missing Environment Variables](#9-missing-environment-variables)
10. [Dependency Graph](#10-dependency-graph)

---

## 1. Folder Structure

```
HackWithAI/
├── app/                          # Next.js App Router pages & API routes
│   ├── (chat)/                   # Chat route group
│   │   ├── layout.tsx            #   Chat layout (auth-gated sidebar)
│   │   ├── page.tsx              #   Main chat page
│   │   └── loading.tsx           #   Chat loading state
│   ├── (marketing)/              # Marketing pages (pricing, blog, etc.)
│   │   ├── layout.tsx
│   │   ├── page.tsx              #   Landing page
│   │   ├── blog/
│   │   ├── changelog/
│   │   ├── legal/
│   │   ├── open-source/
│   │   ├── pricing/
│   │   └── security/
│   ├── api/                      # Next.js API routes (35+ endpoints)
│   │   ├── agent-long/           #   Long-running agent (Trigger.dev)
│   │   ├── auth/                 #   Desktop OAuth callback
│   │   ├── chat/                 #   Chat streaming endpoint
│   │   ├── clear-auth-cookies/
│   │   ├── delete-account/
│   │   ├── delete-sandboxes/
│   │   ├── entitlements/
│   │   ├── extra-usage/          #   Stripe extra usage billing
│   │   ├── fraud/                #   Fraud detection webhook
│   │   ├── health/
│   │   ├── logout-all/
│   │   ├── mfa/                  #   Multi-factor auth (WorkOS)
│   │   ├── migrate-pentestgpt/
│   │   ├── referrals/
│   │   ├── sandbox/              #   Sandbox presence
│   │   ├── stripe.ts             #   Stripe client singleton
│   │   ├── subscribe/
│   │   ├── subscription-details/
│   │   ├── team/                 #   Team management
│   │   └── workos/               #   WorkOS webhook
│   ├── auth/                     # WorkOS AuthKit pages
│   ├── layout.tsx                # Root layout
│   ├── providers.tsx             # PostHog analytics provider
│   └── globals.css               # Global styles (Tailwind)
│
├── components/                   # React components (shadcn/ui + custom)
│   ├── ui/                       #   shadcn/ui primitives
│   ├── chat/                     #   Chat UI components
│   ├── sidebar/                  #   Sidebar components
│   ├── sandbox/                  #   Sandbox UI
│   ├── billing/                  #   Billing/pricing components
│   └── ...                       #   Other feature components
│
├── convex/                       # Convex backend (TypeScript)
│   ├── schema.ts                 #   Database schema (18+ tables)
│   ├── auth.config.ts            #   WorkOS JWT auth config
│   ├── convex.config.ts          #   Convex app config
│   ├── crons.ts                  #   Cron jobs (3 schedules)
│   ├── auth.ts                   #   Auth mutations/queries
│   ├── chats.ts                  #   Chat CRUD
│   ├── messages.ts               #   Message CRUD
│   ├── chatStreams.ts            #   Stream management
│   ├── fileActions.ts            #   File operations
│   ├── fileStorage.ts            #   File storage
│   ├── fileAggregate.ts          #   File aggregation
│   ├── userCustomization.ts      #   User preferences
│   ├── userDeletion.ts           #   Account deletion
│   ├── userSuspensions.ts        #   User suspension
│   ├── extraUsage.ts             #   Extra usage billing
│   ├── extraUsageActions.ts      #   Extra usage actions
│   ├── teamExtraUsage.ts         #   Team extra usage
│   ├── teamExtraUsageActions.ts  #   Team extra usage actions
│   ├── unitEconomics.ts          #   Unit economics
│   ├── unitEconomicsLib.ts       #   Unit economics lib
│   ├── usageLogs.ts              #   Usage logging
│   ├── localSandbox.ts           #   Local sandbox connections
│   ├── tempStreams.ts            #   Temporary streams
│   ├── s3Actions.ts              #   S3 file actions
│   ├── s3Cleanup.ts              #   S3 cleanup
│   ├── s3Utils.ts                #   S3 utilities
│   ├── feedback.ts               #   User feedback
│   ├── notes.ts                  #   User notes
│   ├── referrals.ts              #   Referral system
│   ├── sharedChats.ts            #   Chat sharing
│   ├── rateLimitStatus.ts        #   Rate limit status
│   ├── redisPubsub.ts            #   Redis pub/sub
│   ├── constants.ts              #   Shared constants
│   ├── lib/
│   │   ├── logger.ts             #   Convex logger
│   │   └── utils.ts              #   Convex utilities
│   └── _generated/               # Auto-generated Convex types
│
├── lib/                          # Shared library code
│   ├── ai/
│   │   ├── providers.ts          #   AI provider factory (5 modes)
│   │   └── prompts.ts            #   System prompts
│   ├── api/
│   │   └── chat-handler.ts       #   Core chat handler (~800 lines)
│   ├── auth/
│   │   ├── entitlements.ts       #   Subscription tier resolution
│   │   └── get-user-id.ts        #   User ID extraction
│   ├── rate-limit/
│   │   ├── index.ts              #   Rate limit orchestrator
│   │   ├── token-bucket.ts       #   Token bucket (paid users)
│   │   ├── sliding-window.ts     #   Sliding window (free users)
│   │   ├── redis.ts              #   Redis client
│   │   ├── refund.ts             #   Usage refund logic
│   │   ├── free-concurrency.ts   #   Free concurrency lock
│   │   └── free-monthly-cost.ts  #   Free monthly cost tracking
│   ├── desktop-auth.ts           #   Desktop OAuth with Redis
│   ├── errors.ts                 #   ChatSDKError class
│   ├── local-only.ts             #   Local-only mode detection
│   ├── model-access.ts           #   Model access codes
│   └── types/                    #   Shared TypeScript types
│       ├── index.ts
│       ├── chat.ts
│       └── user.ts
│
├── packages/
│   ├── desktop/                  # Tauri v2 desktop application
│   │   ├── src-tauri/
│   │   │   ├── src/
│   │   │   │   ├── lib.rs        #   Tauri app (~900 lines Rust)
│   │   │   │   └── pty.rs        #   PTY session manager
│   │   │   ├── Cargo.toml
│   │   │   └── tauri.conf.json
│   │   ├── src/                  #   Desktop frontend (React)
│   │   └── package.json
│   └── local/                    # Local sandbox client (Node.js)
│       └── src/
│           └── index.ts          #   LocalSandboxClient (~900 lines)
│
├── trigger/                      # Trigger.dev background jobs
├── docker/
│   └── Dockerfile                # Kali Linux sandbox image (~200 lines)
│
├── .github/
│   └── workflows/
│       ├── desktop-build.yml     #   Multi-platform desktop CI/CD
│       ├── docker-sandbox.yml    #   Docker sandbox CI/CD
│       └── test.yml              #   Test CI/CD
│
├── public/                       # Static assets
├── styles/                       # Additional styles
├── e2e-tests/                    # Playwright E2E tests
│
├── package.json                  # Root workspace config
├── next.config.ts                # Next.js 16 config
├── tsconfig.json                 # TypeScript strict config
├── middleware.ts                 # WorkOS AuthKit middleware
├── tailwind.config.ts            # Tailwind CSS config
├── postcss.config.js             # PostCSS config
├── components.json               # shadcn/ui config
├── trigger.config.ts             # Trigger.dev config
├── .env.local.example            # Environment variable documentation
├── .eslintrc.json                # ESLint config
├── .prettierrc                   # Prettier config
├── .husky/                       # Git hooks
├── jest.config.ts                # Jest config
├── playwright.config.ts          # Playwright config
└── ARCHITECTURE_REPORT.md        # This file
```

---

## 2. Tech Stack

### Frontend

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Framework | Next.js | 16.2.7 | App Router, Turbopack, `output: "standalone"` |
| Language | TypeScript | 6.0.3 | Strict mode, bundler module resolution |
| UI Components | shadcn/ui | Latest | Radix-based, Tailwind-styled |
| Styling | Tailwind CSS | 4.x | Utility-first |
| State (client) | React Context | — | `GlobalStateProvider`, `DataStreamProvider` |
| Real-time (client) | Centrifugo | — | WebSocket-based messaging |
| Analytics | PostHog | — | **Provider tracking DISABLED** (commented out) |

### Backend

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Backend BaaS | Convex | 1.40.0 | DB, server functions, file storage, auth, pub/sub, cron, aggregates |
| Auth Provider | WorkOS AuthKit | — | JWT-based, MFA, org memberships |
| Payments | Stripe | 2026-05-27.dahlia | Subscriptions, extra usage, auto-reload |
| Cache / Rate Limit | Upstash Redis | — | Token bucket (paid), sliding window (free) |
| File Storage | AWS S3 | — | Presigned URLs, Convex file storage integration |
| Background Jobs | Trigger.dev | 4.4.6 | Agent-long mode, 1hr max, node-22, 3 retries |
| Real-time (server) | Centrifugo | — | Sandbox PTY streaming, command relay |
| AI Providers | OpenRouter (default), OpenAI, Google, Anthropic, Ollama | — | Provider factory with fallback chain |
| AI SDK | Vercel AI SDK | 6.0.196 | Streaming chat, tool calling, resumable-stream |
| Session | iron-session | — | Desktop auth transfer token sealing |
| JWT | jose | — | Token handling |

### Desktop

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Desktop Framework | Tauri | v2 | Rust backend + web frontend |
| PTY | portable-pty (Rust) | — | PTY session management |
| Auto-updater | Tauri updater | — | 24h check interval, platform-specific |

### Infrastructure

| Layer | Technology | Notes |
|-------|-----------|-------|
| Package Manager | pnpm | 10.33.2, workspaces, 40+ security overrides |
| Container | Docker | Kali Linux sandbox image |
| CI/CD | GitHub Actions | Desktop build (3 platforms), Docker, tests |
| Testing | Jest 30.x + Playwright | Unit + E2E |
| Git Hooks | Husky 9.x + lint-staged | Pre-commit linting |

---

## 3. Entry Points

### Application Entry Points

| File | Purpose |
|------|---------|
| [`middleware.ts`](middleware.ts) | **First execution point** — WorkOS AuthKit middleware runs on every request. Handles auth, desktop app detection, referral cookies, rate limit errors. |
| [`app/layout.tsx`](app/layout.tsx) | **Root layout** — Wraps all pages in `GlobalStateProvider` → `DataStreamProvider` → `TodoBlockProvider` → `TooltipProvider` → `Toaster`. Local-only mode wraps in `LocalClientProvider`. |
| [`app/providers.tsx`](app/providers.tsx) | **PostHog analytics** — Conditional initialization based on auth. Filters Convex exceptions. Identifies users. |
| [`app/(chat)/page.tsx`](app/(chat)/page.tsx) | **Main chat page** — Authenticated/Unauthenticated split. Unauthenticated shows typing animation + signup redirect. Authenticated renders `Chat` component. |
| [`app/(chat)/layout.tsx`](app/(chat)/layout.tsx) | **Chat layout** — `AuthLoading` (spinner), `Unauthenticated` (full children), `Authenticated` (sidebar + chat). |
| [`app/(marketing)/page.tsx`](app/(marketing)/page.tsx) | **Landing page** — Marketing content for unauthenticated users. |

### API Entry Points

| File | Purpose |
|------|---------|
| [`app/api/chat/route.ts`](app/api/chat/route.ts) | **Chat streaming** — Delegates to `createChatHandler()`. `maxDuration = 420` (7 min). |
| [`app/api/agent-long/route.ts`](app/api/agent-long/route.ts) | **Long-running agent** — Trigger.dev background job. |
| [`app/api/auth/desktop-callback/route.ts`](app/api/auth/desktop-callback/route.ts) | **Desktop OAuth callback** — Verifies state, creates sealed session, generates transfer token. |
| [`app/api/stripe.ts`](app/api/stripe.ts) | **Stripe client singleton** — Lazy initialization, proxy-based export. |
| [`app/api/health/route.ts`](app/api/health/route.ts) | **Health check** — Simple status endpoint. |

### Backend Entry Points (Convex)

| File | Purpose |
|------|---------|
| [`convex/schema.ts`](convex/schema.ts) | **Database schema** — All tables, indexes, relations. |
| [`convex/auth.config.ts`](convex/auth.config.ts) | **Auth configuration** — WorkOS JWT issuers, audiences. |
| [`convex/convex.config.ts`](convex/convex.config.ts) | **Convex app config** — Auth info, file storage, plugins. |
| [`convex/crons.ts`](convex/crons.ts) | **Cron jobs** — Orphan file purge, webhook cleanup, stale connections. |

### Desktop Entry Points

| File | Purpose |
|------|---------|
| [`packages/desktop/src-tauri/src/lib.rs`](packages/desktop/src-tauri/src/lib.rs) | **Tauri app** — PTY management, command server, deep links, auto-updater. |
| [`packages/desktop/src-tauri/src/pty.rs`](packages/desktop/src-tauri/src/pty.rs) | **PTY session manager** — `portable_pty` wrapper with IPC streaming. |
| [`packages/local/src/index.ts`](packages/local/src/index.ts) | **Local sandbox client** — Convex + Centrifugo connection, command relay. |

---

## 4. Authentication Flow

### Overview

The authentication system uses **WorkOS AuthKit** as the primary identity provider, with **Convex** handling backend auth verification and **Redis** managing desktop-specific auth flows.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Browser    │────▶│  Middleware   │────▶│   WorkOS     │
│   / Desktop  │     │ (AuthKit)    │     │   AuthKit    │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                     │
       │                    ▼                     │
       │           ┌──────────────┐              │
       │           │   Convex     │◀─────────────┘
       │           │  JWT Auth    │   (JWT token)
       │           └──────────────┘
       │                    │
       ▼                    ▼
┌──────────────┐     ┌──────────────┐
│   Desktop    │     │   Upstash    │
│   OAuth      │────▶│   Redis      │
│   (Tauri)    │     │ (transfer    │
└──────────────┘     │  tokens)     │
                     └──────────────┘
```

### Flow Details

#### 1. Middleware (`middleware.ts`)
- Runs on **every request** via Next.js middleware.
- **Unauthenticated paths** (`/`, `/pricing`, `/blog/*`, `/api/health`, etc.) — skip auth.
- **Desktop auth handoff paths** (`/api/auth/desktop-callback`) — skip session check.
- **Desktop app detection** — checks `user-agent` for `"MaxAI-Desktop"`.
- **Referral cookie management** — sets `referral_code` cookie from query params.
- **Rate limit error handling** — catches rate limit errors during session refresh.
- **Empty password fallback** — if `WORKOS_COOKIE_PASSWORD` is missing, returns **503**.
- **Session header forwarding** — `x-workos-session` header for Convex.

#### 2. Convex Auth (`convex/auth.config.ts`)
- **WorkOS JWT** authentication provider.
- **Multiple issuer bases**: staging (`http://localhost:3000`), production (`https://hackwithai.com`).
- **Extensive audience variants**: `stripe`, `workos`, `https://api.workos.com/`, `https://api.staging.workos.com/`.
- **Permissive provider** for user_management issuers in non-production environments.

#### 3. Desktop OAuth (`app/api/auth/desktop-callback/route.ts`)
- **OAuth state verification** via Redis (stored during desktop app initiation).
- **WorkOS code exchange** — authenticates with authorization code.
- **Session sealing** — creates iron-session sealed session cookie.
- **Transfer token** — 64-char hex token stored in Redis (300s TTL).
- **Deep link return** — HTML page with `hwai://auth?token=...` deep link or dev callback URL.
- **XSS-safe rendering** — `escapeHtml` for all user-controlled values.

#### 4. Desktop Auth State (`lib/desktop-auth.ts`)
- **Redis-backed** transfer tokens and OAuth state.
- **Supports** Upstash Redis and node Redis.
- **Atomic getdel** — race condition prevention for token consumption.
- **State metadata** includes `devCallbackPort`, `returnPath`, `desktopAuthState`.

#### 5. User ID Extraction (`lib/auth/get-user-id.ts`)
- **`getUserID()`** — basic user ID from WorkOS session.
- **`getUserIDAndPro()`** — with subscription tier resolution.
- **`getUserIDWithFreshLogin()`** — with 10-minute freshness window.
- **Local-only mode** — returns hardcoded `LOCAL_ONLY_USER_ID = "local-kali-user"`.

#### 6. Entitlements (`lib/auth/entitlements.ts`)
- **Tier resolution** from WorkOS entitlements: `Ultra > Team > Pro-Plus > Pro > Free`.
- **Entitlement slugs**: `ultra-plan`, `team-plan`, `pro-plus-plan`, `pro-plan` (with monthly/yearly variants).

#### 7. Model Access Codes (`lib/model-access.ts`)
- **Default codes**: `"QR-MODEL-2026"`, `"QR-ADMIN-ACCESS"`, `"3210-3002"`.
- **localStorage persistence** — codes stored in browser.
- **Event dispatch** on grant — `modelAccessGranted` custom event.
- **`getEffectiveSubscriptionForModelAccess()`** — upgrades free users to pro if valid code provided.

---

## 5. APIs and Database

### Database Schema (`convex/schema.ts`)

**18+ tables** organized by domain:

#### Chat & Messages
| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `chats` | `userId`, `title`, `chatMode`, `selectedModel`, `shareId`, `deleted`, `folderId` | Chat sessions |
| `chat_summaries` | `userId`, `chatId`, `summary`, `title` | Chat summaries for sidebar |
| `messages` | `chatId`, `userId`, `role`, `content`, `toolInvocations`, `experimentalAttachments` | Chat messages |

#### Files & Storage
| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `files` | `userId`, `chatId`, `storageId`, `name`, `size`, `type`, `sha256` | File metadata |
| `temp_streams` | `userId`, `chatId`, `streamId`, `data`, `expiresAt` | Temporary stream data |

#### Billing & Usage
| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `extra_usage` | `userId`, `stripeSessionId`, `amount`, `status` | Individual extra usage |
| `team_extra_usage` | `teamId`, `stripeSessionId`, `amount`, `status` | Team extra usage |
| `team_member_usage` | `teamId`, `memberId`, `usagePoints`, `periodStart` | Team member usage |
| `usage_logs` | `userId`, `chatId`, `model`, `tokensIn`, `tokensOut`, `costPoints` | Usage audit trail |
| `revenue_events` | — | Revenue tracking |
| `paid_start_events` | — | Paid start events |
| `paid_start_mix_daily` | — | Daily paid start mix |
| `unit_economics_daily` | — | Daily unit economics |

#### Users & Social
| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `user_customization` | `userId`, `theme`, `fontSize`, `sidebarPinned` | User preferences |
| `user_suspensions` | `userId`, `reason`, `suspendedAt`, `expiresAt` | User suspensions |
| `referral_codes` | `userId`, `code`, `timesUsed` | Referral codes |
| `referral_attributions` | `userId`, `referredBy`, `attributedAt` | Referral tracking |
| `referral_rewards` | `userId`, `rewardType`, `status` | Referral rewards |

#### System
| Table | Key Fields | Purpose |
|-------|-----------|---------|
| `memories` | `userId`, `content`, `scope` | User memories |
| `notes` | `userId`, `chatId`, `content` | User notes |
| `local_sandbox_tokens` | `token`, `userId`, `expiresAt` | Local sandbox auth tokens |
| `local_sandbox_connections` | `connectionId`, `userId`, `status`, `lastHeartbeat` | Sandbox connection tracking |
| `feedback` | `userId`, `chatId`, `score`, `comment` | User feedback |
| `processed_webhooks` | `eventId`, `source` | Webhook idempotency |
| `processed_checkout_sessions` | `sessionId` | Checkout idempotency |

### API Routes (35+ endpoints)

#### Chat
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/chat` | POST | Chat streaming (delegates to `createChatHandler()`) |
| `/api/chat/[id]/stream` | GET | Stream resumption |

#### Agent (Long-Running)
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/agent-long` | POST | Start long-running agent (Trigger.dev) |
| `/api/agent-long/cancel` | POST | Cancel running agent |
| `/api/agent-long/resume` | POST | Resume paused agent |

#### Auth
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/auth/desktop-callback` | GET | Desktop OAuth callback |
| `/api/clear-auth-cookies` | POST | Clear auth cookies |
| `/api/logout-all` | POST | Logout all sessions |

#### WorkOS
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/workos/webhook` | POST | WorkOS webhook events |

#### Subscriptions & Billing
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/subscribe` | POST | Create subscription |
| `/api/subscription/webhook` | POST | Stripe subscription webhook |
| `/api/subscription-details` | GET | Get subscription details |
| `/api/extra-usage/confirm` | POST | Confirm extra usage purchase |
| `/api/extra-usage/webhook` | POST | Stripe extra usage webhook |

#### Team
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/team/extra-usage/*` | Various | Team extra usage (5 routes) |
| `/api/team/invite` | POST | Invite team member |
| `/api/team/members` | GET | List team members |
| `/api/team/seats` | POST | Manage team seats |

#### MFA
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/mfa/enroll` | POST | Enroll MFA factor |
| `/api/mfa/verify` | POST | Verify MFA challenge |
| `/api/mfa/factors` | GET | List MFA factors |
| `/api/mfa/delete` | DELETE | Remove MFA factor |

#### Other
| Route | Method | Purpose |
|-------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/delete-account` | POST | Delete user account |
| `/api/delete-sandboxes` | POST | Delete sandbox environments |
| `/api/entitlements` | GET | Get user entitlements |
| `/api/fraud/webhook` | POST | Fraud detection webhook |
| `/api/migrate-pentestgpt` | POST | Migrate from PentestGPT |
| `/api/referrals` | POST | Create referral |
| `/api/referrals/attribution` | POST | Record referral attribution |
| `/api/sandbox/presence` | POST | Sandbox presence heartbeat |

### Chat Handler Architecture (`lib/api/chat-handler.ts`)

The core chat handler (~800 lines) orchestrates:

1. **Free run concurrency lock** — TTL-based, prevents concurrent free-tier usage.
2. **Pre-emptive timeout** — for non-agent modes.
3. **Rate limiting** — token bucket (paid) / sliding window (free).
4. **Extra usage config** — builds Stripe checkout for additional credits.
5. **Sandbox file upload** — with path rewriting for sandbox environments.
6. **Title generation** — parallel AI call for chat title.
7. **System prompt** — with resume context, notes injection.
8. **Agent stream runner** — with fallback retry on provider errors.
9. **Incomplete tool call summarization** — on abort.
10. **Usage tracking and deduction** — points-based billing.
11. **Stream resumption** — via `resumable-stream`.
12. **PostHog analytics capture** — usage events.
13. **PTY cleanup** — on error.

### Rate Limiting (`lib/rate-limit/`)

| Strategy | Users | Limits |
|----------|-------|--------|
| Token bucket | Paid (Pro, Pro+, Ultra, Team) | Configurable tokens, refill rate |
| Sliding window | Free | 10 units/day, Ask=1 unit, Agent=2 units |
| Free concurrency lock | Free | Single concurrent run |
| Free monthly cost | Free | Monthly cost cap |

---

## 6. External Integrations

### 1. WorkOS (Auth)
- **Purpose**: Authentication, MFA, organization management, user management.
- **Integration points**: `middleware.ts`, `convex/auth.config.ts`, `app/api/workos/webhook/route.ts`, `app/api/mfa/*`.
- **Data flow**: AuthKit middleware → JWT → Convex auth → Session cookies.

### 2. Stripe (Payments)
- **Purpose**: Subscription management, extra usage billing, auto-reload.
- **Integration points**: `app/api/stripe.ts`, `app/api/subscribe/*`, `app/api/subscription/webhook/route.ts`, `app/api/extra-usage/*`.
- **API version**: `2026-05-27.dahlia`.
- **Data flow**: Checkout session → Webhook → Convex mutations → Entitlement updates.

### 3. Upstash Redis (Cache/Rate Limit)
- **Purpose**: Rate limiting (token bucket + sliding window), desktop auth transfer tokens, OAuth state.
- **Integration points**: `lib/rate-limit/redis.ts`, `lib/desktop-auth.ts`.
- **Data flow**: Middleware/API → Redis → Rate limit decision.

### 4. AWS S3 (File Storage)
- **Purpose**: File storage with presigned URLs.
- **Integration points**: `convex/s3Actions.ts`, `convex/s3Cleanup.ts`, `convex/s3Utils.ts`.
- **Data flow**: Client → Convex → S3 presigned URL → Direct upload.

### 5. Convex (Backend)
- **Purpose**: Database, server functions, file storage, auth, pub/sub, cron jobs, aggregates.
- **Integration points**: All `convex/` files, `app/providers.tsx`.
- **Version**: `1.40.0` with plugins: file storage, auth, pub/sub, cron, aggregates.

### 6. OpenRouter (AI Provider)
- **Purpose**: Default AI model provider aggregation.
- **Integration points**: `lib/ai/providers.ts`.
- **Patches**: Sanitizes xAI requests (strips `encrypted_content`), Gemini function responses (removes `$ref`), Kimi reasoning tool calls.

### 7. OpenAI / Google / Anthropic (AI Providers)
- **Purpose**: Alternative AI model providers.
- **Integration points**: `lib/ai/providers.ts`.
- **Usage**: Fallback chain when OpenRouter is unavailable.

### 8. Ollama (Local AI)
- **Purpose**: Local AI model support (Qwen, DeepSeek, Mistral, Llama).
- **Integration points**: `lib/ai/providers.ts`.
- **Usage**: Local-only mode, no external API calls.

### 9. E2B (Cloud Sandbox)
- **Purpose**: Cloud sandbox environments for code/command execution.
- **Integration points**: `lib/api/chat-handler.ts` (sandbox file upload), sandbox components.
- **Usage**: Primary sandbox mode for cloud users.

### 10. Centrifugo (Real-time)
- **Purpose**: Real-time messaging for sandbox PTY streaming and command relay.
- **Integration points**: `packages/local/src/index.ts`, `convex/redisPubsub.ts`.
- **Data flow**: Local sandbox → Centrifugo → Browser client.

### 11. Trigger.dev (Background Jobs)
- **Purpose**: Long-running agent execution (agent-long mode).
- **Integration points**: `trigger.config.ts`, `app/api/agent-long/*`.
- **Config**: `node-22` runtime, 1hr max duration, 3 retries with exponential backoff.

### 12. PostHog (Analytics)
- **Purpose**: Product analytics, usage tracking.
- **Integration points**: `app/providers.tsx`, `lib/api/chat-handler.ts`.
- **⚠️ DISABLED**: Provider tracking is commented out (`// PostHog provider tracking disabled`).

### 13. Perplexity / Jina (Web Search)
- **Purpose**: Web search capabilities for AI agent.
- **Integration points**: Via AI tool calling in chat handler.

### 14. GitHub Actions (CI/CD)
- **Purpose**: Desktop builds (macOS/Linux/Windows), Docker sandbox builds, test suite.
- **Integration points**: `.github/workflows/*`.

---

## 7. Build System

### Package Manager: pnpm 10.33.2

**Workspace configuration** in [`package.json`](package.json):
- Root workspace with `packages/desktop` and `packages/local` as workspace packages.
- **40+ security overrides** patching known vulnerabilities:
  - `axios@>=0.8.1 <1.7.4` → `1.7.4`
  - `glob@<10.4.5` → `10.4.5`
  - `js-yaml@<4.1.1` → `4.1.1`
  - `vite@<6.0.12` → `6.0.12`
  - `tar@<6.2.1` → `6.2.1`
  - `cookie@<0.7.0` → `0.7.2`
  - `dompurify@<3.2.4` → `3.2.4`
  - `esbuild@<0.25.0` → `0.25.0`
  - `ws@<8.17.1` → `8.17.1`
  - `qs@<6.15.1` → `6.15.1`
  - And 30+ more...
- **Patched dependencies**: `ai@6.0.196` (custom patch).
- **Ignored build dependencies**: `node-pty`, `esbuild`, `sharp`, `isolated-vm`, `lmdb`, `msgpackr`, `sodium-native`.

### Build Scripts

| Script | Command | Purpose |
|--------|---------|---------|
| `dev` | `concurrently "next dev" "convex dev"` | Development server |
| `dev:local` | `convex dev --url ...` | Local Convex dev |
| `dev:all` | `concurrently "next dev" "convex dev" "trigger dev"` | Full dev stack |
| `build` | `next build` | Production build |
| `start` | `next start` | Production server |
| `lint` | `next lint` | Linting |
| `typecheck` | `tsc --noEmit` | Type checking |
| `test` | `jest --passWithNoTests` | Unit tests |
| `test:e2e` | `playwright test` | E2E tests |
| `docker:build` | `docker build ...` | Sandbox Docker image |
| `sandbox:deploy` | Custom script | Deploy sandbox |
| `desktop:dev` | Tauri dev | Desktop development |
| `desktop:build` | Tauri build | Desktop production build |

### Next.js Configuration (`next.config.ts`)
- **Output mode**: `standalone` (self-hosted deployment).
- **Dev indicators**: Disabled.
- **Images**: Unoptimized, localhost remote patterns.
- **Local-only mode**: Wraps in `LocalClientProvider`.

### TypeScript Configuration (`tsconfig.json`)
- **Strict mode**: Enabled.
- **Module resolution**: `bundler`.
- **Target**: `ESNext`.
- **JSX**: `preserve`.

---

## 8. Known Issues and Suspicious Areas

### Critical Issues

#### 1. Empty Password Fallback in Middleware (`middleware.ts`)
- **Severity**: HIGH
- **Location**: [`middleware.ts`](middleware.ts) — `WORKOS_COOKIE_PASSWORD` fallback
- **Issue**: If `WORKOS_COOKIE_PASSWORD` is not set, the middleware falls back to an empty string (`process.env.WORKOS_COOKIE_PASSWORD ?? ""`). This means the cookie encryption key is empty, which would either crash at runtime or silently use a weak key.
- **Impact**: Authentication cookies would be encrypted with an empty password, making them trivially forgeable. The middleware returns a 503 error in this case, but the fallback should throw immediately at startup rather than silently degrading.

#### 2. PostHog Provider Tracking Disabled (`lib/ai/providers.ts`)
- **Severity**: MEDIUM
- **Location**: [`lib/ai/providers.ts`](lib/ai/providers.ts)
- **Issue**: The PostHog provider tracking is explicitly commented out with `// PostHog provider tracking disabled`. This means AI model usage analytics are not being captured.
- **Impact**: Loss of visibility into which models are being used, error rates, and latency metrics. This appears to be intentionally disabled but without a feature flag or configuration toggle.

#### 3. Hardcoded Local-Only User ID (`lib/local-only.ts`)
- **Severity**: MEDIUM
- **Location**: [`lib/local-only.ts`](lib/local-only.ts)
- **Issue**: `LOCAL_ONLY_USER_ID = "local-kali-user"` is hardcoded. In local-only mode, all users share the same user ID.
- **Impact**: No user isolation in local-only mode. All local users share the same database records (chats, settings, etc.). This is acceptable for single-user local deployments but could cause data corruption if multiple users access the same instance.

#### 4. Model Access Codes Hardcoded (`lib/model-access.ts`)
- **Severity**: MEDIUM
- **Location**: [`lib/model-access.ts`](lib/model-access.ts)
- **Issue**: Default access codes (`"QR-MODEL-2026"`, `"QR-ADMIN-ACCESS"`, `"3210-3002"`) are hardcoded in source code.
- **Impact**: Anyone who reads the source code knows the default access codes. These should be environment variables or server-validated secrets.

### Security Concerns

#### 5. pnpm Overrides as Security Patches (`package.json`)
- **Severity**: INFO
- **Location**: [`package.json`](package.json) — `pnpm.overrides`
- **Issue**: 40+ dependency overrides pinning specific versions to patch CVEs. While proactive, this creates a maintenance burden — each override must be tracked and removed when the upstream dependency updates.
- **Recommendation**: Add comments explaining which CVE each override addresses, and set up automated Dependabot/Renovate to track these.

#### 6. Broad CORS in Desktop App (`packages/desktop/src-tauri/src/lib.rs`)
- **Severity**: LOW
- **Location**: [`packages/desktop/src-tauri/src/lib.rs`](packages/desktop/src-tauri/src/lib.rs)
- **Issue**: The Tauri command server uses permissive CORS headers for local development.
- **Impact**: Only affects localhost, but should be restricted to specific origins in production builds.

#### 7. Stripe API Version Pinned (`app/api/stripe.ts`)
- **Severity**: LOW
- **Location**: [`app/api/stripe.ts`](app/api/stripe.ts)
- **Issue**: Stripe API version `2026-05-27.dahlia` is hardcoded. This is a very recent API version (May 2026).
- **Impact**: If Stripe deprecates this version, the application will break. Should be monitored for API version updates.

### Code Quality Issues

#### 8. Massive Chat Handler (`lib/api/chat-handler.ts`)
- **Severity**: MEDIUM
- **Location**: [`lib/api/chat-handler.ts`](lib/api/chat-handler.ts)
- **Issue**: ~800 lines in a single file handling: rate limiting, auth, AI streaming, file uploads, billing, analytics, error handling, stream resumption.
- **Impact**: Difficult to test, maintain, or reason about. Violates Single Responsibility Principle. Should be refactored into smaller modules.

#### 9. Legacy Fields in Schema (`convex/schema.ts`)
- **Severity**: LOW
- **Location**: [`convex/schema.ts`](convex/schema.ts)
- **Issue**: Legacy fields retained for backward compatibility: `codex_thread_id`, `max_mode_enabled`, `byok`, etc.
- **Impact**: Schema bloat. These should be documented and scheduled for cleanup.

#### 10. Monetary Values in POINTS
- **Severity**: INFO
- **Location**: Throughout codebase
- **Issue**: All monetary values are stored as integer POINTS (1 point = $0.0001).
- **Impact**: While this avoids floating-point precision issues, the conversion factor is undocumented in most places. A comment or constant should clarify the conversion.

### Potential Runtime Issues

#### 11. Free Concurrency Lock TTL (`lib/api/chat-handler.ts`)
- **Severity**: LOW
- **Location**: [`lib/api/chat-handler.ts`](lib/api/chat-handler.ts)
- **Issue**: Free-tier concurrency lock uses a TTL-based approach. If a request crashes without releasing the lock, the user is blocked until TTL expiry.
- **Impact**: Temporary denial of service for free users if their requests crash.

#### 12. Desktop Auth Token Race Condition (`lib/desktop-auth.ts`)
- **Severity**: LOW
- **Location**: [`lib/desktop-auth.ts`](lib/desktop-auth.ts)
- **Issue**: Uses `getdel` for atomic token consumption, which is correct. However, the 300s TTL on transfer tokens means tokens could be consumed after expiry if clock skew exists.
- **Impact**: Low probability, but should add TTL validation before accepting tokens.

#### 13. PTY Cleanup on Error (`lib/api/chat-handler.ts`)
- **Severity**: LOW
- **Location**: [`lib/api/chat-handler.ts`](lib/api/chat-handler.ts)
- **Issue**: PTY cleanup is triggered on error, but there's no heartbeat or watchdog for orphaned PTY sessions.
- **Impact**: Orphaned PTY processes could accumulate if the cleanup path is not executed.

#### 14. Convex Auth Config — Permissive Issuers (`convex/auth.config.ts`)
- **Severity**: LOW
- **Location**: [`convex/auth.config.ts`](convex/auth.config.ts)
- **Issue**: Permissive provider for user_management issuers in non-production environments.
- **Impact**: Acceptable for development, but should be locked down in production.

---

## 9. Missing Environment Variables

Based on [`lib/ai/providers.ts`](lib/ai/providers.ts), [`lib/desktop-auth.ts`](lib/desktop-auth.ts), [`lib/rate-limit/redis.ts`](lib/rate-limit/redis.ts), [`app/api/stripe.ts`](app/api/stripe.ts), [`trigger.config.ts`](trigger.config.ts), and [`middleware.ts`](middleware.ts):

### Required (no fallback — will crash if missing)

| Variable | Used In | Purpose |
|----------|---------|---------|
| `WORKOS_CLIENT_ID` | `middleware.ts` | WorkOS OAuth client ID |
| `WORKOS_API_KEY` | `middleware.ts` | WorkOS API key |
| `WORKOS_COOKIE_PASSWORD` | `middleware.ts` | Cookie encryption password (32+ chars) |
| `CONVEX_DEPLOYMENT` | `convex/` | Convex deployment URL |
| `NEXT_PUBLIC_CONVEX_URL` | `app/providers.tsx` | Public Convex URL |
| `TRIGGER_SECRET_KEY` | `trigger.config.ts` | Trigger.dev secret key |
| `TRIGGER_API_URL` | `trigger.config.ts` | Trigger.dev API URL |

### Required for Production (have fallbacks for dev)

| Variable | Used In | Fallback | Purpose |
|----------|---------|----------|---------|
| `STRIPE_API_KEY` / `STRIPE_SECRET_KEY` | `app/api/stripe.ts` | Throws if missing | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | Webhook routes | Throws if missing | Stripe webhook signing secret |
| `UPSTASH_REDIS_REST_URL` | `lib/rate-limit/redis.ts` | Falls back to local Redis | Rate limit Redis URL |
| `UPSTASH_REDIS_REST_TOKEN` | `lib/rate-limit/redis.ts` | Falls back to local Redis | Rate limit Redis token |
| `REDIS_URL` | `lib/desktop-auth.ts` | Falls back to Upstash | Desktop auth Redis URL |
| `AWS_ACCESS_KEY_ID` | `convex/s3Actions.ts` | Throws if missing | S3 access key |
| `AWS_SECRET_ACCESS_KEY` | `convex/s3Actions.ts` | Throws if missing | S3 secret key |
| `AWS_S3_BUCKET` | `convex/s3Actions.ts` | Throws if missing | S3 bucket name |
| `AWS_REGION` | `convex/s3Actions.ts` | Throws if missing | S3 region |

### Optional (have graceful fallbacks)

| Variable | Used In | Fallback | Purpose |
|----------|---------|----------|---------|
| `OPENROUTER_API_KEY` | `lib/ai/providers.ts` | Falls to next provider | OpenRouter API key |
| `OPENAI_API_KEY` | `lib/ai/providers.ts` | Falls to next provider | OpenAI API key |
| `GOOGLE_GENERATIVE_AI_API_KEY` | `lib/ai/providers.ts` | Falls to next provider | Google AI API key |
| `ANTHROPIC_API_KEY` | `lib/ai/providers.ts` | Falls to next provider | Anthropic API key |
| `OLLAMA_BASE_URL` | `lib/ai/providers.ts` | Localhost default | Ollama server URL |
| `E2B_API_KEY` | Chat handler | Sandbox disabled | E2B cloud sandbox key |
| `NEXT_PUBLIC_POSTHOG_KEY` | `app/providers.tsx` | Analytics disabled | PostHog API key |
| `NEXT_PUBLIC_POSTHOG_HOST` | `app/providers.tsx` | Default host | PostHog host URL |
| `CENTRIFUGO_API_URL` | `packages/local/src/index.ts` | Sandbox disabled | Centrifugo server URL |
| `CENTRIFUGO_API_KEY` | `packages/local/src/index.ts` | Sandbox disabled | Centrifugo API key |
| `PERPLEXITY_API_KEY` | Chat handler | Web search disabled | Perplexity search API key |
| `JINA_API_KEY` | Chat handler | Web search disabled | Jina search API key |
| `NEXT_PUBLIC_REFERRAL_REWARD_AMOUNT` | Referral system | Default amount | Referral reward value |
| `NEXT_PUBLIC_REFERRAL_REWARD_CURRENCY` | Referral system | Default currency | Referral reward currency |
| `LOCAL_ONLY_MODE` / `NEXT_PUBLIC_LOCAL_ONLY_MODE` | `lib/local-only.ts` | Cloud mode | Enable local-only mode |

---

## 10. Dependency Graph

### Runtime Dependencies (Root)

```
@hackwithai/desktop (packages/desktop)
├── @tauri-apps/api          # Tauri frontend API
├── @tauri-apps/plugin-*     # Tauri plugins (shell, deep-link, updater, etc.)
└── react/react-dom          # UI framework

@hackwithai/local (packages/local)
├── convex                   # Convex client
├── centrifuge               # Centrifugo real-time client
└── typescript               # TypeScript

root (HackWithAI)
├── next                     # Next.js 16 framework
├── react/react-dom          # UI framework
├── convex                   # Convex backend client
├── @workos-inc/authkit-nextjs  # WorkOS AuthKit
├── ai                       # Vercel AI SDK 6.0.196 (patched)
│   ├── @ai-sdk/openai       #   OpenAI provider
│   ├── @ai-sdk/google       #   Google provider
│   ├── @ai-sdk/anthropic    #   Anthropic provider
│   └── @ai-sdk/openai-compatible # OpenRouter provider
├── stripe                   # Stripe payment processing
├── @upstash/redis           # Upstash Redis client
├── ioredis                  # Redis client (fallback)
├── iron-session             # Session sealing
├── jose                     # JWT handling
├── posthog-js               # PostHog analytics
├── @trigger-dev/sdk         # Trigger.dev background jobs
├── centrifuge               # Centrifugo real-time
├── @aws-sdk/client-s3       # AWS S3
├── @aws-sdk/s3-request-presigner # S3 presigned URLs
├── tailwindcss              # Styling
├── @radix-ui/*              # UI primitives (shadcn/ui)
├── lucide-react             # Icons
├── class-variance-authority # CSS variants
├── clsx/tailwind-merge      # Class utilities
├── zod                      # Schema validation
├── nanoid                   # ID generation
├── date-fns                 # Date utilities
├── react-markdown           # Markdown rendering
├── rehype-*                 # Markdown processing
├── remark-*                 # Markdown processing
├── shiki                    # Syntax highlighting
└── ... (100+ total packages)
```

### Dev Dependencies

```
root (dev)
├── typescript               # TypeScript 6.0.3
├── @types/react             # React types
├── @types/node              # Node types
├── eslint                   # Linting
├── prettier                 # Formatting
├── jest                     # Unit testing
├── @playwright/test         # E2E testing
├── husky                    # Git hooks
├── lint-staged              # Pre-commit linting
├── postcss                  # PostCSS
├── tailwindcss              # Tailwind CSS
├── concurrently             # Parallel command execution
├── @tauri-apps/cli          # Tauri CLI
└── convex                   # Convex CLI
```

### Security Override Chain (pnpm.overrides)

The project applies **40+ security overrides** to patch known CVEs in transitive dependencies:

```
axios → 1.7.4          (CVE-2024-39338)
glob → 10.4.5          (CVE-2024-4067)
js-yaml → 4.1.1        (CVE-2023-2251)
vite → 6.0.12          (CVE-2025-24010, CVE-2025-30208, CVE-2025-31125)
tar → 6.2.1            (CVE-2024-28849, CVE-2024-43788)
cookie → 0.7.2         (CVE-2024-47764, CVE-2024-47765)
dompurify → 3.2.4      (Multiple CVEs)
esbuild → 0.25.0       (CVE-2024-27290)
ws → 8.17.1            (CVE-2024-37890)
qs → 6.15.1            (CVE-2022-24999)
path-to-regexp → 8.2.0 (CVE-2024-52798)
braces → 3.0.3         (CVE-2024-4068)
micromatch → 4.0.8     (CVE-2024-4067)
and 30+ more...
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Browser / Desktop App                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────────┐  │
│  │ Next.js  │  │  Tauri   │  │  Local   │  │   Convex Client   │  │
│  │ (Web UI) │  │ (Desktop)│  │ Sandbox  │  │  (Real-time sync) │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────────┬──────────┘  │
│       │              │             │                  │             │
└───────┼──────────────┼─────────────┼──────────────────┼─────────────┘
        │              │             │                  │
        ▼              ▼             ▼                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Network Layer                                │
│  HTTP/HTTPS    WebSocket    Deep Links (hwai://)    WebSocket       │
└───────┬──────────────┬──────────────────────┬───────────────────────┘
        │              │                      │
        ▼              ▼                      ▼
┌───────────────┐ ┌──────────┐ ┌──────────────────────────┐
│  Next.js API  │ │ WorkOS   │ │     Convex Backend       │
│  Routes (35+) │ │ AuthKit  │ │  ┌────────────────────┐  │
│               │ │          │ │  │  Database (18+     │  │
│  /api/chat    │ │  JWT     │ │  │  tables)           │  │
│  /api/auth/*  │ │  Auth    │ │  │                    │  │
│  /api/stripe* │ │  MFA     │ │  │  Server Functions  │  │
│  /api/team/*  │ │  Orgs    │ │  │  (30+ files)       │  │
│  /api/mfa/*   │ │          │ │  │                    │  │
│  /api/health  │ │          │ │  │  File Storage      │  │
└───────┬───────┘ └──────────┘ │  │  (S3 integration)  │  │
        │                      │  │                    │  │
        ▼                      │  │  Cron Jobs (3)     │  │
┌───────────────┐              │  │                    │  │
│   Stripe      │              │  │  Auth (WorkOS JWT) │  │
│  Payments     │              │  └────────────────────┘  │
│  Subscriptions│              └──────────┬───────────────┘
│  Extra Usage  │                         │
└───────────────┘                         │
        │                                 │
        ▼                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        External Services                             │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Upstash  │  │  AWS S3  │  │PostHog   │  │   Centrifugo     │   │
│  │ Redis    │  │  Storage │  │Analytics │  │   (Real-time)    │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │OpenRouter│  │  OpenAI  │  │  Google  │  │   Anthropic      │   │
│  │ (Default)│  │ (Fallback)│ │ (Fallback)│ │   (Fallback)     │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘   │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────────────────┐   │
│  │  Ollama  │  │  E2B    │  │   Trigger.dev                  │   │
│  │ (Local)  │  │ Sandbox │  │   (Background Jobs, 1hr max)   │   │
│  └──────────┘  └──────────┘  └────────────────────────────────┘   │
│                                                                     │
│  ┌──────────┐  ┌──────────┐                                        │
│  │Perplexity│  │  Jina    │  (Web Search APIs)                     │
│  └──────────┘  └──────────┘                                        │
└─────────────────────────────────────────────────────────────────────┘

        ▼                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Sandbox Environments                          │
│                                                                     │
│  ┌─────────────────────┐  ┌──────────────────────────────────────┐  │
│  │  E2B Cloud Sandbox  │  │  Local Docker Sandbox (Kali Linux)   │  │
│  │  (Managed)          │  │  ┌────────────────────────────────┐  │  │
│  └─────────────────────┘  │  │  Tools: nmap, sqlmap, msf,    │  │  │
│                            │  │  hydra, john, hashcat,       │  │  │
│  ┌─────────────────────┐  │  │  burpsuite, gobuster, wfuzz, │  │  │
│  │  Tauri Desktop PTY  │  │  │  ffuf, nuclei, subfinder,    │  │  │
│  │  (portable-pty)     │  │  │  httpx, naabu, katana,       │  │  │
│  │  HTTP Command API   │  │  │  interactsh, xsstrike,       │  │  │
│  │  Deep Link Auth     │  │  │  paramspider, jwt_tool,      │  │  │
│  └─────────────────────┘  │  │  gitdumper, + 80+ more      │  │  │
│                            │  └────────────────────────────────┘  │  │
│                            └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

*End of Architecture Report*