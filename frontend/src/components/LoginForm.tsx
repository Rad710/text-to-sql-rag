import { type FC, type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { login, register } from "@/api/auth";

/**
 * The login / register form card (decisions 0009, 0013). On success `login`/`register` set the user in
 * the session store, and the LoginPage redirects to `/`. Strings are localized (task 0040).
 */
export const LoginForm: FC = () => {
    const { t } = useTranslation();
    const [mode, setMode] = useState<"login" | "register">("login");
    const [email, setEmail] = useState("");
    const [name, setName] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);

    const isRegister = mode === "register";

    async function onSubmit(e: FormEvent) {
        e.preventDefault();
        setBusy(true);
        setError(null);
        try {
            if (isRegister) {
                await register(email, name, password);
            } else {
                await login(email, password);
            }
        } catch (err) {
            // The thrown message is an i18n key (see api/auth); unknown ones fall back to generic.
            const key = err instanceof Error ? err.message : "errors.signInFailed";
            setError(t(key, { defaultValue: t("errors.signInFailed") }));
        } finally {
            setBusy(false);
        }
    }

    const field =
        "border-border/60 focus:border-ring w-full rounded-lg border bg-transparent px-3 py-2 text-sm outline-none";

    return (
        <form
            onSubmit={onSubmit}
            className="border-border bg-card w-full max-w-sm rounded-2xl border p-6 shadow-sm"
        >
            <div className="mb-1 text-center text-3xl">🚚</div>
            <h1 className="mb-1 text-center text-xl font-semibold">
                DYR Transportes — Data Assistant
            </h1>
            <p className="text-muted-foreground mb-5 text-center text-sm">
                {isRegister ? t("login.signUpSubtitle") : t("login.signInSubtitle")}
            </p>

            <div className="flex flex-col gap-2.5">
                {isRegister && (
                    <input
                        className={field}
                        type="text"
                        placeholder={t("login.name")}
                        aria-label={t("login.name")}
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                )}
                <input
                    className={field}
                    type="email"
                    placeholder={t("login.email")}
                    aria-label={t("login.email")}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />
                <input
                    className={field}
                    type="password"
                    placeholder={t("login.password")}
                    aria-label={t("login.password")}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
            </div>

            {error && <p className="text-destructive mt-3 text-sm">{error}</p>}

            <button
                type="submit"
                disabled={busy}
                className="bg-primary text-primary-foreground mt-4 w-full rounded-lg py-2 text-sm font-medium disabled:opacity-50"
            >
                {busy ? "…" : isRegister ? t("login.signUp") : t("login.signIn")}
            </button>

            <button
                type="button"
                onClick={() => {
                    setMode(isRegister ? "login" : "register");
                    setError(null);
                }}
                className="text-muted-foreground hover:text-foreground mt-3 w-full text-center text-xs"
            >
                {isRegister ? t("login.toSignIn") : t("login.toSignUp")}
            </button>
        </form>
    );
};
