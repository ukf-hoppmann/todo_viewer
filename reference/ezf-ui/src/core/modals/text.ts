import type { TFunction } from "i18next";

/**
 * A finished text (e.g. from the backend) or an i18n key with params. The key
 * may carry a namespace (`variant-filter:errors.x`); without one, `core` applies.
 */
export type Text = string | { key: string; params?: Record<string, unknown> };

/** Translates a `Text` at display time. */
export function translateText(t: TFunction, text: Text): string {
	if (typeof text === "string") return text;
	return t(text.key, { ...text.params, ns: "core" });
}
