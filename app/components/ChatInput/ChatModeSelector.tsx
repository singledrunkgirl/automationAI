"use client";

import { DropdownMenu } from "@/components/ui/dropdown-menu";
import { ModeSelectorTrigger, ModeSelectorContent } from "./ModeSelectorMenu";
import { useGlobalState } from "@/app/contexts/GlobalState";
import { useAuth } from "@workos-inc/authkit-nextjs/components";
import { toast } from "sonner";
import { navigateToAuth, useTauri } from "@/app/hooks/useTauri";
import { isLocalOnlyModeClient } from "@/lib/local-only";

export interface ChatModeSelectorProps {
  className?: string;
}

export function ChatModeSelector({ className }: ChatModeSelectorProps) {
  const {
    chatMode,
    setChatMode,
    temporaryChatsEnabled,
    setSandboxPreference,
    selectedModel,
    setSelectedModel,
  } = useGlobalState();
  const { user } = useAuth();
  const { isTauri } = useTauri();
  const localOnlyMode = isLocalOnlyModeClient();

  const handleAgentModeClick = () => {
    if (!user && !localOnlyMode) {
      navigateToAuth("/signup", { preferSignInForReturningUser: true });
      return;
    }
    if (temporaryChatsEnabled && !localOnlyMode) {
      toast.info("Agent mode requires chat history", {
        description: "Turn off temporary chat to use Agent mode.",
      });
      return;
    }
    setChatMode("agent");
    setSandboxPreference(isTauri || localOnlyMode ? "desktop" : "e2b");
    if (selectedModel !== "auto") {
      setSelectedModel("auto");
    }
  };

  return (
    <>
      <div
        className={`flex items-center gap-1.5 min-w-0 overflow-hidden ${className ?? ""}`}
      >
        <DropdownMenu>
          <ModeSelectorTrigger chatMode={chatMode} />
          <ModeSelectorContent
            setChatMode={setChatMode}
            onAgentModeClick={handleAgentModeClick}
            temporaryChatsEnabled={temporaryChatsEnabled}
          />
        </DropdownMenu>
      </div>
    </>
  );
}
