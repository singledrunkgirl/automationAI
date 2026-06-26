import { NextRequest, NextResponse } from "next/server";
import {
  getStoredChats,
  upsertStoredChat,
  deleteStoredChat,
  migrateFromLocalStorage,
} from "@/lib/chat-db";

// GET /api/chats — list all chats
export async function GET() {
  const chats = getStoredChats();
  return NextResponse.json({ chats });
}

// POST /api/chats — upsert a chat (and optionally migrate localStorage data)
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Handle migration request
    if (body.action === "migrate") {
      const { chats: localChats, messages } = body;
      if (Array.isArray(localChats) && messages && typeof messages === "object") {
        migrateFromLocalStorage(localChats, messages);
        return NextResponse.json({ success: true, migrated: true });
      }
      return NextResponse.json({ error: "Invalid migration data" }, { status: 400 });
    }

    // Handle regular chat upsert
    if (body.chat) {
      upsertStoredChat(body.chat);
      return NextResponse.json({ success: true });
    }

    return NextResponse.json({ error: "Missing chat data" }, { status: 400 });
  } catch (error) {
    console.error("[chats] POST error:", error);
    return NextResponse.json({ error: "Failed to save chat" }, { status: 500 });
  }
}

// DELETE /api/chats — delete a chat (body: { chatId: "..." })
export async function DELETE(req: NextRequest) {
  try {
    const body = await req.json();
    if (body.chatId && typeof body.chatId === "string") {
      deleteStoredChat(body.chatId);
      return NextResponse.json({ success: true });
    }
    return NextResponse.json({ error: "Missing chatId" }, { status: 400 });
  } catch (error) {
    console.error("[chats] DELETE error:", error);
    return NextResponse.json({ error: "Failed to delete chat" }, { status: 500 });
  }
}
