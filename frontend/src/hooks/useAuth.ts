import { logout } from "@/api/auth";
import { useSession } from "@/stores/session";

/** The auth session for components: the current user, whether it's still resolving, and logout. */
export function useAuth() {
    const user = useSession((s) => s.user);
    const status = useSession((s) => s.status);
    return { user, loading: status === "loading", logout };
}
