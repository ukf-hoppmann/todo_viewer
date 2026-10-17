import type { NoteNoticeOut } from "./api";

/** What a notice says, with the element it is about. */
export function noticeText(notice: NoteNoticeOut, t: (key: string, options?: Record<string, unknown>) => string): string {
	const source = notice.source ? `${notice.source.label} — ${notice.source.title}` : "?";
	return t(`notices.kind.${notice.kind}`, { item: source, note: source, defaultValue: notice.kind });
}
