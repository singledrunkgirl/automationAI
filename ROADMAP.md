# HackWithAI v2 — Roadmap

## Current Version: 0.1.0

---

## Phase 1: Stabilization (Current Sprint)

**Goal**: Get the development environment fully operational and clean.

| Milestone | Tasks | Success Criteria |
|-----------|-------|-----------------|
| Port Resolution | T1.1, T1.2 | Next.js runs on consistent port (3000 or documented port) |
| Desktop App Verified | T1.3 | Tauri dev mode loads web app correctly |
| Test Suite Green | T1.4 | All Jest + TypeScript checks pass |
| Config Clean | T2.1, T2.2, T2.3 | Zero warnings on `pnpm dev` |

**Timeline**: 1-2 days

---

## Phase 2: Feature Verification & Hardening

**Goal**: Ensure all core features work end-to-end.

| Milestone | Tasks | Success Criteria |
|-----------|-------|-----------------|
| E2B Sandbox | T3.1 | AI agent executes tools in cloud sandbox |
| Local Sandbox | T3.2 | Commands relay via Centrifugo to local client |
| AI Providers | T3.3 | All configured providers respond correctly |
| E2E Tests | T3.4 | Playwright suite passes for critical paths |
| Documentation | T4.1, T4.2 | README + setup guide complete |

**Timeline**: 2-3 days

---

## Phase 3: MVP Polish

**Goal**: Ship a viable alpha release.

| Feature | Description | Priority |
|---------|-------------|----------|
| Auth Flow Polish | Error recovery, loading states, token refresh | High |
| Chat UX | Message editing, branching, search improvements | High |
| Tool Output Rendering | Consistent formatting, syntax highlighting, file previews | Medium |
| Rate Limiting UX | Clear messaging, progress indicators, upgrade prompts | Medium |
| Mobile Responsive | Basic mobile layout for key screens | Low |
| PWA Support | Offline capability, install prompt | Low |
| Error Boundaries | Graceful failure for all component trees | Medium |

---

## Phase 4: Beta Features

**Goal**: Expand capabilities for power users.

| Feature | Description |
|---------|-------------|
| Agent Workflow Templates | Pre-built workflows for common pentest scenarios (web app, network, API) |
| Custom AI Tool Development | Allow users to define custom tools with sandbox execution |
| Report Generation | Automated pentest report generation (PDF, DOCX, Markdown) |
| Vulnerability Tracking | Built-in vuln database with CVE lookup |
| Team Collaboration | Real-time shared chat, shared sandbox sessions |
| Script Library | Curated collection of pentest scripts accessible to agents |
| Model Fine-tuning | Custom system prompts per project/organization |

---

## Phase 5: Release Candidate

**Goal**: Production-ready v1.0.

| Feature | Description |
|---------|-------------|
| Enterprise SSO | SAML, OIDC integration via WorkOS |
| Audit Logging | Complete activity trail for compliance |
| RBAC | Role-based access control within organizations |
| Multi-region Sandbox | Deploy sandboxes in user's preferred region |
| On-premise Deployment | Self-hosted option with Kubernetes/Docker |
| API Access | Public API for third-party integrations |
| Plugin System | Community plugin marketplace |
| Performance Optimization | Streaming latency, sandbox startup time, context window efficiency |

---

## Phase 6: Post-1.0

| Feature | Description |
|---------|-------------|
| AI Model Marketplace | Community-trained models for specific security domains |
| Automated Remediation | Suggest and apply fixes for found vulnerabilities |
| Compliance Scanning | PCI DSS, HIPAA, SOC2 compliance checklists |
| Threat Intelligence Integration | Live threat feeds and IOC scanning |
| Red Team Automation | Multi-agent attack simulation |
| Integration Marketplace | Jira, Slack, Discord, GitHub, GitLab integrations |
| Mobile App | Native iOS/Android companion app |

---

## Release Schedule (Target)

| Version | Scope | Target |
|---------|-------|--------|
| v0.1.0 | Current: Initial development | Now |
| v0.2.0 | Phase 1 Complete: Stable dev environment | +2 days |
| v0.3.0 | Phase 2 Complete: All features verified | +5 days |
| v0.5.0 | Phase 3 Complete: MVP Polish | +2 weeks |
| v0.7.0 | Phase 4 Complete: Beta Features | +1 month |
| v0.9.0 | Phase 5 Complete: Release Candidate | +3 months |
| v1.0.0 | Production Release | +4 months |

---

## Architecture Evolution

### Current Architecture
- Monolithic Next.js app with Convex backend
- Tauri desktop wrapper around web app
- Direct provider integration (OpenRouter, OpenAI, etc.)

### Target Architecture (v1.0)
- Loosely coupled microservices
- Dedicated AI orchestration service
- Message queue for sandbox commands
- Multi-tenant Convex deployment
- CDN for static assets and sandbox images
- Edge functions for low-latency auth and routing

### Technology Radar

| Technology | Current | Near-term | Long-term |
|------------|---------|-----------|-----------|
| Next.js | 16.2 | Stay current | Evaluate alternatives |
| React | 19.2 | Stay current | — |
| Convex | 1.40 | 1.41+ | Evaluate scale limits |
| WorkOS | Staging | Production setup | Enterprise SSO |
| Tauri | 2.x | 2.x LTS | v3 when available |
| AI SDK | 6.0.196 | Patch updates | v7 when stable |
| Centrifugo | 5.x | 5.x stable | Evaluate NATS |
| Trigger.dev | 4.4 | 4.x stable | Evaluate alternatives |
| Tailwind | 4.3 | Stay current | — |
| TypeScript | 6.0 | Stay current | — |
