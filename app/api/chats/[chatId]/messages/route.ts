import { NextRequest, NextResponse } from "next/server";
import {
  getStoredMessages,
  setStoredMessages,
  appendStoredMessage,
} from "@/lib/chat-db";

// GET /api/chats/[chatId]/messages
export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ chatId: string }> },
) {
  const { chatId } = await params;
  const messages = getStoredMessages(chatId);
  return NextResponse.json({ messages });
}

// POST /api/chats/[chatId]/messages — append or set messages
export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ chatId: string }> },
) {
  const { chatId } = await params;
  try {
    const body = await req.json();

    // Set all messages (replace)
    if (body.messages && Array.isArray(body.messages)) {
      setStoredMessages(chatId, body.messages);
      return NextResponse.json({ success: true });
    }

    // Append single message
    if (body.message) {
      appendStoredMessage(chatId, body.message);
      return NextResponse.json({ success: true });
    }

    return NextResponse.json({ error: "Missing messages or message" }, { status: 400 });
  } catch (error) {
    console.error("[messages] POST error:", error);
    return NextResponse.json({ error: "Failed to save messages" }, { status: 500 });
  }
}

// DELETE /api/chats/[chatId]/messages — delete all messages for a chat
export async function DELETE(
  _req: NextRequest,
  { params }: { params: Promise<{ chatId: string }> },
) {
  const { chatId } = await params;
  setStoredMessages(chatId, []);
  return NextResponse.json({ success: true });
}
