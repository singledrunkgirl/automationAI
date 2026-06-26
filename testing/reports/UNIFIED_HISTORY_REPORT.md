# Unified Chat History Report

## Status: ✅ FIXED  
**Date**: 2026-06-21  
**Problem**: Desktop App (Tauri WebView) and Browser (localhost:3006) maintain separate chat histories

---

## Root Cause

localStorage is per-browser-profile / per-WebView-instance. Even though both the Tauri Desktop app and regular browsers load from `http://localhost:3006` (same origin), each WebView instance has its own isolated localStorage. This means:

- Chrome's localStorage for `localhost:3006` ≠ Tauri WebView's localStorage for `localhost:3006`
- Firefox's localStorage for `localhost:3006` ≠ Tauri WebView's localStorage for `localhost:3006`

When `LOCAL_ONLY_MODE=true`, the `MockConvexClient` routed all chat storage to `localStorage` keys (`hwai_local_chats`, `hwai_local_msgs_*`), causing histories to diverge between browser instances.

---

## Solution

Created a **server-side SQLite database** at `data/chat_history.db` as the single source of truth:

```
┌─────────────┐     GET /api/chats      ┌──────────────────┐
│  Browser A  │ ◄──────────────────────► │  Next.js Server   │
│ (Chrome)    │     POST /api/chats      │                  │
└─────────────┘                          │  SQLite Database  │
                                         │  (chat_history   │
┌─────────────┐     GET /api/chats       │   .db)           │
│  Browser B  │ ◄──────────────────────► │                  │
│ (Tauri WV)  │     POST /api/chats      └──────────────────┘
└─────────────┘
```

### Architecture:
- **Primary storage**: SQLite at `data/chat_history.db` (server-side)
- **Read cache**: localStorage (client-side, refreshed from SQLite on page load)
- **Write path**: Optimistic localStorage write → async SQLite write via `/api/chats`
- **Init**: On page load, all chats + messages are fetched from SQLite → localStorage cache

---

## Files Modified

| File | Change | Purpose |
|------|--------|--------|
| `lib/chat-db.ts` | **NEW** | SQLite database module (better-sqlite3) with chat/message CRUD |
| `app/api/chats/route.ts` | **NEW** | REST API: GET (list), POST (upsert/migrate), DELETE |
| `app/api/chats/[chatId]/messages/route.ts` | **NEW** | REST API: GET (list messages), POST (append/set), DELETE |
| `lib/utils/client-storage.ts` | **MODIFIED** | Chat/message functions now use SQLite API with localStorage cache |
| `package.json` | **MODIFIED** | Added `better-sqlite3` + `@types/better-sqlite3` dependencies |

**Zero changes required** to `MockConvexClient`, `chat.tsx`, or any other consumer — the function signatures in `client-storage.ts` remain identical.

---

## Storage Schema

```sql
CREATE TABLE chats (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL DEFAULT 'New Chat',
  update_time INTEGER NOT NULL,
  user_id TEXT,
  pinned_at INTEGER
);

CREATE TABLE messages (
  id TEXT NOT NULL,
  chat_id TEXT NOT NULL,
  role TEXT NOT NULL CHECK(role IN ('system','user','assistant')),
  parts TEXT NOT NULL DEFAULT '[]',
  content TEXT,
  update_time INTEGER NOT NULL,
  model TEXT,
  mode TEXT,
  finish_reason TEXT,
  usage TEXT,
  PRIMARY KEY (id, chat_id),
  FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
);
```

- **Journal mode**: WAL (Write-Ahead Logging) for safe concurrent reads/writes
- **Foreign keys**: ON with CASCADE deletes

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/chats` | List all chats (sorted by update_time DESC) |
| `POST` | `/api/chats` | Upsert chat or migrate localStorage data |
| `DELETE` | `/api/chats` | Delete chat + cascade messages |
| `GET` | `/api/chats/:chatId/messages` | List messages for a chat |
| `POST` | `/api/chats/:chatId/messages` | Append message or set all messages |
| `DELETE` | `/api/chats/:chatId/messages` | Delete all messages for a chat |

---

## Verification Results

### Build
```
✓ Compiled successfully
✓ TypeScript check passed
✓ All new routes registered
```

### CRUD Tests
```
POST /api/chats                         → 200 {"success":true}       ✅
GET  /api/chats                         → 200 {"chats":[...]}       ✅
POST /api/chats/:id/messages            → 200 {"success":true}      ✅
GET  /api/chats/:id/messages            → 200 {"messages":[...]}    ✅
DELETE /api/chats                       → 200 {"success":true}      ✅
```

### Bidirectional Sync (simulated two browsers)
| Test | Result |
|------|--------|
| Browser A creates chat + messages → Browser B reads them | ✅ Pass |
| Browser B creates its own chat → Both see all chats | ✅ Pass |
| Browser A deletes chat → Browser B sees deletion | ✅ Pass |
| Data survives server restart | ✅ Pass (reconnected to same DB) |

### Chat Streaming
```
POST /api/chat → SSE streaming with text-delta events ✅
```

### Database
```
SQLite file: data/chat_history.db
WAL mode: enabled
Foreign keys: ON (CASCADE deletes)
```

---

## Data Flow

1. **Page Load**: `initializeStorage()` → GET `/api/chats` + GET `/api/chats/:id/messages` for all chats → populate localStorage cache
2. **Create Chat**: `upsertStoredChat()` → optimistic localStorage update + POST `/api/chats`
3. **Append Message**: `appendStoredMessage()` → optimistic localStorage update + POST `/api/chats/:id/messages`
4. **Read Chats**: `getStoredChats()` → sync localStorage cache (populated from SQLite on load)
5. **Read Messages**: `getStoredMessages()` → sync localStorage cache
6. **Delete Chat**: `deleteStoredChat()` → optimistic localStorage removal + DELETE `/api/chats`

## Summary

| Check | Result |
|-------|--------|
| Single SQLite database | ✅ |
| Shared by all browser instances | ✅ |
| Data persists across restarts | ✅ |
| Bidirectional sync | ✅ |
| Chat streaming continues to work | ✅ |
| Existing localStorage data migrated | ✅ |
| Zero changes to UI components | ✅ |
| Delete cascades properly | ✅ |
