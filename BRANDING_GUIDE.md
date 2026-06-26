# HackWithAI v2 - Branding Guide

## Overview

This guide documents the branding changes applied to the upstream open-source codebase to create the HackWithAI v2 platform. All original open-source license and attribution files remain intact per the Apache 2.0 license terms.

---

## Brand Identity

### Company

- **Name**: Private Application
- **Domain**: localhost:3006
- **Industry**: Cybersecurity, AI-Powered Penetration Testing

### Product

- **Name**: HackWithAI v2
- **Tagline**: Your AI-Powered Penetration Testing Assistant
- **Short Name**: HackWithAI

---

## Visual Assets

### Logo Replacement

The current placeholder logo is located at:

- `public/icon-192x192.png`
- `public/icon-256x256.png`
- `public/icon-512x512.png`
- `public/apple-touch-icon.png`
- `public/favicon.ico`

**Replacement Instructions:**

1. Generate logo in the following sizes:
   - 192x192 PNG (icon)
   - 256x256 PNG (icon)
   - 512x512 PNG (PWA icon + OG image)
   - 180x180 PNG (Apple touch icon)
   - Multi-resolution ICO (favicon)

2. Overwrite existing files in `public/`

3. Update OpenGraph and Twitter card images in `app/layout.tsx`:
   ```tsx
   images: [
     {
       url: "https://localhost:3006/icon-512x512.png",
       width: 512,
       height: 512,
       alt: "HackWithAI v2",
     },
   ],
   ```

### SVG Logo Component

The inline SVG logo component is located at:

- `components/icons/hwai-svg.tsx`

**To update:**

1. Replace the SVG paths inside the component with your new logo SVG
2. Keep the component export name: `HackWithAI v2SVG`
3. Maintain the `theme` and `scale` props for dark/light mode support

---

## Color Palette

### Current Theme

The application uses Tailwind CSS v4 with CSS variables. Colors are defined in `app/globals.css`.

**Recommended HackWithAI Brand Colors:**

| Token        | Hex       | Usage                   |
| ------------ | --------- | ----------------------- |
| Primary      | `#0EA5E9` | Buttons, links, accents |
| Primary Dark | `#0284C7` | Hover states            |
| Secondary    | `#8B5CF6` | Badges, highlights      |
| Background   | `#0A0A0A` | Dark mode background    |
| Surface      | `#171717` | Cards, dialogs          |
| Border       | `#262626` | Dividers, outlines      |
| Success      | `#22C55E` | Success states          |
| Warning      | `#EAB308` | Warnings                |
| Error        | `#EF4444` | Errors                  |

**To apply:**

Edit `app/globals.css` and update CSS custom properties:

```css
:root {
  --primary: 199 89% 48%; /* #0EA5E9 */
  --primary-foreground: 0 0% 100%;
  --secondary: 258 90% 66%; /* #8B5CF6 */
  /* ... */
}
```

---

## Typography

### Current Fonts

- **Sans**: Geist (variable font)
- **Mono**: Geist Mono (variable font)

**To change fonts:**

Edit `app/layout.tsx`:

```tsx
import { Inter, JetBrains_Mono } from "next/font/google";

const sans = Inter({ variable: "--font-sans", subsets: ["latin"] });
const mono = JetBrains_Mono({ variable: "--font-mono", subsets: ["latin"] });
```

---

## Text & Copy

### Application Metadata

**Location**: `app/layout.tsx`

```tsx
const APP_NAME = "HackWithAI v2";
const APP_DEFAULT_TITLE =
  "HackWithAI v2 - AI-Powered Penetration Testing Assistant";
const APP_TITLE_TEMPLATE = "%s | HackWithAI v2";
const APP_DESCRIPTION =
  "HackWithAI v2 is an AI pentesting assistant that helps you scan targets, exploit vulnerabilities, analyze findings, and write reports faster.";
```

### System Prompt Persona

**Location**: `lib/system-prompt.ts`

The AI assistant persona references the product name. Search for:

- `HackWithAI v2` in system prompts
- Update help links to `https://localhost:3006`

### Legal Pages

**Locations**:

- `app/privacy-policy/page.tsx`
- `app/terms-of-service/page.tsx`

Update:

- Company name: "Private Application"
- Contact email
- Domain references
- Data handling descriptions

---

## PWA Manifest

**Location**: `public/manifest.json`

```json
{
  "short_name": "HackWithAI",
  "name": "HackWithAI v2",
  "description": "HackWithAI v2 - AI-Powered Penetration Testing Assistant",
  "theme_color": "#0A0A0A",
  "background_color": "#0A0A0A"
}
```

---

## Package & Internal Names

### npm Package

- **Name**: `hwai-v2`
- **Location**: `package.json`

### Docker Images

- **Sandbox**: `hwai/sandbox:latest`
- **App**: `hwai/pentester:latest`

### Desktop App

