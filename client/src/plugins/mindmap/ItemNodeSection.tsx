import CloseIcon from "@mui/icons-material/Close";
import { Alert, Box, Button, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { IconAction } from "../../shared";
import { useItemDetail, useShownStatuses } from "../backlog";
import { useProjectSelection } from "../workspace";
import { errorMessage, useAssignItemMutation, useCreateNodeMutation, useGetItemNodeQuery, useGetTreeQuery, useUnassignItemMutation } from "./api";
import { parentForNewNode, visibleNodes } from "./domain/tree";
import { useMapNavigation } from "./navigation";
import { mindmapTestIds } from "./testIds";

const INDENT = "  ";

/**
 * In the detail panel of an item (slot `backlog.item-detail`): the mind map node the item hangs on, chosen from the
 * tree of its project. An item that hangs on a node of its own can be released; one that hangs on a node only because
 * its parent does is marked as inherited. Choosing a node assigns the item to it and takes it from its former node.
 * Three separate actions: "Gehe hin" opens the map at the effective node (the root without one), "Erstelle" creates a
 * node with the title of the item below that node and hangs the item on it, "Anker" (only for an item on a node of its
 * own) opens the map with that node as the root. A project of the item that is hidden is shown and marked first.
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
	const [createNode] = useCreateNodeMutation();
	const { visible, marked, toggleVisible, mark } = useProjectSelection();
	const { openFocus } = useMapNavigation();
	const [error, setError] = useState<string>();
	const [creating, setCreating] = useState(false);

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
	// The map shows the marked project, so a hidden project of the item is shown and marked before the map opens.
	const open = (node: string) => {
		if (!visible.some((project) => project.uid === item.project_uid)) toggleVisible(item.project_uid);
		if (marked?.uid !== item.project_uid) mark(item.project_uid);
		openFocus(node || undefined);
	};
	// No node arises silently: the node is created on request, and if hanging the item on it fails, the node stays.
	const create = () => {
		const parent = parentForNewNode(current, item.project_uid);
		setError(undefined);
		setCreating(true);
		createNode({ project: item.project_uid, title: item.title, ...(parent ? { parent } : {}) })
			.unwrap()
			.then((created) => assignItem({ node: created.uid, item: item.uid, replace: true }).unwrap())
			.catch(fail)
			.finally(() => setCreating(false));
	};
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
			<Stack direction="row" spacing={1} sx={{ mt: 1 }}>
				<Button size="small" variant="outlined" onClick={() => open(current)} data-testid={mindmapTestIds.itemNodeGoto}>
					{t("itemNode.goto")}
				</Button>
				<Button size="small" variant="outlined" disabled={creating} onClick={create} data-testid={mindmapTestIds.itemNodeCreate}>
					{t("itemNode.create")}
				</Button>
				{where?.explicit && current !== "" && (
					<Button size="small" variant="outlined" onClick={() => open(current)} data-testid={mindmapTestIds.itemNodeAnchor}>
						{t("itemNode.anchor")}
					</Button>
				)}
			</Stack>
			<Typography variant="caption" color="text.secondary">
				{current === "" ? t("itemNode.unassigned") : where?.explicit ? "" : t("itemNode.inherited")}
			</Typography>
		</Box>
	);
}
