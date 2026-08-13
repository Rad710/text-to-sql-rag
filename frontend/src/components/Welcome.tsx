import { ThreadPrimitive } from "@assistant-ui/react";
import type { FC } from "react";
import { useTranslation } from "react-i18next";

/** Branded empty state — replaces the Thread's default greeting. Suggestions follow the UI language. */
export const Welcome: FC = () => {
    const { t } = useTranslation();
    const suggestions = t("suggestions", { returnObjects: true }) as string[];

    return (
        <div className="mb-8 flex flex-col items-center px-4 text-center">
            <div className="mb-3 text-4xl">🚚</div>
            <h1 className="text-2xl font-semibold tracking-tight">{t("welcome.title")}</h1>
            <p className="text-muted-foreground mt-1.5 text-sm">{t("welcome.subtitle")}</p>
            <div className="mt-6 flex flex-wrap justify-center gap-2">
                {suggestions.map((s) => (
                    <ThreadPrimitive.Suggestion
                        key={s}
                        prompt={s}
                        method="replace"
                        autoSend
                        className="border-border/60 text-foreground hover:bg-muted max-w-xs cursor-pointer rounded-full border px-3.5 py-1.5 text-sm transition-colors"
                    >
                        {s}
                    </ThreadPrimitive.Suggestion>
                ))}
            </div>
        </div>
    );
};
