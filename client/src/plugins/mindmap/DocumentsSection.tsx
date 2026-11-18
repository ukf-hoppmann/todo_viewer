import { useTranslation } from "react-i18next";
import { DocumentsSection as SharedDocumentsSection, type DocumentsLabels } from "../../shared";
import { toWriteError, useAppendEntryMutation, useGetDocumentQuery, usePutDocumentMutation, type NodeOut } from "./api";

function useNodeDocument(uid: string, name: string) {
	const { data, refetch } = useGetDocumentQuery({ uid, name });
	return { document: data, refetch: async () => (await refetch()).data };
}

/** The section "Documents" of the node detail: the notes and specs of the node (shared building block). */
export function DocumentsSection({ node }: { node: NodeOut }) {
	const { t } = useTranslation("mindmap");
	const [put] = usePutDocumentMutation();
	const [append] = useAppendEntryMutation();
	const labels: DocumentsLabels = {
		none: t("documents.none"),
		addEntry: t("documents.addEntry"),
		addSpec: t("documents.addSpec"),
		large: t("documents.large"),
		edit: t("action.edit"),
		close: t("action.close"),
		cancel: t("form.cancel"),
		save: t("form.save"),
		topic: t("documents.topic"),
		discussed: t("documents.discussed"),
		decided: t("documents.decided"),
		open: t("documents.open"),
		onePerLine: t("documents.onePerLine"),
		summary: t("field.title"),
		specName: t("documents.specName"),
		specNameHint: t("documents.specNameHint", { label: node.label }),
		conflict: t("documents.conflict"),
		showCurrent: t("documents.showCurrent"),
		saveAnyway: t("documents.saveAnyway"),
		currentState: t("documents.currentState"),
		toc: t("documents.toc"),
	};

	return (
		<SharedDocumentsSection
			owner={node.uid}
			names={node.documents}
			readOnly={false}
			spec={{ name: `${node.label}_spec.md`, content: `# ${node.label} — ${node.title}\n` }}
			useDocument={useNodeDocument}
			saveDocument={async (name, content, version) => {
				try {
					return await put({ uid: node.uid, name, content, version }).unwrap();
				} catch (failure) {
					throw toWriteError(failure);
				}
			}}
			appendEntry={async ({ topic, discussed, decided, open }) => {
				await append({ uid: node.uid, topic, discussed, decided, open }).unwrap();
			}}
			errorMessage={(failure) => toWriteError(failure).message}
			labels={labels}
		/>
	);
}
