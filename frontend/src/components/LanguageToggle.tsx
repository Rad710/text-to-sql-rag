import { useTranslation } from "react-i18next";

import { cn } from "@/lib/utils";

/** ES | EN segmented toggle for the UI language (task 0040). Persists via i18next's detector. */
export function LanguageToggle() {
    const { i18n } = useTranslation();
    const current = i18n.resolvedLanguage ?? "es";

    return (
        <div className="border-border/60 flex overflow-hidden rounded-md border text-xs">
            {/* Two toggle buttons, each self-labeled by its text + aria-pressed. */}
            {(["es", "en"] as const).map((lng) => (
                <button
                    key={lng}
                    type="button"
                    onClick={() => void i18n.changeLanguage(lng)}
                    aria-pressed={current === lng}
                    className={cn(
                        "px-2 py-0.5 uppercase transition-colors",
                        current === lng
                            ? "bg-muted text-foreground font-medium"
                            : "text-muted-foreground hover:text-foreground",
                    )}
                >
                    {lng}
                </button>
            ))}
        </div>
    );
}
