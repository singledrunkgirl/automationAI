# HackWithAI v2 — Master Plan

## Project Identity

| Field | Value |
|-------|-------|
| **Name** | HackWithAI v2 (`hwai-v2`) |
| **Purpose** | AI-powered penetration testing assistant |
| **Version** | 0.1.0 |
| **License** | Proprietary / Private |
| **Repository** | `/home/kali/HackWithAI` |

## Mission

HackWithAI v2 provides security professionals and ethical hackers with an AI-driven assistant capable of planning attacks, executing terminal commands in sandboxed environments, analyzing outputs, generating reports, and managing penetration testing workflows — all through a chat-based interface.

## Core Capabilities

1. **AI Chat Interface** — Multi-turn conversations with agent and ask modes
2. **Automated Tool Execution** — Run 50+ pentesting tools in isolated sandboxes
3. **Long-Running Agents** — Background agents via Trigger.dev (up to 1 hour)
4. **Cross-Platform** — Web app + Tauri desktop app (macOS, Windows, Linux)
5. **Local Execution** — Run commands on host OS via desktop app or local sandbox client
6. **File Handling** — Upload, analyze, and generate files (PDF, DOCX, JSON, etc.)
7. **Team Collaboration** — Organizations, shared chats, referral system
8. **Monetization** — Tiered subscriptions (Free/Pro/Pro+/Ultra/Team) with extra-usage credits

## Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| Next.js App Router | Server components, streaming, modern React patterns |
| Convex real-time DB | Replaces traditional REST/GraphQL; real-time sync, server functions |
| WorkOS AuthKit | Enterprise-ready auth with MFA, organizations, SSO |
| Vercel AI SDK | Unified multi-provider AI abstraction (OpenRouter, OpenAI, Google, Anthropic, Ollama) |
| Centrifugo | WebSocket relay for real-time sandbox command streaming |
| E2B Sandbox | Isolated cloud execution environment based on Kali Linux |
| Tauri v2 | Lightweight desktop wrapper with native OS access (vs Electron) |
| Trigger.dev | Durable background job execution for agent-long tasks |
| pnpm Monorepo | Efficient package management with patching support |

## Tech Stack

```
Frontend:   Next.js 16 + React 19 + TypeScript 6 + Tailwind CSS 4 + Radix UI
Backend:    Convex (real-time database + server functions)
AI:         Vercel AI SDK 6.0.196 (OpenRouter, OpenAI, Google, Anthropic, Ollama)
Auth:       WorkOS AuthKit (JWT, MFA, SSO, organizations)
Realtime:   Centrifugo v5 (WebSocket pub/sub)
Sandbox:    E2B (Kali Linux Docker) + local sandbox client
Desktop:    Tauri v2 (Rust + WebView)
Jobs:       Trigger.dev 4.4
Payments:   Stripe (subscriptions + extra-usage)
Analytics:  PostHog
Testing:    Jest (unit) + Playwright (E2E)
CI/CD:      GitHub Actions
Deploy:     Vercel + Docker Compose
```

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Next.js dev server | Operational | Falls back to port 3002 (3000 blocked) |
| Convex backend | Operational | Local mode, no cloud account linked |
| Desktop app | Needs verification | Not tested in current session |
| Local sandbox | Not tested | `@hwai/local` package present |
| E2B sandbox | Configured | API key set, templates defined |
| Tests | 200+ test files | Jest + Playwright configured |
| CI/CD | Configured | GitHub Actions workflows present |

## Known Issues (Post-Cleanup)

1. Port 3000 occupied by unidentified system process — Next.js falls back to 3002
2. `pnpm.overrides` field deprecated — should migrate to `pnpm-workspace.yaml`
3. `middleware` convention deprecated in Next.js — should migrate to `proxy`
4. `.env.local` has `NEXT_PUBLIC_BASE_URL=http://localhost:3006` but dev runs on 3002
5. Convex running without account link — cloud features unavailable
6. `NEXT_PUBLIC_CONVEX_SITE_URL` not auto-configured in `.env.local`

## Environment

| File | Purpose |
|------|---------|
| `.env.local` | Main development environment (real keys, `LOCAL_ONLY_MODE=true`) |
| `.env.local.example` | Template with all 80+ documented variables |
| `.env.e2e.example` | E2E test user credentials template |
| `.npmrc` | pnpm configuration |
| `convex/convex.config.ts` | Convex deployment configuration |
| `trigger.config.ts` | Trigger.dev project configuration |
| `vercel.json` | Vercel deployment (minimal) |

## Entry Points

| Command | Purpose |
|---------|---------|
| `pnpm dev` | Start Next.js + Convex (standard dev) |
| `pnpm dev:next` | Start Next.js only |
| `pnpm dev:convex` | Start Convex only |
| `pnpm dev:all` | Start Next.js + Convex + Trigger.dev |
| `pnpm build` | Production Next.js build |
| `pnpm start` | Production Next.js start |
| `pnpm desktop:dev` | Tauri desktop app (dev) |
| `pnpm desktop:build` | Tauri desktop app (production build) |
| `pnpm local-sandbox` | Local sandbox client |
| `pnpm test` | Jest unit tests |
| `pnpm test:e2e` | Playwright E2E tests |
| `pnpm setup` | First-run setup wizard |
