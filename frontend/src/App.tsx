import { BrowserRouter } from "react-router";

import { AppRoutes } from "@/components/AppRoutes";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AuthProvider } from "@/context/AuthProvider";

/** App shell: router + global providers. Routes and screens live under pages/ and components/. */
export default function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <TooltipProvider>
                    <AppRoutes />
                </TooltipProvider>
            </AuthProvider>
        </BrowserRouter>
    );
}
