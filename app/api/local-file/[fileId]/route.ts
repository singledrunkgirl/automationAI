import { NextRequest, NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ fileId: string }> },
) {
  const { fileId } = await params;

  // Look up file metadata from the uploads directory
  const uploadsDir = path.join(process.cwd(), "data", "uploads");

  if (!fs.existsSync(uploadsDir)) {
    return new NextResponse("Uploads directory not found", { status: 404 });
  }

  // Find file matching this fileId prefix
  const files = fs.readdirSync(uploadsDir);
  const match = files.find((f) => f.startsWith(fileId));

  if (!match) {
    return new NextResponse("File not found", { status: 404 });
  }

  const filePath = path.join(uploadsDir, match);

  if (!fs.existsSync(filePath)) {
    return new NextResponse("File not found", { status: 404 });
  }

  const stat = fs.statSync(filePath);
  const ext = path.extname(match).toLowerCase();

  const mimeTypes: Record<string, string> = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".md": "text/markdown",
    ".csv": "text/csv",
    ".json": "application/json",
    ".zip": "application/zip",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  };

  const contentType = mimeTypes[ext] || "application/octet-stream";

  return new NextResponse(fs.readFileSync(filePath), {
    status: 200,
    headers: {
      "Content-Type": contentType,
      "Content-Length": String(stat.size),
      "Cache-Control": "public, max-age=31536000, immutable",
    },
  });
}
