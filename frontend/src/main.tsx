import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import App from "./App";
import "./i18n"; // initialize i18next (task 0040) before the app renders
import "./index.css";

const root = document.getElementById("root");
if (!root) throw new Error("Root element #root not found");

createRoot(root).render(
    <StrictMode>
        <App />
    </StrictMode>,
);
