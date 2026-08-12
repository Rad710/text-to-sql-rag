import {
    createContext,
    type FC,
    type ReactNode,
    useCallback,
    useEffect,
    useMemo,
    useState,
} from "react";

import { type AuthUser, clearToken, fetchMe, onUnauthorized } from "@/api/auth";

export type AuthValue = {
    user: AuthUser | null;
    loading: boolean;
    /** Re-fetch the current user (e.g. after login/register) so consumers re-render. */
    refresh: () => Promise<void>;
    logout: () => void;
};

export const AuthContext = createContext<AuthValue | null>(null);

/**
 * Owns the auth session: loads the current user once on mount and clears it on a mid-session 401
 * (via onUnauthorized) so the router bounces back to /login.
 */
export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<AuthUser | null>(null);
    const [loading, setLoading] = useState(true);

    const refresh = useCallback(async () => {
        setUser(await fetchMe());
    }, []);

    const logout = useCallback(() => {
        clearToken();
        setUser(null);
    }, []);

    useEffect(() => {
        let active = true;
        async function loadUser() {
            const me = await fetchMe();
            if (active) {
                setUser(me);
                setLoading(false);
            }
        }
        void loadUser();
        onUnauthorized(logout);
        return () => {
            active = false;
            onUnauthorized(null);
        };
    }, [logout]);

    const value = useMemo<AuthValue>(
        () => ({ user, loading, refresh, logout }),
        [user, loading, refresh, logout],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
