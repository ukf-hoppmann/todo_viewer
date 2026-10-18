import { useTranslation } from "react-i18next";
import { DocumentsSection as SharedDocumentsSection, type DocumentsLabels } from "../../shared";
import { toWriteError, useAppendEntryMutation, useGetDocumentQuery, usePutDocumentMutation, type NoteOut } from "./api";

function useNoteDocument(uid: string, name: string) {
	const { data, refetch } = useGetDocumentQuery({ uid, name });
	return { document: data, refetch: async () => (await refetch()).data };
}

/** The section "Documents" of the note detail: the notes and specs of the note (shared building block). */
export function DocumentsSection({ note }: { note: NoteOut }) {
	const { t } = useTranslation("notes");
	const [put] = usePutDocumentMutation();
	const [append] = useAppendEntryMutation();
	const labels: DocumentsLabels = {
		none: t("documents.none"),
		addEntry: t("documents.addEntry"),
		addSpec: t("documents.addSpec"),
		large: t("documents.large"),
		edit: t("action.edit"),
		close: t("form.close"),
		cancel: t("form.cancel"),
		save: t("form.save"),
		topic: t("documents.topic"),
		discussed: t("documents.discussed"),
		decided: t("documents.decided"),
		open: t("documents.open"),
		onePerLine: t("documents.onePerLine"),
		summary: t("field.summary"),
		specName: t("documents.specName"),
		specNameHint: t("documents.specNameHint", { label: note.label }),
		conflict: t("documents.conflict"),
		showCurrent: t("documents.showCurrent"),
		saveAnyway: t("documents.saveAnyway"),
		currentState: t("documents.currentState"),
		toc: t("documents.toc"),
	};

	return (
		<SharedDocumentsSection
			owner={note.uid}
			names={note.documents}
			readOnly={note.archived || note.deleted}
			spec={{ name: `${note.label}_spec.md`, content: `# ${note.label} — ${note.summary}\n` }}
			useDocument={useNoteDocument}
			saveDocument={async (name, content, version) => {
				try {
					return await put({ uid: note.uid, name, content, version }).unwrap();
				} catch (failure) {
					throw toWriteError(failure);
				}
			}}
			appendEntry={async ({ topic, discussed, decided, open }) => {
				await append({ uid: note.uid, topic, discussed, decided, open }).unwrap();
			}}
			errorMessage={(failure) => toWriteError(failure).message}
			labels={labels}
		/>
	);
}
