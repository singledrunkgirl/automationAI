import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import { randomBytes } from "crypto";

function generateFileId(): string {
  return `local-${Date.now()}-${randomBytes(4).toString("hex")}`;
}

function estimateTokens(bytes: number): number {
  return Math.ceil(bytes / 4);
}

const UPLOADS_DIR = path.join(process.cwd(), "data", "uploads");
const META_DIR = path.join(UPLOADS_DIR, ".meta");

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const { name, mediaType, size, content } = body as {
      name: string;
      mediaType: string;
      size: number;
      content: string; // base64 encoded
    };

    if (!name || !content) {
      return NextResponse.json(
        { error: "Missing name or content" },
        { status: 400 },
      );
    }

    const fileId = generateFileId();
    const ext = name.includes(".") ? name.split(".").pop() || "bin" : "bin";
    const safeName = `${fileId}.${ext}`;

    fs.mkdirSync(UPLOADS_DIR, { recursive: true });
    fs.mkdirSync(META_DIR, { recursive: true });

    const filePath = path.join(UPLOADS_DIR, safeName);
    const buffer = Buffer.from(content, "base64");
    fs.writeFileSync(filePath, buffer);

    const tokens = estimateTokens(size || buffer.length);
    const url = `/api/local-file/${fileId}`;

    // Write metadata
    fs.writeFileSync(
      path.join(META_DIR, `${fileId}.json`),
      JSON.stringify({
        fileId,
        name,
        mediaType,
        size: buffer.length,
        tokens,
        localPath: `data/uploads/${safeName}`,
        uploadedAt: Date.now(),
      }),
    );

    return NextResponse.json({
      fileId,
      url,
      name,
      mediaType,
      size: buffer.length,
      tokens,
    });
  } catch (error) {
    console.error("[local-file-upload] Error:", error);
    return NextResponse.json(
      { error: "Failed to save file" },
      { status: 500 },
    );
  }
}

export async function DELETE(req: NextRequest) {
  try {
    const body = await req.json();
    const { fileId } = body as { fileId: string };

    if (!fileId) {
      return NextResponse.json({ error: "Missing fileId" }, { status: 400 });
    }

    // Remove file from uploads dir
    if (fs.existsSync(UPLOADS_DIR)) {
      const files = fs.readdirSync(UPLOADS_DIR);
      const match = files.find((f) => f.startsWith(fileId));
      if (match) {
        fs.unlinkSync(path.join(UPLOADS_DIR, match));
      }
    }

    // Remove metadata
    const metaPath = path.join(META_DIR, `${fileId}.json`);
    if (fs.existsSync(metaPath)) {
      fs.unlinkSync(metaPath);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("[local-file-upload] Delete error:", error);
    return NextResponse.json({ error: "Failed to delete" }, { status: 500 });
  }
}
