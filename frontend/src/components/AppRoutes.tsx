import { Navigate, Route, Routes } from "react-router";

import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ChatPage } from "@/pages/ChatPage";
import { LoginPage } from "@/pages/LoginPage";

/** App routes: /login (public) and / (the chat app, auth-guarded). */
export function AppRoutes() {
    return (
        <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<ProtectedRoute />}>
                <Route path="/" element={<ChatPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    );
}
