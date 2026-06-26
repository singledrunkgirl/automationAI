# HackWithAI v2 — Tasks

## Current Status

The project has been analyzed and the immediate blocker (orphaned `next-server` on port 3006) has been resolved. The application starts and serves correctly on port 3002 with Convex on port 3210.

## Active Issues

### Priority: High

| # | Issue | Impact | Status |
|---|-------|--------|--------|
| H1 | Port 3000 occupied by unknown system process | Next.js falls back to port 3002 | Needs investigation |
| H2 | `.env.local` BASE_URL mismatch (`localhost:3006` vs actual `3002`) | Desktop app config, auth callbacks may target wrong port | Needs update |
| H3 | Convex running without cloud account link | Cloud features, deployment unavailable | Needs configuration |

### Priority: Medium

| # | Issue | Impact | Status |
|---|-------|--------|--------|
| M1 | `pnpm.overrides` field deprecated in `package.json` | Build warnings, future pnpm incompatibility | Migrate to `pnpm-workspace.yaml` |
| M2 | Next.js `middleware` convention deprecated | Warnings, future Next.js incompatibility | Migrate to `proxy` convention |
| M3 | `NEXT_PUBLIC_CONVEX_SITE_URL` not auto-set in `.env.local` | Manual configuration required | Document or auto-configure |
| M4 | Desktop app not verified in current session | Unknown if Tauri compilation works | Test desktop dev/build |

### Priority: Low

| # | Issue | Impact | Status |
|---|-------|--------|--------|
| L1 | npm config warnings in startup logs | Noise in logs, no functional impact | Clean up npmrc |
| L2 | Convex minor update available (1.40.0 → 1.41.0) | Missing latest features/bugfixes | Update dependency |
| L3 | Convex AI files not installed | Feature not available | Install or disable message |
| L4 | `codex_thread_id` field is legacy in chats table | Dead code in schema | Remove or document |

## Task Breakdown

### Phase 1: Stabilization (PRIORITY)

- [ ] **T1.1** — Investigate port 3000 occupation
  - Identify process holding port 3000 (`sudo lsof -i :3000`)
  - Kill/relocate if possible, or document as permanent
- [ ] **T1.2** — Fix `.env.local` configuration
  - Align `NEXT_PUBLIC_BASE_URL` with actual dev server port
  - Verify all URL-dependent features (auth callbacks, desktop handoff)
- [ ] **T1.3** — Verify desktop app development flow
  - Run `pnpm desktop:dev` and test Tauri compilation
  - Test Tauri IPC commands from web app
  - Test PTY session functionality
- [ ] **T1.4** — Run full test suite
  - `pnpm test` (Jest unit tests)
  - `pnpm typecheck` (TypeScript)
  - `pnpm lint` (ESLint)

### Phase 2: Configuration Cleanup

- [ ] **T2.1** — Migrate pnpm config from `package.json` to `pnpm-workspace.yaml`
  - Move `overrides`, `patchedDependencies`, `onlyBuiltDependencies`
  - Verify pnpm install succeeds
  - Update documentation
- [ ] **T2.2** — Migrate middleware to proxy convention
  - Rename `middleware.ts` → implement `proxy` export pattern
  - Verify all auth gating, routing, CSP still work
- [ ] **T2.3** — Clean up npm config warnings
  - Audit `.npmrc` for deprecated/unnecessary keys
  - Remove or update as needed

### Phase 3: Feature Verification

- [ ] **T3.1** — Test E2B sandbox functionality
  - Verify E2B API key is valid
  - Run `pnpm e2b:build:dev` to build sandbox template
  - Test sandbox creation and command execution
- [ ] **T3.2** — Test local sandbox client
  - Run `pnpm local-sandbox`
  - Verify Convex connection and Centrifugo subscription
  - Test command execution and PTY sessions
- [ ] **T3.3** — Test AI provider connectivity
  - OpenRouter (primary)
  - OpenAI (fallback)
  - Google Generative AI
  - Anthropic
  - Ollama (local)
- [ ] **T3.4** — Test E2E test suite
  - Run `pnpm test:e2e:setup` (create test users)
  - Run `pnpm test:e2e:chromium`

### Phase 4: Documentation

- [ ] **T4.1** — Complete development environment setup guide
  - Document required API keys and services
  - Document local-only mode limitations
  - Document desktop app build requirements
- [ ] **T4.2** — Update README.md with current information
  - Project overview and architecture
  - Quick start guide
  - Available scripts
- [ ] **T4.3** — Create CONTRIBUTING.md
  - Code conventions
  - Testing guidelines
  - PR process

### Future Enhancements

- [ ] **F1** — Implement AI tool pipeline visualization
- [ ] **F2** — Add agent workflow templates
- [ ] **F3** — Implement collaborative real-time terminal sharing
- [ ] **F4** — Add report generation templates
- [ ] **F5** — Implement custom tool plugin system
- [ ] **F6** — Add vulnerability database integration
- [ ] **F7** — Implement automated retesting workflows
- [ ] **F8** — Add PCI DSS / OWASP compliance checklists

## Testing Inventory

| Suite | Framework | Location | Files |
|-------|-----------|----------|-------|
| Unit | Jest | `**/__tests__/` | 200+ test files |
| E2E | Playwright | `e2e/` | 10 spec files |
| Convex | Jest | `convex/__tests__/` | 15 test files |
| lib | Jest | `lib/**/__tests__/` | 30+ test files |
| Components | Jest | `app/components/__tests__/` | 12 test files |
| Hooks | Jest | `app/hooks/__tests__/` | 5 test files |
| API | Jest | `app/api/**/__tests__/` | 8 test files |
| Desktop | Jest | `app/services/__tests__/` | 1 test file |

## Services Required

| Service | Purpose | Status |
|---------|---------|--------|
| Convex Cloud | Backend DB + Functions | Not linked (local mode active) |
| WorkOS | Authentication | Not configured in local mode |
| OpenRouter | AI provider | API key in `.env.local` |
| E2B | Cloud sandbox | API key configured |
| Centrifugo | Real-time relay | Need container or hosted instance |
| Upstash Redis | Rate limiting | URL configured |
| Stripe | Payments | Only for production |
| PostHog | Analytics | Disabled in local mode |
| Trigger.dev | Background jobs | Needs cloud or self-hosted |
