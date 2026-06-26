# HackWithAI v2 — Architecture

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        HackWithAI v2 Platform                        │
│                                                                      │
│  ┌─────────────────────┐     ┌───────────────────────────────────┐  │
│  │   Next.js Web App    │     │        Tauri Desktop App           │  │
│  │   (React 19, TS 6)   │◄───►│   (Rust backend + WebView)         │  │
│  │                      │ IPC │                                    │  │
│  │  app/                 │     │  packages/desktop/                 │  │
│  │  ├── (chat)/          │     │  ├── src/index.html (loader)      │  │
│  │  ├── share/[id]/      │     │  └── src-tauri/src/               │  │
│  │  ├── api/             │     │      ├── main.rs (entry)          │  │
│  │  ├── components/      │     │      ├── lib.rs (commands+HTTP)   │  │
│  │  ├── hooks/           │     │      ├── platform.rs (cross-os)   │  │
│  │  └── services/        │     │      └── pty.rs (terminal)        │  │
│  │                       │     │                                    │  │
│  │  lib/                 │     │  Commands: exec, read/write files  │  │
│  │  ├── ai/              │     │  PTY sessions, auth, updates       │  │
│  │  ├── chat/            │     └───────────────────────────────────┘  │
│  │  ├── api/             │                                            │
│  │  ├── auth/            │                                            │
│  │  ├── billing/         │                                            │
│  │  ├── rate-limit/      │                                            │
│  │  ├── centrifugo/      │                                            │
│  │  └── utils/           │                                            │
│  │                       │                                            │
│  │  convex/              │                                            │
│  │  ├── schema.ts        │                                            │
│  │  ├── chats.ts         │                                            │
│  │  ├── messages.ts      │                                            │
│  │  ├── sharedChats.ts   │                                            │
│  │  ├── fileStorage.ts   │                                            │
│  │  ├── s3Actions.ts     │                                            │
│  │  ├── extraUsage.ts    │                                            │
│  │  ├── referrals.ts     │                                            │
│  │  ├── unitEconomics.ts │                                            │
│  │  ├── localSandbox.ts  │                                            │
│  │  ├── crons.ts         │                                            │
│  │  └── lib/utils.ts     │                                            │
│  └──────────┬───────────┘                                            │
│             │                                                        │
│    ┌────────┴────────┬──────────────┐                               │
│    ▼                 ▼              ▼                                │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐                          │
│  │  Convex  │  │ Centrifugo │  │   E2B    │                          │
│  │ (Real-time│  │ (WebSocket │  │ (Kali    │                          │
│  │  DB+Funcs)│  │  Pub/Sub)  │  │  Sandbox)│                          │
│  └──────────┘  └─────┬─────┘  └──────────┘                          │
│                      │                                               │
│              ┌───────▼────────┐                                     │
│              │  Local Sandbox │                                     │
│              │  (@hwai/local) │                                     │
│              │  Node.js CLI   │                                     │
│              │  node-pty,     │                                     │
│              │  Centrifuge    │                                     │
│              └────────────────┘                                     │
└──────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
HackWithAI/
├── app/                          # Next.js App Router (pages, API routes, components)
│   ├── (chat)/                   # Main chat route group
│   │   ├── layout.tsx            # Chat route layout (auth gating)
│   │   ├── page.tsx              # Home/chat page
│   │   └── c/[id]/page.tsx       # Specific chat page
│   ├── api/                      # API route handlers (30+ endpoints)
│   │   ├── chat/                 # Chat API (main + stream)
│   │   ├── agent-long/           # Long-running agent API
│   │   ├── subscribe/            # Subscription management
│   │   ├── mfa/                  # MFA enrollment/verification
│   │   ├── team/                 # Team management
│   │   ├── referrals/            # Referral system
│   │   └── ...                   # 15+ more endpoint groups
│   ├── share/[shareId]/          # Shared chat view
│   ├── components/               # Page-level React components (70+ files)
│   │   ├── ChatInput/            # Chat input subsystem
│   │   ├── ModelSelector/        # AI model picker
│   │   ├── tools/                # Tool result renderers
│   │   ├── usage/                # Usage display components
│   │   ├── extra-usage/          # Extra-usage purchase UI
│   │   └── ...                   # Dialogs, panels, settings tabs
│   ├── hooks/                    # React hooks (15+)
│   ├── services/                 # Client services (desktop-sandbox bridge)
│   └── contexts/                 # React contexts (GlobalState, TodoBlock, etc.)
│
├── convex/                       # Convex backend (24 tables, 100+ functions)
│   ├── schema.ts                 # Database schema (640 lines)
│   ├── auth.config.ts            # WorkOS JWT auth configuration
│   ├── chats.ts                  # Chat CRUD
│   ├── messages.ts               # Message CRUD + search
│   ├── chatStreams.ts            # Stream lifecycle management
│   ├── sharedChats.ts            # Public/private sharing
│   ├── fileStorage.ts            # File upload/download/delete
│   ├── s3Actions.ts              # S3 presigned URL generation
│   ├── s3Cleanup.ts              # S3 orphan file cleanup
│   ├── extraUsage.ts             # Prepaid balance management
│   ├── teamExtraUsage.ts         # Team-wide extra-usage
│   ├── referrals.ts              # Referral codes + attribution
│   ├── notes.ts                  # Notes CRUD + search
│   ├── feedback.ts               # User feedback collection
│   ├── localSandbox.ts           # Local sandbox connection lifecycle
│   ├── unitEconomics.ts          # Revenue/cost tracking
│   ├── crons.ts                  # Scheduled cron jobs
│   ├── redisPubsub.ts            # Redis pub/sub for cancellation
│   └── lib/                      # Backend utilities
│
├── components/                   # Shared UI components
│   ├── ui/                       # shadcn/ui primitives (30+ components)
│   ├── ai-elements/              # AI SDK UI elements
│   ├── icons/                    # SVG icons
│   └── ConvexClientProvider.tsx  # Convex React provider
│
├── lib/                          # Core business logic (100+ modules)
│   ├── ai/                       # AI provider configuration + tools
│   │   ├── providers.ts          # Multi-provider AI setup (555 lines)
│   │   ├── tools/                # AI tool definitions (10 tools)
│   │   │   ├── index.ts          # Tool registry
│   │   │   ├── run-terminal-cmd.ts
│   │   │   ├── interact-terminal-session.ts
│   │   │   ├── get-terminal-files.ts
│   │   │   ├── file.ts
│   │   │   ├── web-search.ts
│   │   │   ├── open-url.ts
│   │   │   ├── todo-write.ts
│   │   │   ├── notes.ts
│   │   │   ├── proxy-tool.ts
│   │   │   └── utils/            # Sandbox managers, PTY adapters, guardrails
│   │   └── openrouter-attribution.ts
│   │
│   ├── api/                      # API handler core logic
│   │   ├── chat-handler.ts       # Main chat endpoint (1539 lines)
│   │   ├── chat-stream-helpers.ts
│   │   └── agent-stream-runner.ts
│   │
│   ├── chat/                     # Chat processing
│   │   ├── chat-processor.ts
│   │   ├── agent-routing.ts
│   │   ├── stop-conditions.ts
│   │   ├── doom-loop-detection.ts
│   │   ├── budget-monitor.ts
│   │   ├── summarization/
│   │   └── compaction/
│   │
│   ├── auth/                     # Authentication utilities
│   │   ├── get-user-id.ts
│   │   ├── entitlements.ts
│   │   └── feature-flags.ts
│   │
│   ├── billing/                  # Stripe billing logic
│   ├── rate-limit/               # Rate limiting (token bucket, sliding window)
│   ├── centrifugo/               # Centrifugo real-time messaging
│   ├── analytics/                # PostHog analytics helpers
│   ├── db/                       # Convex client + DB actions
│   ├── utils/                    # 35+ utility modules
│   └── system-prompt.ts          # AI system prompt assembly (511 lines)
│
├── packages/                     # Monorepo sub-packages
│   ├── desktop/                  # Tauri desktop app
│   │   ├── src/index.html        # App loader (redirects to web app)
│   │   ├── scripts/build.js      # Build-time URL injection
│   │   └── src-tauri/            # Rust backend
│   │       ├── src/
│   │       │   ├── main.rs       # Entry point
│   │       │   ├── lib.rs        # Tauri commands + HTTP server (1640 lines)
│   │       │   ├── platform.rs   # Cross-platform process mgmt (243 lines)
│   │       │   └── pty.rs        # PTY session manager (285 lines)
│   │       ├── tauri.conf.json   # Production config
│   │       └── tauri.dev.conf.json # Dev config
│   │
│   └── local/                    # Local sandbox client (Node.js CLI)
│       ├── src/
│       │   ├── index.ts          # Main sandbox client (1215 lines)
│       │   ├── process-runner.ts # PTY process manager (260 lines)
│       │   └── utils.ts          # Platform utilities
│       └── package.json          # @hwai/local v0.8.3
│
├── trigger/                      # Trigger.dev background tasks
│   ├── agent-long.ts             # Agent-long task (1845 lines)
│   ├── streams.ts                # Stream type definitions
│   └── stream-ids.ts             # Stream ID constants
│
├── scripts/                      # Development & ops scripts (14 files)
├── e2e/                          # Playwright E2E tests
├── docker/                       # Docker configuration
│   ├── Dockerfile                # Sandbox image (Kali + 50 pentest tools)
│   └── centrifugo/               # Centrifugo server config + deploy guide
├── e2b/                          # E2B sandbox build scripts
├── types/                        # TypeScript type definitions
├── public/                       # Static assets + PWA icons
├── patches/                      # Patched dependencies (ai@6.0.196)
├── __mocks__/                    # Jest module mocks
├── local-mocks/                  # Local-only development mocks
└── .github/                      # CI/CD workflows + Dependabot
```

## Data Flow

### Chat Request Flow
```
User Input (browser/desktop)
  │
  ▼
