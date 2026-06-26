# HackWithAI v2 - System Architecture

## Overview

HackWithAI v2 is a full-stack AI-powered penetration testing platform built on Next.js 16, React 19, and TypeScript. It leverages multiple AI providers, secure sandbox environments, and real-time collaboration tools to assist authorized cybersecurity professionals.

**Base Technology**: HackWithAI v2  
**Frontend**: Next.js 16 (App Router), React 19, Tailwind CSS v4, Radix UI  
**Backend**: Convex (serverless database + backend functions), WorkOS (auth)  
**AI Engine**: Multi-provider (OpenRouter, OpenAI, Google Gemini, Anthropic Claude, Ollama)  
**Sandbox**: E2B (cloud), Docker/Kali (local), Centrifugo (real-time relay)  
**Task Runner**: Trigger.dev (durable execution for long-running agents)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │   Web App    │  │ Desktop App  │  │  Mobile Web  │  │ Shared Chats   │  │
│  │  (Next.js)   │  │   (Tauri)    │  │  (PWA)       │  │ (Public URLs)  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └────────────────┘  │
└─────────┼─────────────────┼─────────────────┼──────────────────────────────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                            │
                    ┌───────▼────────┐
                    │   WorkOS Auth  │
                    │  (SSO, MFA)    │
                    └───────┬────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────────────┐
│                           API LAYER                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                     Next.js 16 App Router                            │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────────┐  │   │
│  │  │ /api/chat   │ │ /api/agent  │ │ /api/team   │ │ /api/sandbox   │  │   │
│  │  │   (stream)  │ │  (long)     │ │  (billing)  │ │  (presence)    │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └────────────────┘  │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────────────┐  │   │
│  │  │ /api/mfa    │ │ /api/sub    │ │ /api/ref    │ │ /api/health    │  │   │
│  │  │  (factors)  │ │ (webhooks)  │ │  (referral) │ │  (monitoring)  │  │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐  ┌────────▼────────┐  ┌──────▼───────┐
│   Convex     │  │   Trigger.dev   │  │  E2B / Local │
│  (Database)  │  │ (Agent Runner)  │  │   Sandbox    │
└───────┬──────┘  └─────────────────┘  └──────────────┘
        │
┌───────▼─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │    Users     │  │    Chats     │  │   Messages   │  │    Files       │  │
│  │  (profiles)  │  │ (sessions)   │  │  (history)   │  │ (S3/Convex)    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │    Teams     │  │  Subscriptions│  │   Notes      │  │   Referrals    │  │
│  │  (members)   │  │   (Stripe)    │  │  (memory)    │  │   (tracking)   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Breakdown

### 1. Frontend (`app/`)

| Directory         | Purpose                                                      |
| ----------------- | ------------------------------------------------------------ |
| `app/(chat)/`     | Main chat interface with sidebar, message stream, and input  |
| `app/components/` | React components (dialogs, selectors, chat UI, settings)     |
| `app/hooks/`      | Custom hooks (auth, file upload, sandbox preference, typing) |
| `app/api/`        | API routes for chat streaming, webhooks, authentication      |
| `app/contexts/`   | React context providers (global state, todo blocks)          |
| `app/share/`      | Public shared chat pages                                     |
| `app/download/`   | Desktop app download page                                    |

**Key Components:**

- `ChatLayout` - Responsive layout with collapsible sidebar
- `ModelSelector` - AI model/tier selection with cost indicators
- `SandboxSelector` - Cloud (E2B) vs Local (Docker) vs Desktop sandbox switching
- `DataStreamProvider` - Real-time message streaming and tool execution

### 2. AI Engine (`lib/ai/`)

| File               | Purpose                                                                |
| ------------------ | ---------------------------------------------------------------------- |
| `providers.ts`     | Multi-provider factory (OpenRouter, OpenAI, Google, Anthropic, Ollama) |
| `tools/*.ts`       | AI tool definitions (terminal, file, web search, notes, URL, proxy)    |
| `tools/utils/`     | Tool utilities (sandbox adapters, uploaders, health checks)            |
| `system-prompt.ts` | Dynamic system prompt generation with persona and sandbox context      |

**Provider Modes:**

- `openrouter` - Unified cloud provider (default)
- `openai` - Direct OpenAI API
- `google` - Direct Gemini API
- `anthropic` - Direct Claude API
- `ollama` - Local Ollama instance (Qwen, DeepSeek, Mistral, Llama)

### 3. Backend Services

#### Convex (`convex/`)

Serverless backend with real-time subscriptions:

- **Tables**: `users`, `chats`, `messages`, `files`, `notes`, `teams`, `subscriptions`
- **Functions**: Queries, mutations, and actions for data operations
- **Auth Integration**: WorkOS session validation via JWT

#### WorkOS (`lib/auth/`)

Enterprise authentication:

- SSO (SAML, OIDC)
- Multi-Factor Authentication (TOTP)
- Organization/Team management
- Session management with cookie encryption

#### Trigger.dev (`trigger/`)

Durable task execution:

- Long-running agent loops
- Background job processing
- Resumable workflows

### 4. Sandbox Systems

| Type        | Technology           | Use Case                                       |
| ----------- | -------------------- | ---------------------------------------------- |
| **Cloud**   | E2B + Centrifugo     | Default agent execution in isolated containers |
| **Local**   | Docker (Kali-based)  | Air-gapped environments, custom tool sets      |
| **Desktop** | Tauri + Local bridge | Native app with direct host access             |

