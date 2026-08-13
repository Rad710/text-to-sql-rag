// i18n setup (task 0040). Auto-detects the machine language on first load (navigator) and remembers the
// choice in localStorage. Two languages: es · en. A Spanish browser gets Spanish; every other locale
// falls back to English (`fallbackLng: "en"`). Importable outside React (e.g. lib/runtime.ts) via the
// default `i18n` instance and `i18n.t(...)`.

import i18n from "i18next";
import LanguageDetector from "i18next-browser-languagedetector";
import { initReactI18next } from "react-i18next";

import { en } from "./en";
import { es } from "./es";

export const SUPPORTED_LANGUAGES = ["es", "en"] as const;
export type Language = (typeof SUPPORTED_LANGUAGES)[number];

i18n.use(LanguageDetector)
    .use(initReactI18next)
    .init({
        resources: { es: { translation: es }, en: { translation: en } },
        fallbackLng: "en", // Spanish browsers → es; every other locale → en
        supportedLngs: SUPPORTED_LANGUAGES,
        // Map region variants ("en-US" → "en") so navigator detection resolves to a supported base.
        nonExplicitSupportedLngs: true,
        load: "languageOnly",
        interpolation: { escapeValue: false }, // React already escapes
        detection: {
            order: ["localStorage", "navigator"],
            lookupLocalStorage: "dyr_lang",
            caches: ["localStorage"],
        },
    });

export default i18n;
