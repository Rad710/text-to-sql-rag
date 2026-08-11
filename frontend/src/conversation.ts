// Tracks the active conversation id so the runtime adapter can thread it on /chat (task 0019).
// Lives outside React (like the auth token) so the module-level adapter can read/update it.

let currentId: string | null = null;
let listener: ((id: string) => void) | null = null;

export function getConversationId(): string | null {
  return currentId;
}

export function setConversationId(id: string | null): void {
  currentId = id;
}

/** Register a callback fired when a turn (re)identifies its conversation — App uses it to refresh. */
export function onConversationStarted(cb: ((id: string) => void) | null): void {
  listener = cb;
}

/** Called by the adapter when /chat emits its `conversation` event. */
export function notifyConversation(id: string): void {
  currentId = id;
  listener?.(id);
}
