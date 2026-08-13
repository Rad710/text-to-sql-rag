import { useEffect } from "react";
import { BrowserRouter } from "react-router";

import { bootstrapSession } from "@/api/auth";
import { AppRoutes } from "@/components/AppRoutes";
import { TooltipProvider } from "@/components/ui/tooltip";

/** App shell: router + providers. Session lives in the `useSession` store; bootstrap runs once here. */
export default function App() {
    useEffect(() => {
        void bootstrapSession();
    }, []);

    return (
        <BrowserRouter>
            <TooltipProvider>
                <AppRoutes />
            </TooltipProvider>
        </BrowserRouter>
    );
}
