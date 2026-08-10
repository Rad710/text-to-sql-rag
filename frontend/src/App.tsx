import { AssistantRuntimeProvider, ThreadPrimitive, useLocalRuntime } from "@assistant-ui/react";
import type { FC } from "react";

import { Thread } from "@/components/assistant-ui/thread";
import { TooltipProvider } from "@/components/ui/tooltip";

import { adapter } from "./runtime";

const SUGGESTIONS = [
  "facturación total por ruta",
  "how many shipments did each driver make and total kilos",
  "planillas sin cobrar y su total pendiente",
  "drivers with unpaid settlements and pending amount",
];

// Branded, bilingual empty state — replaces the Thread's default "How can I help you today?".
const Welcome: FC = () => (
  <div className="mb-8 flex flex-col items-center px-4 text-center">
    <div className="mb-3 text-4xl">🚚</div>
    <h1 className="text-2xl font-semibold tracking-tight">¿Qué querés saber?</h1>
    <p className="text-muted-foreground mt-1.5 text-sm">
      Preguntá en español o inglés · Ask about shipments, drivers, routes & billing
    </p>
    <div className="mt-6 flex flex-wrap justify-center gap-2">
      {SUGGESTIONS.map((s) => (
        <ThreadPrimitive.Suggestion
          key={s}
          prompt={s}
          method="replace"
          autoSend
          className="border-border/60 text-foreground hover:bg-muted max-w-xs cursor-pointer rounded-full border px-3.5 py-1.5 text-sm transition-colors"
        >
          {s}
        </ThreadPrimitive.Suggestion>
      ))}
    </div>
  </div>
);

export default function App() {
  const runtime = useLocalRuntime(adapter);
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <TooltipProvider>
        <div className="flex h-full flex-col">
          <header className="border-border flex items-baseline gap-3 border-b px-6 py-3.5">
            <span className="font-semibold">🚚 DYR Transportes — Data Assistant</span>
            <span className="text-muted-foreground text-xs">text-to-SQL · RAG · mock mode</span>
          </header>
          <div className="min-h-0 flex-1">
            <Thread components={{ Welcome }} />
          </div>
        </div>
      </TooltipProvider>
    </AssistantRuntimeProvider>
  );
}
