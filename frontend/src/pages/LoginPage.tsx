import { Navigate } from "react-router";

import { LoginForm } from "@/components/LoginForm";
import { useAuth } from "@/hooks/useAuth";

/** /login — the auth screen. Redirects to / once authenticated. */
export function LoginPage() {
    const { user, loading } = useAuth();
    if (loading) {
        return null; // brief; the app root shows nothing until the session resolves
    }
    if (user) {
        return <Navigate to="/" replace />;
    }
    return (
        <div className="flex h-full items-center justify-center px-4">
            <LoginForm />
        </div>
    );
}
