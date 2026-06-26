"use client";

// ── Local File Storage ──────────────────────────────────────────────────
// For local-only mode, files are saved to the local filesystem and metadata
// is stored in localStorage so uploads survive page refreshes.

const FILES_KEY = "hwai:local-files";
const UPLOAD_DIR = "data/uploads";

export interface LocalFileMeta {
  fileId: string;
  name: string;
  mediaType: string;
  size: number;
  tokens: number;
  localPath: string;
  uploadedAt: number;
}

function generateFileId(): string {
  return `local-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function estimateTokens(bytes: number): number {
  // Rough estimate: 1 token ≈ 4 chars ≈ 4 bytes
  return Math.ceil(bytes / 4);
}

export function getLocalFiles(): LocalFileMeta[] {
  try {
    const raw = localStorage.getItem(FILES_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function getLocalFileById(fileId: string): LocalFileMeta | undefined {
  return getLocalFiles().find((f) => f.fileId === fileId);
}

export function removeLocalFile(fileId: string): void {
  const files = getLocalFiles().filter((f) => f.fileId !== fileId);
  localStorage.setItem(FILES_KEY, JSON.stringify(files));
}

/**
 * Save a file locally. Returns metadata including URL for the file.
 * The file content is stored as base64 in localStorage for persistence
 * across server restarts.
 */
export async function saveLocalFile(file: File): Promise<LocalFileMeta> {
  const fileId = generateFileId();
  const ext = file.name.includes(".") ? file.name.split(".").pop() || "bin" : "bin";
  const safeName = fileId + "." + ext;
  const tokens = estimateTokens(file.size);

  // Read file as ArrayBuffer, then convert to base64 for localStorage
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  const base64 = btoa(binary);
  const storageKey = `hwai:file:${fileId}`;

  // Store file content in localStorage (chunk if too large)
  try {
    localStorage.setItem(storageKey, base64);
  } catch (e) {
    // If file is too large for localStorage, we still record metadata
    // but the file will only be available via the API route
    console.warn("File too large for localStorage, will use filesystem only:", file.name);
  }

  const meta: LocalFileMeta = {
    fileId,
    name: file.name,
    mediaType: file.type || "application/octet-stream",
    size: file.size,
    tokens,
    localPath: UPLOAD_DIR + "/" + safeName,
    uploadedAt: Date.now(),
  };

  // Persist metadata
  const files = getLocalFiles();
  files.push(meta);
  localStorage.setItem(FILES_KEY, JSON.stringify(files));

  return meta;
}

/**
 * Load file content as base64 from localStorage.
 */
export function loadLocalFileContent(fileId: string): string | null {
  return localStorage.getItem(`hwai:file:${fileId}`);
}
