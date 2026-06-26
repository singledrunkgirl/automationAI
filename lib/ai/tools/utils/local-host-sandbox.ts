import { spawn } from "node:child_process";
import { promises as fs } from "node:fs";
import os from "node:os";
import path from "node:path";

interface CommandOptions {
  envVars?: Record<string, string>;
  envs?: Record<string, string>;
  cwd?: string;
  timeoutMs?: number;
  background?: boolean;
  onStdout?: (data: string) => void;
  onStderr?: (data: string) => void;
  signal?: AbortSignal;
}

export class LocalHostSandbox {
  readonly sandboxKind = "centrifugo" as const;

  private readonly connectionId = "local-host";
  private readonly connectionName = "Local Kali";

  commands = {
    run: async (command: string, opts: CommandOptions = {}) => {
      return this.runCommand(command, opts);
    },
  };

  files = {
    write: async (
      filePath: string,
      content: string | Buffer | ArrayBuffer | Uint8Array,
      ..._args: unknown[]
    ) => {
      await fs.mkdir(path.dirname(filePath), { recursive: true });
      await fs.writeFile(filePath, toWritableContent(content));
    },
    read: async (filePath: string, ..._args: unknown[]) =>
      fs.readFile(filePath, "utf8"),
    remove: async (filePath: string, ..._args: unknown[]) => {
      await fs.rm(filePath, { recursive: true, force: true });
    },
    list: async (dirPath: string, ..._args: unknown[]) => {
      const entries = await fs.readdir(dirPath, { withFileTypes: true });
      return entries.map((entry) => ({ name: entry.name }));
    },
    uploadToUrl: async (
      filePath: string,
      uploadUrl: string,
      mediaType?: string,
    ) => {
      const content = await fs.readFile(filePath);
      const response = await fetch(uploadUrl, {
        method: "PUT",
        headers: mediaType ? { "Content-Type": mediaType } : undefined,
        body: content,
      });
      if (!response.ok) {
        throw new Error(`Upload failed with HTTP ${response.status}`);
      }
    },
  };

  isWindows(): boolean {
    return process.platform === "win32";
  }

  getConnectionId(): string {
    return this.connectionId;
  }

  getConnectionName(): string {
    return this.connectionName;
  }

  getHost(port: number): string {
    return `127.0.0.1:${port}`;
  }

  getOsContext(): string {
    return `<sandbox_environment>
IMPORTANT: You are running in LOCAL ONLY MODE. Commands execute directly on this Kali host without E2B, WorkOS login, Docker isolation, or a remote relay.

System Environment:
- OS: ${os.type()} ${os.release()} (${os.arch()})
- Hostname: ${os.hostname()}
- Working directory: ${process.cwd()}
- Upload path: /tmp/hwai-upload
</sandbox_environment>`;
  }

  async close(): Promise<void> {
    return;
  }

  private runCommand(command: string, opts: CommandOptions) {
    const env = {
      ...process.env,
      ...(opts.envVars ?? {}),
      ...(opts.envs ?? {}),
    };
    const cwd = opts.cwd || process.env.LOCAL_ONLY_WORKDIR || os.homedir();

    if (opts.background) {
      const child = spawn("bash", ["-lc", command], {
        cwd,
        env,
        detached: true,
        stdio: "ignore",
      });
      child.unref();
      return Promise.resolve({
        stdout: "",
        stderr: "",
        exitCode: 0,
        pid: child.pid,
      });
    }

    return new Promise<{
      stdout: string;
      stderr: string;
      exitCode: number;
    }>((resolve, reject) => {
      const child = spawn("bash", ["-lc", command], {
        cwd,
        env,
        stdio: ["ignore", "pipe", "pipe"],
      });

      let stdout = "";
      let stderr = "";
      let finished = false;
      let timeout: NodeJS.Timeout | undefined;

      const finish = (result: {
        stdout: string;
        stderr: string;
        exitCode: number;
      }) => {
        if (finished) return;
        finished = true;
        if (timeout) clearTimeout(timeout);
        opts.signal?.removeEventListener("abort", onAbort);
        resolve(result);
      };

      const onAbort = () => {
        child.kill("SIGTERM");
        setTimeout(() => child.kill("SIGKILL"), 1500).unref();
      };

      if (opts.signal) {
        if (opts.signal.aborted) onAbort();
        opts.signal.addEventListener("abort", onAbort);
      }

      if (opts.timeoutMs && opts.timeoutMs > 0) {
        timeout = setTimeout(() => {
          child.kill("SIGTERM");
          setTimeout(() => child.kill("SIGKILL"), 1500).unref();
        }, opts.timeoutMs);
      }

      child.stdout.on("data", (chunk: Buffer) => {
        const text = chunk.toString();
        stdout += text;
        opts.onStdout?.(text);
      });

      child.stderr.on("data", (chunk: Buffer) => {
        const text = chunk.toString();
        stderr += text;
        opts.onStderr?.(text);
      });

      child.on("error", (error) => {
        if (finished) return;
        finished = true;
        if (timeout) clearTimeout(timeout);
        opts.signal?.removeEventListener("abort", onAbort);
        reject(error);
      });

      child.on("close", (code, signal) => {
        finish({
          stdout,
          stderr: signal ? `${stderr}\nsignal: ${signal}`.trim() : stderr,
          exitCode: code ?? (signal ? 1 : 0),
        });
      });
    });
  }
}

function toWritableContent(
  content: string | Buffer | ArrayBuffer | Uint8Array,
): string | Buffer | Uint8Array {
  if (content instanceof ArrayBuffer) {
    return Buffer.from(content);
  }
  return content;
}
