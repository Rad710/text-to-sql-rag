import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

// Single source of truth for session state (decision 0013). Replaces the ad-hoc module-level globals
// that used to live in api/auth, lib/active-conversation, and api/feedback. Readable outside React via
// `useSession.getState()` (the runtime adapter needs that) and reactive inside components via selectors.
//
// The **access token stays in memory only** — never persisted — so it can't outlive the tab. Only the
// **refresh token** is persisted (localStorage), and it's short-lived + rotated + reuse-detected
// server-side, which (with the strict CSP) is what makes the bearer model safe without cookies.

export type AuthUser = { id: string; email: string; name: string };
export type AuthStatus = "loading" | "authenticated" | "anonymous";

type SessionState = {
    accessToken: string | null; // in-memory only
    refreshToken: string | null; // persisted
    user: AuthUser | null;
    status: AuthStatus;
    conversationId: string | null;
    lastAssistantMessageId: string | null;

    setTokens: (accessToken: string, refreshToken: string) => void;
    setAccessToken: (accessToken: string) => void;
    setUser: (user: AuthUser | null) => void;
    setStatus: (status: AuthStatus) => void;
    signOut: () => void;
    setConversationId: (id: string | null) => void;
    setLastAssistantMessageId: (id: string | null) => void;
    resetConversation: () => void;
};

export const useSession = create<SessionState>()(
    persist(
        (set) => ({
            accessToken: null,
            refreshToken: null,
            user: null,
            status: "loading",
            conversationId: null,
            lastAssistantMessageId: null,

            setTokens: (accessToken, refreshToken) => set({ accessToken, refreshToken }),
            setAccessToken: (accessToken) => set({ accessToken }),
            setUser: (user) => set({ user, status: user ? "authenticated" : "anonymous" }),
            setStatus: (status) => set({ status }),
            signOut: () =>
                set({
                    accessToken: null,
                    refreshToken: null,
                    user: null,
                    status: "anonymous",
                    conversationId: null,
                    lastAssistantMessageId: null,
                }),
            setConversationId: (conversationId) => set({ conversationId }),
            setLastAssistantMessageId: (lastAssistantMessageId) => set({ lastAssistantMessageId }),
            resetConversation: () => set({ conversationId: null, lastAssistantMessageId: null }),
        }),
        {
            name: "dyr_session",
            storage: createJSONStorage(() => localStorage),
            // Persist ONLY the refresh token — never the access token or user.
            partialize: (s) => ({ refreshToken: s.refreshToken }),
        },
    ),
);
