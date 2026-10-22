import { useTranslation } from "react-i18next";

/** The text of a state mark: why the head of the notes is marked (`undefined` when it needs no mark). */
export function useNotesMarkText(state: string | null | undefined) {
	const { t } = useTranslation("backlog");
	return state === "stale" ? t("notes.stale") : state === "missing" ? t("notes.missing") : undefined;
}
