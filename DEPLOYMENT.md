# HackWithAI v2 - Deployment Guide

## Overview

Production deployment strategies for Ubuntu VPS, Kali Linux servers, Docker, and cloud platforms.

## Deployment Methods

### 1. Docker Compose (Recommended)

```bash
cd hwai-v2
cp .env.local.example .env.local
# Edit .env.local with production credentials

docker compose up -d --build
```

Services deployed:

- `hwai-app` - Next.js app (port 3000)
- `hwai-centrifugo` - WebSocket relay (port 8000)
- `hwai-ollama` - Local AI (optional, port 11434)
- `hwai-redis` - Cache (optional, port 6379)

### 2. Standalone Docker Image

```bash
docker build -t hwai/pentester:latest .
docker run -d --name hwai-app --env-file .env.local -p 3000:3000 hwai/pentester:latest
```

### 3. VPS with PM2

```bash
npm install -g pm2
pnpm install
pnpm build

cat > ecosystem.config.js << 'INNEREOF'
module.exports = {
  apps: [{
    name: 'hwai-v2',
    script: './node_modules/next/dist/bin/next',
    args: 'start',
    instances: 1,
    autorestart: true,
    max_memory_restart: '2G',
    env: { NODE_ENV: 'production', PORT: 3000 }
  }]
};
INNEREOF

pm2 start ecosystem.config.js
pm2 save
pm2 startup systemd
```

## Environment Variables

Required: `WORKOS_API_KEY`, `WORKOS_CLIENT_ID`, `WORKOS_COOKIE_PASSWORD`, `CONVEX_DEPLOYMENT`, `NEXT_PUBLIC_CONVEX_URL`, `CONVEX_SERVICE_ROLE_KEY`, `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `E2B_API_KEY`, `TRIGGER_PROJECT_ID`, `TRIGGER_SECRET_KEY`, `NEXT_PUBLIC_BASE_URL`

## Security Hardening

- Secrets in Docker secrets or vault
- HTTPS only (TLS 1.2+)
- Firewall: UFW allow 22, 80, 443
- Docker non-root user
- Regular key rotation

## Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name localhost:3006;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name localhost:3006;

    ssl_certificate /etc/letsencrypt/live/localhost:3006/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/localhost:3006/privkey.pem;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

## Monitoring

```bash
# Health check
curl https://localhost:3006/api/health

# Docker stats
docker stats hwai-app
```

## Backup

```bash
# Convex export
npx convex export --path ./backups/convex-$(date +%Y%m%d)

# Env backup
cp .env.local /secure/backup/hwai-env-$(date +%Y%m%d).backup
```

## Update Procedure

```bash
cd hwai-v2
git pull origin main
docker compose build --no-cache
docker compose up -d
```

## Security Checklist

- [ ] Secrets in env vars only
- [ ] HTTPS enforced
- [ ] Firewall configured
- [ ] Docker non-root user
- [ ] Automatic security updates
- [ ] Fail2ban for SSH
- [ ] WorkOS MFA enforced
- [ ] E2B token rotated
- [ ] Logs centralized
