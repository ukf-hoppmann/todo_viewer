import { Alert, Box, Button, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { errorMessage, useListRemovedPlacementsQuery, useRestoreNodePlacementMutation, type NodeOut, type RemovedFromOut } from "./api";
import { mindmapTestIds } from "./testIds";

/**
 * "Früher in …" in the detail of a node: the trees the branch was taken out of with "Hier entfernen". "Wieder einsetzen"
 * puts it back where it stood, with the sub-nodes removed together with it. When the old parent is gone the branch comes
 * under the root of the map; the list says so before and a notice after. Nothing is shown when no placement is remembered.
 */
export function RemovedPlacementsSection({ node }: { node: NodeOut }) {
	const { t } = useTranslation("mindmap");
	const { data: removed } = useListRemovedPlacementsQuery(node.uid);
	const [restore] = useRestoreNodePlacementMutation();
	const [message, setMessage] = useState<{ severity: "info" | "error"; text: string }>();
	const label = (entry: RemovedFromOut) => (entry.kind === "project" ? t("maps.projectTree", { name: entry.name }) : entry.name);
	if ((removed ?? []).length === 0 && !message) return null;
	const put = (entry: RemovedFromOut) => {
		setMessage(undefined);
		restore({ ref: node.uid, version: node.version, tree: entry.tree_uid })
			.unwrap()
			.then((done) =>
				setMessage(
					done.fell_back_to_root
						? { severity: "info", text: t("removed.restoredAtRoot", { title: node.title, name: label(entry) }) }
						: { severity: "info", text: t("removed.restored", { name: label(entry) }) },
				),
			)
			.catch((failure: unknown) => setMessage({ severity: "error", text: errorMessage(failure, t("error.failed")) }));
	};
	return (
		<Box data-testid={mindmapTestIds.removedSection}>
			<Typography variant="subtitle2">{t("removed.title")}</Typography>
			<Stack spacing={0.5}>
				{(removed ?? []).map((entry) => (
					<Box key={entry.tree_uid} sx={{ display: "flex", alignItems: "center", gap: 1 }} data-testid={mindmapTestIds.removedEntry(entry.tree_uid)}>
						<Box sx={{ flex: 1 }}>
							<Typography variant="body2">{t("removed.tree", { name: label(entry), count: entry.nodes })}</Typography>
							{!entry.parent_available && <Typography variant="caption">{t("removed.parentGone")}</Typography>}
						</Box>
						<Button size="small" onClick={() => put(entry)} data-testid={mindmapTestIds.removedRestore(entry.tree_uid)}>
							{t("removed.restore")}
						</Button>
					</Box>
				))}
			</Stack>
			{message && (
				<Alert severity={message.severity} sx={{ mt: 1 }} data-testid={mindmapTestIds.removedNotice}>
					{message.text}
				</Alert>
			)}
		</Box>
	);
}
