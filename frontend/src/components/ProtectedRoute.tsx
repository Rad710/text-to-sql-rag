import { Navigate, Outlet } from "react-router";

import { useAuth } from "@/hooks/useAuth";

/** Route guard: waits for the auth check, then renders the child route or redirects to /login. */
export function ProtectedRoute() {
    const { user, loading } = useAuth();
    if (loading) {
        return (
            <div className="text-muted-foreground flex h-full items-center justify-center text-sm">
                Cargando…
            </div>
        );
    }
    return user ? <Outlet /> : <Navigate to="/login" replace />;
}
