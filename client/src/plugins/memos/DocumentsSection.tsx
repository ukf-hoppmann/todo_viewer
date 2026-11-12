import { useTranslation } from "react-i18next";
import { DocumentsSection as SharedDocumentsSection, type DocumentsLabels } from "../../shared";
import { toWriteError, useAppendEntryMutation, useGetDocumentQuery, usePutDocumentMutation, type MemoOut } from "./api";

function useMemoDocument(uid: string, name: string) {
	const { data, refetch } = useGetDocumentQuery({ uid, name });
	return { document: data, refetch: async () => (await refetch()).data };
}

/** The section "Documents" of the memo detail: the memos and specs of the memo (shared building block). */
export function DocumentsSection({ memo }: { memo: MemoOut }) {
	const { t } = useTranslation("memos");
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
		specNameHint: t("documents.specNameHint", { label: memo.label }),
		conflict: t("documents.conflict"),
		showCurrent: t("documents.showCurrent"),
		saveAnyway: t("documents.saveAnyway"),
		currentState: t("documents.currentState"),
		toc: t("documents.toc"),
	};

	return (
		<SharedDocumentsSection
			owner={memo.uid}
			names={memo.documents}
			readOnly={memo.archived || memo.deleted}
			spec={{ name: `${memo.label}_spec.md`, content: `# ${memo.label} — ${memo.summary}\n` }}
			useDocument={useMemoDocument}
			saveDocument={async (name, content, version) => {
				try {
					return await put({ uid: memo.uid, name, content, version }).unwrap();
				} catch (failure) {
					throw toWriteError(failure);
				}
			}}
			appendEntry={async ({ topic, discussed, decided, open }) => {
				await append({ uid: memo.uid, topic, discussed, decided, open }).unwrap();
			}}
			errorMessage={(failure) => toWriteError(failure).message}
			labels={labels}
		/>
	);
}