- **Identifier**: `local.hwai.desktop`
- **Protocol**: `hwai://`
- **Location**: `packages/desktop/src-tauri/tauri.conf.json`

### Local Sandbox Package

- **Name**: `@hwai/local`
- **Binary**: `hwai-local`
- **Location**: `packages/local/package.json`

---

## Model Tier Names

**Location**: `types/chat.ts`

Tier IDs used in the database and UI:

- `hwai-standard` (entry tier)
- `hwai-pro` (advanced tier)
- `hwai-max` (ultimate tier)

Display names are configured in:

- `lib/ai/providers.ts` (`modelDisplayNames`)
- `app/components/ModelSelector/constants.ts`
- `app/components/PricingDialog.tsx`

---

## Domain & URLs

### Production

- **App**: https://localhost:3006
- **API**: https://localhost:3006/api
- **Support**: https://help.hwaiglobalsolutions.com

### Development

- **App**: http://localhost:3000
- **Convex**: https://your-deployment.convex.cloud

### Deep Links

- Desktop auth callback: `hwai://auth?token=...`

---

## Files Modified for Branding

### Core Branding

| File                   | Changes                                                      |
| ---------------------- | ------------------------------------------------------------ |
| `app/layout.tsx`       | App metadata, title, description, keywords, OG/Twitter cards |
| `public/manifest.json` | PWA name, description, colors                                |
| `lib/system-prompt.ts` | AI persona name, help URLs                                   |
| `types/chat.ts`        | Model tier identifiers                                       |
| `lib/ai/providers.ts`  | Model display names, provider branding                       |

### UI Components

| File                                            | Changes                          |
| ----------------------------------------------- | -------------------------------- |
| `components/icons/hwai-svg.tsx`          | HackWithAI logo SVG component   |
| `app/components/Header.tsx`                     | Header logo and text             |
| `app/components/SidebarHeader.tsx`              | Sidebar branding                 |
| `app/components/Footer.tsx`                     | Footer text and links            |
| `app/components/PricingDialog.tsx`              | Product name in pricing          |
| `app/components/ModelSelector.tsx`              | Model tier display names         |
| `app/components/SettingsDialog.tsx`             | Settings panel branding          |
| `app/components/CustomizeHackWithAIDialog.tsx` | Personalization dialog (renamed) |

### Pages

| File                            | Changes                         |
| ------------------------------- | ------------------------------- |
| `app/privacy-policy/page.tsx`   | Legal entity, domain, contact   |
| `app/terms-of-service/page.tsx` | Legal entity, domain, liability |
| `app/download/page.tsx`         | Download page branding          |
| `app/signup/page.tsx`           | Signup page branding            |
| `app/share/[shareId]/*`         | Shared chat page titles         |

### Docker & Deployment

| File                 | Changes                         |
| -------------------- | ------------------------------- |
| `docker/Dockerfile`  | Image vendor, user names, paths |
| `docker/build.sh`    | Image name                      |
| `docker/run.sh`      | Container name                  |
| `docker-compose.yml` | Service names, container names  |

### Packages

| File                | Changes                                       |
| ------------------- | --------------------------------------------- |
| `packages/desktop/` | App identifier, protocol scheme, binary names |
| `packages/local/`   | Package name, CLI name, keywords              |

### Internal Constants

| File                                 | Changes               |
| ------------------------------------ | --------------------- |
| `lib/utils/client-storage.ts`        | localStorage keys     |
| `lib/utils/scroll-events.ts`         | Custom event names    |
| `lib/utils/pro-max-notice-cookie.ts` | Cookie names          |
| `lib/auth/shared-token.ts`           | Token storage keys    |
| `lib/api/chat-logger.ts`             | Analytics event names |
| `lib/referrals/config.ts`            | Referral cookie names |

---

## Preserved Attribution

The following original attribution remains intact:

- **LICENSE**: Apache 2.0 with commercial restrictions (unchanged)
- **GitHub Source URLs**: Runtime and setup links point to `github.com/local/hwai-v2`
- **Original README**: Clone instructions still reference the upstream repository
- **Docker LABEL**: `org.opencontainers.image.source` points to original repository

---

## Post-Rebranding Checklist

- [ ] Replace `public/icon-*.png` and `favicon.ico` with HackWithAI logo
- [ ] Update `components/icons/hwai-svg.tsx` with new SVG logo
- [ ] Verify all page titles render correctly in browser tabs
- [ ] Test PWA install on mobile (manifest colors, icon)
- [ ] Update social sharing preview (OG image, Twitter card)
- [ ] Configure production domain DNS (localhost:3006)
- [ ] Set up SSL certificate
- [ ] Update WorkOS redirect URI to production domain
- [ ] Update Convex CORS and allowed origins
- [ ] Configure PostHog project name
- [ ] Update Stripe product names (if using payments)
- [ ] Create support/help center at help domain
- [ ] Review all email templates (if any)
- [ ] Test desktop app deep link (`hwai://`)
