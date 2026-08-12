import { useEffect, useState } from "react";

import { fetchServerMode } from "@/api/server";

/** The runtime-mode label for the header (the model name in openai mode, else "mock mode"). */
export function useServerMode(): string {
    const [label, setLabel] = useState("");
    useEffect(() => {
        let active = true;
        async function load() {
            const mode = await fetchServerMode();
            if (active) {
                setLabel(mode);
            }
        }
        void load();
        return () => {
            active = false;
        };
    }, []);
    return label;
}
