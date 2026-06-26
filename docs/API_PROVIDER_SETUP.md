# HackWithAI v2 API Provider Setup

HackWithAI v2 V1 keeps the existing provider architecture intact and uses environment-driven routing. Do not enable additional providers unless the deployment owner has supplied the matching API key and intentionally changed `PROVIDER_MODE`.

## Production Defaults

- Primary agent model: Anthropic Claude Sonnet
- Secondary agent model: OpenAI GPT-4.5
- Research and analysis model: Google Gemini
- Default provider mode: `openrouter`

## Required API Key Placeholders

Add these values to `.env.local` for local development and to the production hosting environment for deployment:

```bash
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
OPENROUTER_API_KEY=
```

`GOOGLE_GENERATIVE_AI_API_KEY` is still supported as a backward-compatible alias, but new deployments should use `GOOGLE_API_KEY`.

## Provider Modes

`PROVIDER_MODE=openrouter` is the default and recommended cloud routing mode.

Supported direct modes:

- `openrouter`
- `openai`
- `google`
- `anthropic`
- `ollama`

Prepared provider placeholders, not active by default:

- OpenAI
- OpenRouter
- Gemini
- Anthropic
- Ollama
- Qwen
- DeepSeek
- Mistral
- Llama

## WorkOS Configuration

Set these in the deployment environment before using authentication flows:

```bash
WORKOS_API_KEY=
WORKOS_CLIENT_ID=
WORKOS_COOKIE_PASSWORD=
WORKOS_WEBHOOK_SECRET=
NEXT_PUBLIC_WORKOS_REDIRECT_URI=https://localhost:3006/callback
NEXT_PUBLIC_BASE_URL=https://localhost:3006
```

The WorkOS SDK is initialized lazily at request time so builds can complete without live secrets, but authenticated routes still require valid WorkOS credentials at runtime.

## Owner-Supplied Secrets Still Required

- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GOOGLE_API_KEY`
- `OPENROUTER_API_KEY`
- WorkOS credentials listed above
- Convex deployment URL and service role key
- E2B key for agent sandbox execution
- Trigger.dev keys for agent-long tasks
- Optional Stripe, Redis, S3, PostHog, Perplexity, and Jina keys if those features are enabled