POST /api/chat  (app/api/chat/route.ts)
  │
  ├─► Auth: WorkOS JWT validation (lib/auth/get-user-id.ts)
  ├─► Rate Limit: Upstash Redis token bucket (lib/rate-limit/)
  ├─► Files: Process attachments (convex/fileStorage.ts)
  ├─► System Prompt: Assemble context (lib/system-prompt.ts)
  ├─► AI Stream: call streamText() via Vercel AI SDK (lib/api/chat-handler.ts)
  │     │
  │     ├─► Tool Calls → Sandbox execution (lib/ai/tools/)
  │     │     ├─► E2B cloud sandbox
  │     │     ├─► Desktop Tauri backend (local HTTP server)
  │     │     └─► Local sandbox client (Centrifugo WebSocket)
  │     │
  │     └─► Streaming → UI chunks via Server-Sent Events
  │
  ├─► Persistence: Save messages to Convex (convex/messages.ts)
  ├─► Analytics: Log to PostHog (lib/analytics/)
  └─► Response: SSE stream to client
```

### Long-Running Agent Flow
```
POST /api/agent-long
  │
  ├─► Start Trigger.dev task (trigger/agent-long.ts)
  │     │
  │     ├─► Fetch context from Convex
  │     ├─► Loop: generate → tool calls → persist → continue
  │     └─► Stream UI updates via Trigger.dev realtime
  │
  └─► Client receives updates via Trigger.dev hooks (app/hooks/useAutoResume.ts)
