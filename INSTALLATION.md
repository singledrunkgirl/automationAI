# HackWithAI v2 - Installation Guide

## Overview

This guide covers installing HackWithAI v2 on **Kali Linux**, **Ubuntu VPS**, and **local development machines**. HackWithAI v2 is built from the approved upstream architecture and requires several external services for full functionality.

---

## Prerequisites

### Required Accounts & Services

| Service         | Purpose                                 | Signup URL                  |
| --------------- | --------------------------------------- | --------------------------- |
| **WorkOS**      | Authentication & user management        | https://workos.com          |
| **Convex**      | Database, backend, and real-time sync   | https://www.convex.dev      |
| **E2B**         | Secure sandbox for agent code execution | https://e2b.dev             |
| **Trigger.dev** | Durable runtime for long-running agents | https://trigger.dev         |
| **OpenRouter**  | Default AI model provider (cloud)       | https://openrouter.ai       |
| **OpenAI**      | Content moderation & direct API         | https://platform.openai.com |

### Optional Services

| Service             | Purpose                              | Signup URL                |
| ------------------- | ------------------------------------ | ------------------------- |
| **Amazon S3**       | File storage (alternative to Convex) | https://aws.amazon.com/s3 |
| **Perplexity**      | Web search functionality             | https://perplexity.ai     |
| **Jina AI**         | URL content extraction               | https://jina.ai/reader    |
| **Redis / Upstash** | Stream resumption & rate limiting    | https://upstash.com       |
| **PostHog**         | Analytics & observability            | https://posthog.com       |
| **Stripe**          | Payment processing                   | https://stripe.com        |

### System Requirements

- **OS**: Ubuntu 22.04+ or Kali Linux 2024+
- **Node.js**: 22.x LTS
- **pnpm**: 10.33.2+ (via corepack)
- **Docker**: 24.0+ (for containerized deployment)
- **Docker Compose**: v2+ (for stack deployment)
- **RAM**: 4GB minimum (8GB recommended for production)
- **CPU**: 2 cores minimum (4+ recommended)
- **Disk**: 20GB free space

---

## Local Development Installation

### 1. Clone the Repository

```bash
git clone https://github.com/local/hwai-v2.git HackWithAI-v2-v1
cd HackWithAI-v2-v1
```

### 2. Install Node.js 22

```bash
# Using NodeSource (Ubuntu/Kali)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node -v  # v22.x.x
npm -v
```

### 3. Enable pnpm

```bash
corepack enable
corepack prepare pnpm@10.33.2 --activate
pnpm -v
```

### 4. Install Dependencies

```bash
pnpm install
```

### 5. Configure Environment Variables

```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your service credentials:

```env
# Required
WORKOS_API_KEY=sk_example_123456789
WORKOS_CLIENT_ID=client_123456789
WORKOS_COOKIE_PASSWORD=<generate-32-char-secret>
CONVEX_DEPLOYMENT=dev:your-deployment
NEXT_PUBLIC_CONVEX_URL=https://your-deployment.convex.cloud
CONVEX_SERVICE_ROLE_KEY=<32-char-secret>
OPENROUTER_API_KEY=sk-or-...
OPENAI_API_KEY=sk-...
E2B_API_KEY=e2b_...
TRIGGER_PROJECT_ID=proj_...
TRIGGER_SECRET_KEY=tr_dev_...

# AI Provider Mode
PROVIDER_MODE=openrouter

# Optional local Ollama
OLLAMA_ENABLED=false
OLLAMA_BASE_URL=http://localhost:11434/api
```

Generate secrets:

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

### 6. Run Setup Script

```bash
pnpm run setup
```

### 7. Start Development Servers

```bash
# Run Next.js + Convex dev simultaneously
pnpm run dev

