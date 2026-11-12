import type { MemoHintOut } from "./api";

/** What a hint says, with the element it is about. */
export function hintText(hint: MemoHintOut, t: (key: string, options?: Record<string, unknown>) => string): string {
	const source = hint.source ? `${hint.source.label} — ${hint.source.title}` : "?";
	return t(`hints.kind.${hint.kind}`, { item: source, memo: source, defaultValue: hint.kind });
}
