import { Box } from "@mui/material";
import { useTranslation } from "react-i18next";
import { DetailPanel, DetailSection, InlineField } from "../../shared";
import { DocumentsSection } from "./DocumentsSection";
import { errorMessage, useUpdateNodeMutation, type NodeOut } from "./api";
import { mindmapTestIds } from "./testIds";

/**
 * The detail of a node in the detail column: its label, title and text as fields that save at once (a rejected
 * save shows the message of the server at the field; an empty text removes it), and the section "Documents".
 */
export function NodeDetail({ node, onClose }: { node: NodeOut; onClose: () => void }) {
	const { t } = useTranslation("mindmap");
	const [updateNode] = useUpdateNodeMutation();
	const save = async (fields: { title?: string; text?: string }) => {
		try {
			await updateNode({ uid: node.uid, version: node.version, ...fields }).unwrap();
		} catch (failure) {
			throw new Error(errorMessage(failure, t("error.failed")), { cause: failure });
		}
	};
	return (
		<Box data-testid={mindmapTestIds.detail}>
			<DetailPanel title={node.title} subtitle={node.label} onClose={onClose} closeLabel={t("action.close")}>
				<Box sx={{ p: 1.5, display: "flex", flexDirection: "column", gap: 2 }}>
					<InlineField
						kind="text"
						id="title"
						label={t("field.title")}
						value={node.title}
						onSave={(title) => {
							if (title.trim() === "") throw new Error(t("error.titleEmpty"));
							return save({ title: title.trim() });
						}}
					/>
					<InlineField kind="text" id="text" label={t("field.text")} value={node.text ?? ""} multiline onSave={(text) => save({ text })} />
					<DetailSection id="documents" title={t("field.documents")}>
						<DocumentsSection node={node} />
					</DetailSection>
				</Box>
			</DetailPanel>
		</Box>
	);
}
