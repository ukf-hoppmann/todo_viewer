import CloseIcon from "@mui/icons-material/Close";
import { Alert, Box, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { IconAction } from "../../shared";
import { useItemDetail, useShownStatuses } from "../backlog";
import { errorMessage, useAssignItemMutation, useGetItemNodeQuery, useGetTreeQuery, useUnassignItemMutation } from "./api";
import { visibleNodes } from "./domain/tree";
import { mindmapTestIds } from "./testIds";

const INDENT = "  ";

/**
 * In the detail panel of an item (slot `backlog.item-detail`): the mind map node the item hangs on, chosen from the
 * tree of its project. An item that hangs on a node of its own can be released; one that hangs on a node only because
 * its parent does is marked as inherited. Choosing a node assigns the item to it and takes it from its former node.
 * Nothing is shown for an item in the trash.
 */
export function ItemNodeSection() {
	const { t } = useTranslation("mindmap");
	const item = useItemDetail();
	const statuses = useShownStatuses();
	const { data: where } = useGetItemNodeQuery(item.uid, { skip: item.deleted });
	const { data: tree } = useGetTreeQuery({ project: item.project_uid, statuses }, { skip: item.deleted });
	const [assignItem] = useAssignItemMutation();
	const [unassignItem] = useUnassignItemMutation();
	const [error, setError] = useState<string>();

	const options = useMemo(() => {
		const nodes = tree?.nodes ?? [];
		const open = Object.fromEntries(nodes.map((node) => [node.uid, "open" as const]));
		return visibleNodes(item.project_uid, nodes, open)
			.filter((entry) => entry.node !== undefined)
			.map((entry) => ({ uid: entry.id, title: entry.node!.title, depth: entry.depth }));
	}, [tree, item.project_uid]);

	if (item.deleted) return null;
	const current = where?.node_uid ?? "";
	const fail = (failure: unknown) => setError(errorMessage(failure, t("error.failed")));
	return (
		<Box data-testid={mindmapTestIds.itemNode}>
			<Typography variant="overline" color="text.secondary">
				{t("itemNode.title")}
			</Typography>
			{error && (
				<Alert severity="error" onClose={() => setError(undefined)} data-testid={mindmapTestIds.itemNodeError}>
					{error}
				</Alert>
			)}
			<Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
				<TextField
					select
					size="small"
					fullWidth
					label={t("itemNode.node")}
					value={options.some((option) => option.uid === current) ? current : ""}
					onChange={(event) => {
						setError(undefined);
						assignItem({ node: event.target.value, item: item.uid, replace: true }).unwrap().catch(fail);
					}}
					slotProps={{ htmlInput: { "data-testid": mindmapTestIds.itemNodeSelect } }}
				>
					{options.map((option) => (
						<MenuItem key={option.uid} value={option.uid}>
							{INDENT.repeat(option.depth - 1)}
							{option.title}
						</MenuItem>
					))}
				</TextField>
				{where?.explicit && (
					<IconAction label={t("itemNode.release")} icon={CloseIcon} onClick={() => void unassignItem(item.uid).unwrap().catch(fail)} testId={mindmapTestIds.itemNodeRelease} />
				)}
			</Stack>
			<Typography variant="caption" color="text.secondary">
				{current === "" ? t("itemNode.unassigned") : where?.explicit ? "" : t("itemNode.inherited")}
			</Typography>
		</Box>
	);
}
