import { type FC, type FormEvent, useState } from "react";

import { login, register } from "./auth";

/** Login / register screen shown until the user is authenticated (decision 0009). */
export const LoginScreen: FC<{ onAuthed: () => void }> = ({ onAuthed }) => {
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
      if (isRegister) await register(email, name, password);
      else await login(email, password);
      onAuthed();
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo iniciar sesión");
    } finally {
      setBusy(false);
    }
  }

  const field =
    "border-border/60 focus:border-ring w-full rounded-lg border bg-transparent px-3 py-2 text-sm outline-none";

  return (
    <div className="flex h-full items-center justify-center px-4">
      <form
        onSubmit={onSubmit}
        className="border-border bg-card w-full max-w-sm rounded-2xl border p-6 shadow-sm"
      >
        <div className="mb-1 text-center text-3xl">🚚</div>
        <h1 className="mb-1 text-center text-xl font-semibold">DYR Transportes — Data Assistant</h1>
        <p className="text-muted-foreground mb-5 text-center text-sm">
          {isRegister ? "Creá tu cuenta para empezar" : "Iniciá sesión para continuar"}
        </p>

        <div className="flex flex-col gap-2.5">
          {isRegister && (
            <input
              className={field}
              type="text"
              placeholder="Nombre"
              aria-label="Nombre"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          )}
          <input
            className={field}
            type="email"
            placeholder="Email"
            aria-label="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className={field}
            type="password"
            placeholder="Contraseña"
            aria-label="Contraseña"
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
          {busy ? "…" : isRegister ? "Crear cuenta" : "Entrar"}
        </button>

        <button
          type="button"
          onClick={() => {
            setMode(isRegister ? "login" : "register");
            setError(null);
          }}
          className="text-muted-foreground hover:text-foreground mt-3 w-full text-center text-xs"
        >
          {isRegister ? "¿Ya tenés cuenta? Iniciá sesión" : "¿No tenés cuenta? Registrate"}
        </button>
      </form>
    </div>
  );
};
