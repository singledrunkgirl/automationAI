import { describe, it, expect } from "@jest/globals";
import { ASK_MODEL_OPTIONS, AGENT_MODEL_OPTIONS } from "../constants";
import { myProvider, resolveTierToProviderKey } from "@/lib/ai/providers";
import type { ChatMode } from "@/types/chat";

/**
 * Drift guard: every selectable HackWithAI v2 tier must resolve to a provider key
 * registered with `myProvider` in *both* modes. Without this, picking the
 * tier from the UI would crash on `myProvider.languageModel()`.
 */
describe("ModelSelector tier ↔ provider drift", () => {
  const allOptions = [...ASK_MODEL_OPTIONS, ...AGENT_MODEL_OPTIONS];

  it("every option in both lineups resolves to a registered provider", () => {
    for (const mode of ["ask", "agent"] as ChatMode[]) {
      const options =
        mode === "agent" ? AGENT_MODEL_OPTIONS : ASK_MODEL_OPTIONS;
      for (const option of options) {
        const providerKey = resolveTierToProviderKey(option.id, mode);
        expect(providerKey).not.toBeNull();
        expect(() =>
          myProvider.languageModel(providerKey as string),
        ).not.toThrow();
      }
    }
  });

  it("ask + agent lineups expose the same tier ids", () => {
    const askIds = new Set(ASK_MODEL_OPTIONS.map((o) => o.id));
    const agentIds = new Set(AGENT_MODEL_OPTIONS.map((o) => o.id));
    expect([...askIds].sort()).toEqual([...agentIds].sort());
  });

  it("HackWithAI v2 Standard resolves to different providers per mode", () => {
    expect(resolveTierToProviderKey("hwai-standard", "ask")).toBe(
      "model-gemini-3-flash",
    );
    expect(resolveTierToProviderKey("hwai-standard", "agent")).toBe(
      "model-kimi-k2.6",
    );
  });

  it("HackWithAI v2 Pro and Max resolve to the same provider in both modes", () => {
    expect(resolveTierToProviderKey("hwai-pro", "ask")).toBe(
      "model-sonnet-4.6",
    );
    expect(resolveTierToProviderKey("hwai-pro", "agent")).toBe(
      "model-sonnet-4.6",
    );
    expect(resolveTierToProviderKey("hwai-max", "ask")).toBe(
      "model-opus-4.6",
    );
    expect(resolveTierToProviderKey("hwai-max", "agent")).toBe(
      "model-opus-4.6",
    );
  });

  it("'auto' returns null (caller routes to the auto router)", () => {
    expect(resolveTierToProviderKey("auto", "ask")).toBeNull();
    expect(resolveTierToProviderKey("auto", "agent")).toBeNull();
  });

  it("hover-popup descriptions are present for every HackWithAI v2 tier", () => {
    const tiered = allOptions.filter((o) => o.label.startsWith("HackWithAI v2"));
    expect(tiered.length).toBeGreaterThan(0);
    for (const option of tiered) {
      expect(option.description).toBeTruthy();
      expect(option.poweredBy).toBeTruthy();
    }
  });
});
