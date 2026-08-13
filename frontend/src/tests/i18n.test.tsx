import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useTranslation } from "react-i18next";
import { afterEach, expect, test } from "vitest";

import { LanguageToggle } from "@/components/LanguageToggle";
import i18n from "@/i18n";

/** Renders a translated string so we can observe the language switch. */
function Probe() {
    const { t } = useTranslation();
    return <span data-testid="probe">{t("common.logout")}</span>;
}

afterEach(async () => {
    await i18n.changeLanguage("en"); // reset to the pinned test language
});

test("the header toggle switches the UI language (en ⇄ es)", async () => {
    render(
        <>
            <LanguageToggle />
            <Probe />
        </>,
    );
    // Setup pins en.
    expect(screen.getByTestId("probe")).toHaveTextContent("Log out");

    await userEvent.click(screen.getByRole("button", { name: "es" }));
    expect(screen.getByTestId("probe")).toHaveTextContent("Salir");
    expect(screen.getByRole("button", { name: "es" })).toHaveAttribute("aria-pressed", "true");

    await userEvent.click(screen.getByRole("button", { name: "en" }));
    expect(screen.getByTestId("probe")).toHaveTextContent("Log out");
});
