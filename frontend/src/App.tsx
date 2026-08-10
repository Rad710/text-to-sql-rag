import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useLocalRuntime,
} from "@assistant-ui/react";
import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown";

import { adapter } from "./runtime";

const SUGGESTIONS = [
  "facturación total por ruta",
  "how many shipments did each driver make and total kilos",
  "planillas sin cobrar y su total pendiente",
  "drivers with unpaid settlements and pending amount",
];

const MarkdownText = () => <MarkdownTextPrimitive />;

const UserMessage = () => (
  <MessagePrimitive.Root className="msg user">
    <MessagePrimitive.Content />
  </MessagePrimitive.Root>
);

const AssistantMessage = () => (
  <MessagePrimitive.Root className="msg assistant">
    <MessagePrimitive.Content components={{ Text: MarkdownText }} />
  </MessagePrimitive.Root>
);

function Thread() {
  return (
    <ThreadPrimitive.Root className="thread">
      <ThreadPrimitive.Viewport className="viewport">
        <ThreadPrimitive.Empty>
          <div className="welcome">
            <h1>What would you like to know?</h1>
            <p>Ask in English or Spanish · Preguntá en español o inglés</p>
            <div className="suggestions">
              {SUGGESTIONS.map((s) => (
                <ThreadPrimitive.Suggestion
                  key={s}
                  prompt={s}
                  method="replace"
                  autoSend
                  className="suggestion"
                >
                  {s}
                </ThreadPrimitive.Suggestion>
              ))}
            </div>
          </div>
        </ThreadPrimitive.Empty>

        <ThreadPrimitive.Messages
          components={{ UserMessage, AssistantMessage }}
        />

        <ThreadPrimitive.ViewportFooter className="composer-row">
          <ComposerPrimitive.Root className="composer">
            <ComposerPrimitive.Input
              className="composer-input"
              placeholder="Ask about shipments, drivers, routes, billing…"
              autoFocus
            />
            <ComposerPrimitive.Send className="composer-send" aria-label="Send">
              ↑
            </ComposerPrimitive.Send>
          </ComposerPrimitive.Root>
        </ThreadPrimitive.ViewportFooter>
      </ThreadPrimitive.Viewport>
    </ThreadPrimitive.Root>
  );
}

export default function App() {
  const runtime = useLocalRuntime(adapter);
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <div className="app">
        <header className="topbar">
          <span className="brand">🚚 DYR Transportes — Data Assistant</span>
          <span className="tag">text-to-SQL · RAG · mock mode</span>
        </header>
        <Thread />
      </div>
    </AssistantRuntimeProvider>
  );
}
