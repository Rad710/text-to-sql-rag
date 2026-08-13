export const es = {
    common: {
        logout: "Salir",
        loading: "Cargando…",
        newConversation: "+ Nueva conversación",
        noConversations: "Sin conversaciones todavía",
        openMenu: "Abrir conversaciones",
        closeMenu: "Cerrar menú",
    },
    welcome: {
        title: "¿Qué querés saber?",
        subtitle: "Preguntá sobre viajes, choferes, rutas y facturación",
    },
    // Example prompts shown on the empty state — sent verbatim as the question.
    suggestions: [
        "facturación total por ruta",
        "cuántos viajes hizo cada chofer y cuántos kilos",
        "planillas sin cobrar y su total pendiente",
        "choferes con liquidaciones impagas y monto pendiente",
    ],
    login: {
        signInSubtitle: "Iniciá sesión para continuar",
        signUpSubtitle: "Creá tu cuenta para empezar",
        name: "Nombre",
        email: "Email",
        password: "Contraseña",
        signIn: "Entrar",
        signUp: "Crear cuenta",
        toSignUp: "¿No tenés cuenta? Registrate",
        toSignIn: "¿Ya tenés cuenta? Iniciá sesión",
    },
    errors: {
        invalidCredentials: "Email o contraseña incorrectos",
        emailTaken: "Ese email ya está registrado",
        invalidInput: "Revisá el email y que la contraseña tenga al menos 8 caracteres",
        signInFailed: "No se pudo iniciar sesión",
        generic: "Ocurrió un error",
    },
    result: {
        table: "Tabla",
        chart: "Gráfico",
        loadingChart: "Cargando gráfico…",
        rows_one: "{{count}} fila",
        rows_other: "{{count}} filas",
        truncated: ", truncado",
    },
    feedback: {
        good: "Buena respuesta",
        bad: "Mala respuesta",
    },
    chat: {
        sessionExpired: "⚠️ Tu sesión expiró. Iniciá sesión de nuevo.",
        rateLimitMinute: "Alcanzaste el límite de consultas por minuto.",
        rateLimitDay: "Alcanzaste el límite diario de consultas.",
        retrySeconds: " Probá de nuevo en {{seconds}} s.",
        retryLater: " Probá de nuevo más tarde.",
        error: "⚠️ {{status}} {{statusText}}",
    },
};
