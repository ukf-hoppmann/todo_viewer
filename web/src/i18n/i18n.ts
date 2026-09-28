import { createContext, useContext } from "react";
import { ApiError } from "../api/client";
import { type Lang, MESSAGES, type MessageKey, VOCAB_DE, type VocabKind } from "./messages";

export interface I18n {
  lang: Lang;
  t: (key: MessageKey, vars?: Record<string, string | number>) => string;
  /** Display name of a file value (status, priority, ...); unknown values are shown as-is. */
  vocab: (kind: VocabKind, value: string | null | undefined) => string;
  /** Translated text for an error code, falling back to the server message; details fill {placeholders}. */
  errorText: (code: string | null | undefined, fallback: string, details?: Record<string, string>) => string;
}

export function createI18n(lang: Lang): I18n {
  const t: I18n["t"] = (key, vars) => {
    let text = MESSAGES[lang][key];
    for (const [k, v] of Object.entries(vars ?? {})) text = text.split(`{${k}}`).join(String(v));
    return text;
  };
  const vocab: I18n["vocab"] = (kind, value) => {
    if (value == null) return "";
    return lang === "de" ? (VOCAB_DE[kind][value] ?? value) : value;
  };
  const errorText: I18n["errorText"] = (code, fallback, details) => {
    const key = `err.${code ?? ""}` as MessageKey;
    if (!code || !(key in MESSAGES[lang])) return fallback;
    return t(key, details) + (code === "parse_error" && fallback ? `: ${fallback}` : "");
  };
  return { lang, t, vocab, errorText };
}

export function describeError(i18n: I18n, error: unknown): string {
  if (error instanceof ApiError) return i18n.errorText(error.code, error.message, error.details);
  return error instanceof Error ? error.message : String(error);
}

export const I18nContext = createContext<I18n>(createI18n("de"));

export function useI18n(): I18n {
  return useContext(I18nContext);
}