```

### Desktop App Flow
```
Tauri Window loads APP_URL
  │
  ├─► index.html → HEAD check → redirect to web app
  │
  ▼
Web app detects Tauri (window.__TAURI__)
  │
  ├─► Tauri IPC Commands:
  │     execute_command()
  │     read_local_file()
  │     execute_pty_create() / execute_pty_input() / execute_pty_resize()
  │
  └─► Local HTTP Server (127.0.0.1:random):
        /execute, /execute/stream
        /files/read, /files/write, /files/remove, /files/list
```

### Local Sandbox Flow
```
User runs: npx @hwai/local --token TOKEN
  │
  ├─► Convex: connect() mutation → get centrifugoToken
  ├─► Centrifugo: connect WebSocket → subscribe sandbox channel
  │
  ▼
Commands arrive via Centrifugo messages
  │
  ├─► Spawn child process / PTY session
  ├─► Stream stdout/stderr via Centrifugo publish
  └─► Send exit code
```

## Database Schema (24 Tables)

| Table | Purpose | Key Indexes |
|-------|---------|-------------|
| `chats` | Chat sessions | by_user_and_updated, by_share_id, search_title |
| `chat_summaries` | Conversation summaries | by_chat_id |
| `messages` | Chat messages | by_chat_id, by_user_id, search_content |
| `files` | Uploaded/generated files | by_user_id, by_s3_key |
| `feedback` | User thumbs up/down | — |
| `user_customization` | AI personality + settings | by_user_id |
| `extra_usage` | Prepaid balance (per user) | by_user_id |
| `team_extra_usage` | Prepaid balance (per org) | by_org |
| `team_member_usage` | Per-member caps (org) | by_org_user |
| `referral_codes` | Referral links | by_user_id, by_code |
| `referral_attributions` | Referral tracking | by_referrer, by_referred |
| `referral_rewards` | Awarded bonuses | by_idempotency_key |
| `user_suspensions` | Fraud/dispute suspensions | by_user_and_status |
| `memories` | AI memory entries | by_user_and_update_time |
| `notes` | User notes (with categories) | by_user_and_category, search_notes |
| `temp_streams` | Temporary chat streams | by_chat_id |
| `local_sandbox_tokens` | Local client auth tokens | by_user_id, by_token |
| `local_sandbox_connections` | Connection lifecycle | by_user_and_status |
| `usage_logs` | Per-request usage (append-only) | by_user, by_user_and_model |
| `revenue_events` | Revenue ledger (append-only) | by_idempotency_key, by_entity |
| `paid_start_events` | Paid conversion ledger | by_entity_day |
| `paid_start_mix_daily` | Daily paid conversion rollup | by_segment |
| `unit_economics_daily` | Daily P&L per entity | by_entity_day |
| `processed_webhooks` | Stripe webhook idempotency | by_event_id |

## AI Tools

| Tool | Purpose |
|------|---------|
| `run_terminal_cmd` | Execute commands in sandbox |
| `interact_terminal_session` | Interact with PTY sessions |
| `get_terminal_files` | List/retrieve terminal files |
| `file` | Read/write/view files |
| `web_search` | Web search via Perplexity |
| `open_url` | Open HTTP URLs |
| `todo_write` | Manage task lists |
| `create_note` | Create notes |
| `list_notes` | List/search notes |
| `update_note` | Edit notes |
| `delete_note` | Remove notes |
| `proxy_tool` | Caido proxy integration (kill-switched) |

## Security Model

- **Dual Auth**: Client functions use WorkOS JWT; backend functions use service key validation
- **CSP**: Strict Content-Security-Policy in Tauri (relaxed in dev)
- **Rate Limiting**: Token bucket per user, tiered limits (Upstash Redis)
- **Sandbox Isolation**: Commands execute in Docker (E2B) or separate process (Tauri/local)
- **File Storage**: Convex storage + AWS S3 with presigned URLs
- **Webhook Idempotency**: Processed event tracking prevents duplicate Stripe webhook processing
- **User Suspensions**: Stripe fraud/dispute webhooks trigger automated suspensions
- **Content Moderation**: AI response filtering (lib/moderation.ts)
