import { useContext } from "react";

import { AuthContext } from "@/context/AuthProvider";

/** Access the auth session. Must be used within an <AuthProvider>. */
export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return ctx;
}
