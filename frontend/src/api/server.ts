// Runtime info from the API's /health, used to label the UI with the real mode (not a hardcoded string).

/** The header label for the current LLM mode: the model name in openai mode, else "mock mode". */
export async function fetchServerMode(): Promise<string> {
    try {
        const res = await fetch("/health");
        const info = (await res.json()) as { llm_mode?: string; model?: string };
        return info.llm_mode === "openai" ? (info.model ?? "live") : "mock mode";
    } catch {
        return "mock mode";
    }
}