# Or run separately:
pnpm run dev:next   # Terminal 1
pnpm run dev:convex # Terminal 2
```

The application will be available at **http://localhost:3000**.

### 8. Start Trigger.dev Worker (for Agent Mode)

```bash
npx trigger.dev@latest dev
```

---

## Kali Linux Specific Setup

Kali Linux ships with many penetration testing tools pre-installed. HackWithAI v2 integrates with these tools via its agent sandbox.

### Install Additional Dependencies

```bash
sudo apt-get update
sudo apt-get install -y \
  git \
  curl \
  wget \
  build-essential \
  python3 \
  python3-pip \
  python3-venv \
  nodejs \
  npm \
  docker.io \
  docker-compose

# Enable Docker
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
```

### Ollama Local AI (Optional)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended models for pentesting
ollama pull qwen2.5-coder
ollama pull deepseek-coder:6.7b
ollama pull mistral
ollama pull llama3.1

# Start Ollama service
ollama serve
```

Set in `.env.local`:

```env
PROVIDER_MODE=ollama
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434/api
```

### Local Sandbox Mode (No E2B)

For fully offline operation on Kali:

```bash
# Build the local sandbox Docker image
pnpm run docker:build

# Run local sandbox bridge
pnpm run local-sandbox --token YOUR_TOKEN
```

---

## Ubuntu VPS Production Installation

### 1. Server Preparation

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Install Node.js (for local builds if needed)
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. Clone & Build

```bash
git clone https://github.com/local/hwai-v2.git HackWithAI-v2-v1
cd HackWithAI-v2-v1
corepack enable
corepack prepare pnpm@10.33.2 --activate
pnpm install
```

### 3. Configure Environment

```bash
cp .env.local.example .env.local
# Edit .env.local with production credentials
nano .env.local
```

### 4. Docker Deployment

```bash
# Build and start services
docker compose up -d --build

# View logs
docker compose logs -f app

# Scale or restart
docker compose restart app
```

### 5. Reverse Proxy (Nginx)

```bash
sudo apt-get install -y nginx
sudo nano /etc/nginx/sites-available/hwai
```

```nginx
server {
    listen 80;
    server_name localhost:3006;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/hwai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Enable HTTPS with Certbot
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d localhost:3006
```

---

## AI Provider Configuration

### Cloud Mode (Default)

Uses OpenRouter as the unified provider. Supports OpenAI, Gemini, Claude, DeepSeek, and more.

```env
PROVIDER_MODE=openrouter
OPENROUTER_API_KEY=your-key
```

### Direct Cloud Providers

Switch to direct API providers:

```env
# OpenAI Direct
PROVIDER_MODE=openai
OPENAI_API_KEY=sk-...

# Google Gemini Direct
PROVIDER_MODE=google
GOOGLE_API_KEY=...

# Anthropic Claude Direct
PROVIDER_MODE=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### Local Mode (Ollama)

For air-gapped or privacy-sensitive environments:

```env
PROVIDER_MODE=ollama
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434/api
```

Recommended Ollama models:

- `qwen2.5-coder` - Coding and scripting tasks
- `deepseek-coder:6.7b` - Exploit development
- `mistral` - Fast reasoning
- `llama3.1` - General purpose

---

## Troubleshooting

### Build Errors

```bash
# Clear cache
pnpm store prune
rm -rf .next node_modules
pnpm install
pnpm build
```

### Convex Connection Issues

```bash
# Ensure convex dev is running
npx convex dev

# Check deployment
npx convex status
```

### Docker Permission Denied

```bash
sudo usermod -aG docker $USER
# Log out and back in
```

### Ollama Connection Refused

```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# Check service status
systemctl --user status ollama
```

---

## Next Steps

After installation:

1. Configure **WorkOS** authentication providers (Google, GitHub, SAML)
2. Set up **Trigger.dev** environment variables for agent tasks
3. Customize branding in `app/layout.tsx` and `public/`
4. Review `DEPLOYMENT.md` for production hardening
5. Review `SYSTEM_ARCHITECTURE.md` for component understanding
