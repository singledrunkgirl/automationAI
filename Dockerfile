# =============================================================================
# HackWithAI v2 - Production Dockerfile
# =============================================================================
# Multi-stage build for Next.js 16 application
# Supports: Kali Linux, Ubuntu VPS, Docker Compose, Kubernetes
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Dependencies
# -----------------------------------------------------------------------------
FROM node:22-slim AS deps

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable && corepack prepare pnpm@10.33.2 --activate

WORKDIR /app

# Copy workspace config and package files
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY patches ./patches
COPY packages/desktop/package.json ./packages/desktop/package.json
COPY packages/local/package.json ./packages/local/package.json

# Install dependencies (production + dev needed for build)
RUN pnpm install --frozen-lockfile

# -----------------------------------------------------------------------------
# Stage 2: Builder
# -----------------------------------------------------------------------------
FROM node:22-slim AS builder

ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN corepack enable && corepack prepare pnpm@10.33.2 --activate

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/packages ./packages
COPY . .

# Build arguments for environment injection at build time
ARG NEXT_PUBLIC_BASE_URL
ARG NEXT_PUBLIC_CONVEX_URL
ARG NEXT_PUBLIC_WORKOS_REDIRECT_URI
ARG NEXT_PUBLIC_POSTHOG_KEY
ARG NEXT_PUBLIC_POSTHOG_HOST
ARG NEXT_PUBLIC_FF_CROSS_TAB_TOKEN_SHARING

ENV NEXT_TELEMETRY_DISABLED=1

# Build the Next.js application
RUN pnpm build

# -----------------------------------------------------------------------------
# Stage 3: Production Runner
# -----------------------------------------------------------------------------
FROM node:22-slim AS runner

LABEL org.opencontainers.image.title="HackWithAI v2"
LABEL org.opencontainers.image.description="AI-Powered Penetration Testing Assistant"
LABEL org.opencontainers.image.vendor="HackWithAI"
LABEL org.opencontainers.image.source="https://github.com/HackWithAI"

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

WORKDIR /app

# Create non-root user for security
RUN groupadd --gid 1001 hwai && \
    useradd --uid 1001 --gid hwai --shell /bin/bash --create-home hwai

# Copy standalone output and static files
COPY --from=builder --chown=hwai:hwai /app/.next/standalone ./
COPY --from=builder --chown=hwai:hwai /app/.next/static ./.next/static
COPY --from=builder --chown=hwai:hwai /app/public ./public

USER hwai

EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health', (r) => r.statusCode === 200 ? process.exit(0) : process.exit(1))"

CMD ["node", "server.js"]
