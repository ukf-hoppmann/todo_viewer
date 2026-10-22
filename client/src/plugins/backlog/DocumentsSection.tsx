import { useTranslation } from "react-i18next";
import { DocumentsSection as SharedDocumentsSection, type DocumentsLabels } from "../../shared";
import { NotesHead } from "./NotesHead";
import { toWriteError, useAppendNoteMutation, useGetDocumentQuery, usePutDocumentMutation, type ItemOut } from "./api";

function useItemDocument(uid: string, name: string) {
	const { data, refetch } = useGetDocumentQuery({ uid, name });
	return { document: data, refetch: async () => (await refetch()).data };
}

/** The section "Documents" of the item detail: the notes and specs of the item (shared building block). */
export function DocumentsSection({ item }: { item: ItemOut }) {
	const { t } = useTranslation("backlog");
	const [put] = usePutDocumentMutation();
	const [append] = useAppendNoteMutation();
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
		specNameHint: t("documents.specNameHint", { label: item.label }),
		conflict: t("documents.conflict"),
		showCurrent: t("documents.showCurrent"),
		saveAnyway: t("documents.saveAnyway"),
		currentState: t("documents.currentState"),
		toc: t("documents.toc"),
	};

	return (
		<>
		<NotesHead item={item} />
		<SharedDocumentsSection
			owner={item.uid}
			names={[...item.notes, ...item.spec]}
			readOnly={item.deleted}
			spec={{ name: `${item.label}_spec.md`, content: `# ${item.label} — ${item.title}\n` }}
			summary={item.notes.length === 0 && !item.summary ? (item.summary ?? "") : undefined}
			useDocument={useItemDocument}
			saveDocument={async (name, content, version) => {
				try {
					return await put({ uid: item.uid, name, content, version }).unwrap();
				} catch (failure) {
					throw toWriteError(failure);
				}
			}}
			appendEntry={async (entry) => {
				await append({ uid: item.uid, ...entry }).unwrap();
			}}
			errorMessage={(failure) => toWriteError(failure).message}
			labels={labels}
		/>
		</>
	);
}
