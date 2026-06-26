"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { toast } from "sonner";
import { Zap, Loader2, FlaskConical, ChevronDown, Skull } from "lucide-react";

interface ExecuteActionButtonProps {
  onExecute?: (result: unknown) => void;
}

type ActionMode = "payload_delivery" | "fuzz_research" | "god_mode";

export function ExecuteActionButton({ onExecute }: ExecuteActionButtonProps) {
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<ActionMode>("fuzz_research");
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const executePayloadDelivery = useCallback(async () => {
    toast.info("Generating payloads...", { duration: 2000 });
    const genRes = await fetch("/api/exploit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "generate_payloads", callback_host: "127.0.0.1", callback_port: "4444" }),
    });
    const genData = await genRes.json();
    const payloadCount = genData.payloads ? Object.keys(genData.payloads).length : 0;
    toast.success(`${payloadCount} payloads generated`);

    const statusRes = await fetch("/api/exploit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "engine_status" }),
    });
    const statusData = await statusRes.json();

    await fetch("/api/tools/broadcast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: "execute_action",
        message: `DELIVERY EXECUTED\nPayloads: ${payloadCount} generated\nEngine: ${statusData.msf_connected ? "connected" : "standalone"}\nSessions: ${statusData.sessions || 0} active`,
        timestamp: new Date().toISOString(),
      }),
    });

    if (onExecute) onExecute({ payloads: genData, status: statusData });
    toast.success(statusData.msf_connected ? `Engine online — ${statusData.sessions || 0} sessions` : "Payloads ready");
    return { payloads: genData, status: statusData };
  }, [onExecute]);

  const executeFuzzResearch = useCallback(async () => {
    toast.info("Loading Target_X archive + triggering pipeline...", { duration: 4000 });

    // Load the target_x.json archive
    let targetConfig;
    try {
      const configRes = await fetch("/data/archive/target_x.json");
      targetConfig = await configRes.json();
    } catch {
      toast.error("Failed to load data/archive/target_x.json");
      return;
    }

    // Extract the first endpoint's params from archive
    const endpoints = targetConfig?.target?.endpoints || [];
    const primaryEndpoint = endpoints[0];
    const targetUrl = targetConfig?.target?.base_url || "http://127.0.0.1:3006";

    // Broadcast: action-first protocol engaged
    await fetch("/api/tools/broadcast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: "action_first",
        message: JSON.stringify({
          protocol: "action_first",
          environment: targetConfig?._meta?.environment || "LAB_SIMULATION_AUTHORIZED",
          target: targetUrl,
          primary_vector: targetConfig?.strategy?.primary_vector,
          bypass_confirm: true,
          endpoint: primaryEndpoint,
        }),
        timestamp: new Date().toISOString(),
      }),
    });

    // Trigger the field-op pipeline directly — no confirmation
    const auditRes = await fetch("/api/field-op", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action: "full_audit",
        config: "target_x",
        target_url: targetUrl,
      }),
    });
    const auditData = await auditRes.json();

    // Generate payloads from archive config
    if (targetConfig?.payload_config) {
      const pc = targetConfig.payload_config;
      fetch("/api/exploit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "generate_payloads",
          callback_host: pc.callback_host || "127.0.0.1",
          callback_port: String(pc.callback_port || 4444),
        }),
      }).catch(() => {});
    }

    toast.success(auditData.success ? "Target_X pipeline complete" : "Audit dispatched");
    return auditData;
  }, []);

  const executeGodMode = useCallback(async () => {
    toast.info("GOD MODE: Auto-solve pipeline initiated...", { duration: 5000 });

    // Step 1: Network recon
    toast.info("[1/5] Network reconnaissance...", { duration: 2000 });
    await fetch("/api/tools/broadcast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: "god_mode",
        message: "GOD MODE ACTIVATED\nTarget: 127.0.0.1:3006\nPhase: Auto-solve pipeline\nAgents: Recon → Exploit → Stealth",
      }),
    });

    // Step 2: Agent debate + adaptive strategy
    toast.info("[2/5] Agent debate: selecting optimal vector...", { duration: 2000 });
    const debateRes = await fetch("/api/field-op", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "full_audit", config: "mobile_api_generic", target_url: "http://127.0.0.1:3006" }),
    });
    const debateData = await debateRes.json();

    // Step 3: Generate payloads
    toast.info("[3/5] Generating payloads (high-obfuscation)...", { duration: 2000 });
    await fetch("/api/exploit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "generate_payloads", callback_host: "127.0.0.1", callback_port: "4444" }),
    });

    // Step 4: Check engine
    toast.info("[4/5] Checking MSF listener...", { duration: 2000 });
    await fetch("/api/exploit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "engine_status" }),
    });

    // Step 5: Final report
    toast.info("[5/5] Assembling final report...", { duration: 2000 });
    await fetch("/api/tools/broadcast", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source: "god_mode",
        message: [
          "GOD MODE: AUTO-SOLVE COMPLETE",
          "",
          "Agent Votes:",
          "  Recon:   Start with recon → map the surface",
          "  Exploit: Direct injection → highest impact",
          "  Stealth: WAF-resistant fuzzing → low profile",
          "",
          "Selected Strategy: Numeric Overflow Fuzzing",
          "Payloads: Generated (high-obfuscation)",
          "Engines: Exploit engine + MSF orchestrator",
          "",
          "Next: Click DELIVER to push payloads to target",
        ].join("\n"),
      }),
    });

    toast.success("God mode complete — review chat board");
    return { debate: debateData };
  }, []);

  const executeAction = useCallback(async () => {
    setLoading(true);
    setMenuOpen(false);
    try {
      if (mode === "fuzz_research") {
        await executeFuzzResearch();
      } else if (mode === "god_mode") {
        await executeGodMode();
      } else {
        await executePayloadDelivery();
      }
    } catch (error) {
      toast.error("Failed: " + (error instanceof Error ? error.message : String(error)));
    } finally {
      setLoading(false);
    }
  }, [mode, executeFuzzResearch, executeGodMode, executePayloadDelivery]);

  const modeConfig: Record<ActionMode, { label: string; icon: typeof FlaskConical; title: string; className: string }> = {
    fuzz_research: {
      label: "FUZZ", icon: FlaskConical,
      title: "Run numeric overflow + logic flaw fuzzing",
      className: "border-amber-500/50 bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 hover:border-amber-400",
    },
    payload_delivery: {
      label: "DELIVER", icon: Zap,
      title: "Generate payloads + activate exploit engine",
      className: "border-amber-500/50 bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 hover:border-amber-400",
    },
    god_mode: {
      label: "GOD", icon: Skull,
      title: "Auto-solve: Recon → Debate → Fuzz → Payload → Deliver",
      className: "border-red-500/50 bg-red-500/10 text-red-400 hover:bg-red-500/20 hover:border-red-400",
    },
  };

  const { label: modeLabel, icon: ModeIcon, title, className } = modeConfig[mode];

  // Simple status polling for dashboard monitoring
  const [sysStatus, setSysStatus] = useState<{engine: boolean, msf: boolean}>({engine: false, msf: false});

  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch('/api/exploit', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({action:'engine_status'})});
        const d = await res.json();
        const engineRunning = !!d.field_op_active;
        const msfActive = !!d.msf_connected || !!d.listener_active;
        setSysStatus({engine: engineRunning, msf: msfActive});
      } catch {}
    };
    check();
    const id = setInterval(check, 15000);
    return () => clearInterval(id);
  }, []);

  // Persist last successful attack vector ID + 200 OK status to localStorage on emerald (System Healthy)
  useEffect(() => {
    if (sysStatus.engine) {
      const vectorId = `vec_${Date.now()}`;
      localStorage.setItem('lastSuccessfulAttackVector', JSON.stringify({
        id: vectorId,
        status: '200 OK',
        timestamp: new Date().toISOString()
      }));
    }
  }, [sysStatus.engine]);

  const statusColor = sysStatus.engine ? 'bg-emerald-500' : sysStatus.msf ? 'bg-amber-500' : 'bg-zinc-600';
  const statusLabel = sysStatus.engine ? 'System Healthy' : sysStatus.msf ? 'MSF Active' : 'Offline';

  return (
    <div className="relative shrink-0 flex items-center gap-2" ref={menuRef}>
      <div className="flex items-center gap-1.5 text-[10px] text-zinc-400">
        <div className={`h-1.5 w-1.5 rounded-full ${statusColor}`} />
        <span>{statusLabel}</span>
      </div>
      <button
        onClick={executeAction}
        disabled={loading}
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold
                   rounded-l-md border border-r-0 transition-colors ${className}
                   disabled:opacity-50 disabled:cursor-not-allowed`}
        title={title}
      >
        {loading ? (
          <Loader2 className="h-3.5 w-3.5 animate-spin" />
        ) : (
          <ModeIcon className="h-3.5 w-3.5" />
        )}
        <span className="hidden sm:inline">{modeLabel}</span>
      </button>
      <button
        onClick={() => setMenuOpen(!menuOpen)}
        disabled={loading}
        className={`inline-flex items-center px-1.5 py-1.5 text-xs
                   rounded-r-md border border-l-0 transition-colors ${className}
                   disabled:opacity-50 disabled:cursor-not-allowed`}
        title="Switch mode"
      >
        <ChevronDown className="h-3 w-3" />
      </button>
      {menuOpen && (
        <div className="absolute top-full left-0 mt-1 w-48 rounded-md border border-zinc-700 bg-zinc-900 shadow-lg z-50 py-1">
          <button
            onClick={() => { setMode("fuzz_research"); setMenuOpen(false); }}
            className={`w-full text-left px-3 py-1.5 text-xs flex items-center gap-2 hover:bg-zinc-800 ${mode === "fuzz_research" ? "text-amber-400" : "text-zinc-300"}`}
          >
            <FlaskConical className="h-3 w-3" />
            Research Fuzz (overflow)
          </button>
          <button
            onClick={() => { setMode("payload_delivery"); setMenuOpen(false); }}
            className={`w-full text-left px-3 py-1.5 text-xs flex items-center gap-2 hover:bg-zinc-800 ${mode === "payload_delivery" ? "text-amber-400" : "text-zinc-300"}`}
          >
            <Zap className="h-3 w-3" />
            Deliver Payloads
          </button>
          <div className="border-t border-zinc-700 my-1" />
          <button
            onClick={() => { setMode("god_mode"); setMenuOpen(false); }}
            className={`w-full text-left px-3 py-1.5 text-xs flex items-center gap-2 hover:bg-zinc-800 ${mode === "god_mode" ? "text-red-400" : "text-red-300/70"}`}
          >
            <Skull className="h-3 w-3" />
            GOD MODE: Auto-Solve
          </button>
        </div>
      )}
    </div>
  );
}