**Sandbox Image (`docker/Dockerfile`):**

- Base: `kalilinux/kali-rolling`
- 50+ pre-installed tools: nmap, sqlmap, nuclei, gobuster, ffuf, etc.
- Browser automation: Chromium + agent-browser
- Document generation: reportlab, python-docx, pandas

### 5. Real-Time Infrastructure

**Centrifugo** (`docker/centrifugo/`)

- WebSocket server for sandbox stdout/stderr streaming
- JWT-authenticated channels
- Presence tracking for active sandboxes

---

## Data Flow

### Chat Request Flow

```
User Input
    │
    ▼
┌─────────────┐
│ Next.js API │  ──► Auth check (WorkOS)
│  /api/chat  │  ──► Rate limiting (Redis/Upstash)
└──────┬──────┘
       │
       ▼
┌──────────────┐
│ Chat Stream  │  ──► Build system prompt (persona + sandbox context)
│   Handler    │  ──► Select AI provider based on PROVIDER_MODE
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ AI Provider  │  ──► Stream LLM response with tool calls
│  (Vercel AI  │  ──► Handle reasoning, multimodal, encrypted blobs
│    SDK)      │
└──────┬───────┘
       │
       ├──────────────────────┬──────────────────────┐
       ▼                      ▼                      ▼
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│ Text Reply  │      │ Tool Call    │      │ Agent Mode   │
│ (streaming) │      │ (terminal,   │      │ (Trigger.dev │
│             │      │ file, web)   │      │  durable run)│
└─────────────┘      └──────┬───────┘      └──────────────┘
                            │
                    ┌───────┴───────┐
                    ▼               ▼
            ┌──────────┐    ┌──────────┐
            │ E2B Cloud│    │ Local    │
            │ Sandbox  │    │ Sandbox  │
            └──────────┘    └──────────┘
```

### File Upload Flow

```
User drops file
    │
    ▼
┌─────────────┐     ┌─────────────┐
│ Client      │────►│ Convex      │
│ Validation  │     │ Storage or  │
│             │     │ S3 Upload   │
└──────┬──────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│ File Parser │  ──► PDF, DOCX, XLSX, PPTX, images
│ (mammoth,   │  ──► Text extraction and chunking
│  pdfjs,     │
│  marked)    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Message     │
│ Attachment  │
└─────────────┘
```

---

## Security Architecture

### Authentication

- **WorkOS AuthKit**: Passwordless and SSO authentication
- **MFA**: TOTP-based enrollment and verification
- **Session**: Iron-session encrypted cookies with cross-tab token sharing

### Authorization

- **Subscription Tiers**: free, pro, pro-plus, ultra, team
- **Feature Flags**: WorkOS organization-level entitlement checks
- **Rate Limiting**: Token bucket per user (Redis/Upstash)

### Data Protection

- **File Storage**: S3 with presigned URLs or Convex internal storage
- **PII Redaction**: Automatic error message sanitization
- **Sandbox Isolation**: E2B ephemeral containers, no host access

### Audit & Compliance

- **PostHog**: Tool usage events, error tracking, funnel analytics
- **Chat Logging**: Structured logs for compliance review
- **Suspension System**: Automated abuse detection

---

## Technology Stack

| Layer      | Technology        | Version         |
| ---------- | ----------------- | --------------- |
| Framework  | Next.js           | 16.2.7          |
| UI Library | React             | 19.2.7          |
| Language   | TypeScript        | 6.0.3           |
| Styling    | Tailwind CSS      | 4.3.0           |
| Components | Radix UI          | Latest          |
| Icons      | Lucide React      | 1.17.0          |
| State      | Convex React      | 1.40.0          |
| Auth       | WorkOS AuthKit    | 4.1.1           |
| AI SDK     | Vercel AI SDK     | 6.0.196         |
| Database   | Convex            | 1.40.0          |
| Tasks      | Trigger.dev       | 4.4.6           |
| Tests      | Jest + Playwright | 30.4.2 / 1.60.0 |

---

## Scalability Considerations

### Horizontal Scaling

- Next.js app can be deployed across multiple containers behind a load balancer
- Convex scales automatically (serverless)
- E2B sandboxes scale elastically

### Caching

- Chat message lists cached via Convex subscriptions
- File URLs cached with S3 presigned URL rotation
- LocalStorage for UI preferences and sidebar state

### Performance

- Turbopack for fast development builds
- Standalone Next.js output for minimal Docker image
- Image optimization disabled (handled by CDN)
- Streaming responses for low-latency UX

---

## Extension Points

### Adding a New AI Provider

1. Install provider package: `pnpm add @ai-sdk/provider-name`
2. Add to `lib/ai/providers.ts`:
   ```typescript
   import { createProvider } from "@ai-sdk/provider-name";
   const provider = createProvider({ apiKey: process.env.PROVIDER_API_KEY });
   ```
3. Add model map in `buildProviderMap()`
4. Add environment variable to `.env.local.example`
5. Update `INSTALLATION.md` and `DEPLOYMENT.md`

### Adding a New Tool

1. Define tool schema in `lib/ai/tools/my-tool.ts`
2. Export tool function and parameters
3. Register in `lib/ai/tools/index.ts`
4. Add UI handler in `app/components/DataStreamProvider.tsx` or equivalent

### Custom Sandbox Image

1. Edit `docker/Dockerfile`
2. Add tools via `apt-get` or binary downloads
3. Build: `pnpm run docker:build`
4. Update `lib/system-prompt.ts` tool list
