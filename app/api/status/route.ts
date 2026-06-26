import { NextResponse } from "next/server";
import { execSync } from "child_process";
import fs from "fs";
import path from "path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function toolStatus() {
  const tools = [
    "nmap", "masscan", "nc", "tcpdump", "bettercap", "responder", "dnsrecon",
    "msfconsole", "searchsploit", "sqlmap", "hydra", "john", "hashcat",
    "gobuster", "ffuf", "wpscan", "nikto", "wafw00f", "whatweb",
    "aircrack-ng", "reaver", "wifite", "kismet",
    "checksec", "radare2", "gdb", "upx",
    "theHarvester", "sherlock", "holehe", "h8mail", "dmitry",
    "tor", "torsocks", "proxychains4",
    "openssl", "gpg", "hashid", "netcat", "socat", "chisel",
    "evil-winrm", "smbclient", "enum4linux",
  ];
  const installed: string[] = [];
  for (const t of tools) {
    try {
      execSync(`which ${t}`, { stdio: "ignore", timeout: 2000 });
      installed.push(t);
    } catch {}
  }

  // Count data files
  const dataDir = "/home/kali/HackWithAI/data";
  let scrapeCount = 0, reportCount = 0, payloadCount = 0;
  try { scrapeCount = fs.readdirSync(path.join(dataDir, "darkweb")).length; } catch {}
  try { reportCount = fs.readdirSync(path.join(dataDir, "reports")).length; } catch {}
  try { payloadCount = fs.readdirSync(path.join(dataDir, "c2/payloads")).length; } catch {}

  return {
    tools_total: installed.length,
    tools_installed: installed.slice(0, 20),
    darkweb_scrapes: scrapeCount,
    reports: reportCount,
    payloads: payloadCount,
    knowledge_db: fs.existsSync("/home/kali/HackWithAI/data/knowledge/knowledge_graph.db"),
    cve_db: fs.existsSync("/home/kali/HackWithAI/data/zeroday/cve.db"),
    listeners: 0,
    agents_online: 5,
    uptime: process.uptime(),
  };
}

export async function GET() {
  return NextResponse.json({
    status: "operational",
    timestamp: new Date().toISOString(),
    ...toolStatus(),
  });
}
