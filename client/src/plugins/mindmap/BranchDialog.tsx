import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, FormLabel, Radio, RadioGroup, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { errorMessage, toWriteError, useGetTreeQuery, useListMapsQuery, useMoveNodeToMapMutation, useTransferNodeToMapMutation, type MapOut } from "./api";
import { branchOf, targetReason, type BranchAction, type BranchSource } from "./domain/branches";
import { mapKey } from "./domain/maps";
import { mindmapTestIds } from "./testIds";

interface Props {
	/** The branch: the node with its sub-nodes in the tree `source.tree_uid`. */
	source: BranchSource;
	/** The action to start with; the drag onto the map list leaves the choice to the user, the menu entries fix it. */
	action?: BranchAction;
	/** A target map chosen beforehand (its key), e.g. the entry of the map list a node was dropped on. */
	target?: string;
	onClose: () => void;
}

/**
 * The dialog "Umhängen nach …" / "Übertragen nach …": the maps of the node's project as targets, an action to choose
 * (hang over: the branch leaves its tree; transfer: it also stays), and the reason why a map is no target (the branch or
 * a part of it already stands there; a transfer into the own tree). The branch lands below the root of the target map.
 * The server refuses the same cases, so a stale list cannot do harm; its message is shown in the dialog.
 */
export function BranchDialog({ source, action: preset, target: presetTarget, onClose }: Props) {
	const { t } = useTranslation("mindmap");
	const { data: maps } = useListMapsQuery(source.project_uid);
	const [moveToMap] = useMoveNodeToMapMutation();
	const [transferToMap] = useTransferNodeToMapMutation();
	const [action, setAction] = useState<BranchAction>(preset ?? "move");
	const [chosen, setChosen] = useState<string | undefined>(presetTarget);
	const [error, setError] = useState<string>();
	const [busy, setBusy] = useState(false);
	const sourceMap = maps?.find((map) => map.tree_uid === source.tree_uid);
	const { data: sourceTree } = useGetTreeQuery(
		{ project: source.project_uid, statuses: "", ...(sourceMap?.kind === "free" ? { tree: sourceMap.tree_uid! } : {}) },
		{ skip: !sourceMap },
	);
	const sourceNodes = sourceTree?.nodes;
	const branch = sourceNodes ? branchOf(sourceNodes, source.uid) : [source.uid];

	const submit = async () => {
		const map = maps?.find((entry) => mapKey(entry) === chosen);
		if (!map) return;
		setError(undefined);
		setBusy(true);
		const write = action === "move" ? moveToMap : transferToMap;
		try {
			await write({ ref: source.uid, version: source.version, target: map.tree_uid ?? map.project_uid, tree: source.tree_uid }).unwrap();
			onClose();
		} catch (failure) {
			const failed = toWriteError(failure);
			const titles = Array.isArray(failed.details.nodes)
				? (failed.details.nodes as string[]).map((uid) => sourceNodes?.find((node) => node.uid === uid)?.title ?? uid)
				: [];
			setError(titles.length > 0 ? `${errorMessage(failure, t("error.failed"))}: ${titles.join(", ")}` : errorMessage(failure, t("error.failed")));
		} finally {
			setBusy(false);
		}
	};
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="xs" data-testid={mindmapTestIds.branchDialog}>
			<DialogTitle>{t("branch.title", { title: source.title })}</DialogTitle>
			<DialogContent>
				<FormLabel id="branch-action">{t("branch.action")}</FormLabel>
				<RadioGroup row aria-labelledby="branch-action" value={action} onChange={(event) => setAction(event.target.value as BranchAction)}>
					<FormControlLabel value="move" control={<Radio size="small" slotProps={{ input: { "data-testid": mindmapTestIds.branchAction("move") } as never }} />} label={t("branch.move")} />
					<FormControlLabel value="transfer" control={<Radio size="small" slotProps={{ input: { "data-testid": mindmapTestIds.branchAction("transfer") } as never }} />} label={t("branch.transfer")} />
				</RadioGroup>
				<Typography variant="caption" color="text.secondary" component="p" sx={{ mb: 1 }}>
					{t(action === "move" ? "branch.moveHint" : "branch.transferHint")}
				</Typography>
				<FormLabel id="branch-target">{t("branch.target")}</FormLabel>
				<RadioGroup aria-labelledby="branch-target" value={chosen ?? ""} onChange={(event) => setChosen(event.target.value)}>
					{(maps ?? []).map((map) => (
						<TargetRow key={mapKey(map)} map={map} action={action} source={source} branch={branch} />
					))}
				</RadioGroup>
				{error && (
					<Alert severity="error" sx={{ mt: 1 }} data-testid={mindmapTestIds.branchError}>
						{error}
					</Alert>
				)}
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{t("form.cancel")}</Button>
				<Button variant="contained" disabled={!chosen || busy} onClick={() => void submit()} data-testid={mindmapTestIds.branchConfirm}>
					{t(action === "move" ? "branch.moveConfirm" : "branch.transferConfirm")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}

/** One map as a target; it reads its own tree to know whether the branch (or a part of it) already stands there. */
function TargetRow({ map, action, source, branch }: { map: MapOut; action: BranchAction; source: BranchSource; branch: readonly string[] }) {
	const { t } = useTranslation("mindmap");
	const { data: tree } = useGetTreeQuery(
		{ project: source.project_uid, statuses: "", ...(map.kind === "free" ? { tree: map.tree_uid! } : {}) },
		{ skip: map.tree_uid === null || map.tree_uid === source.tree_uid },
	);
	const key = mapKey(map);
	const reason = targetReason(action, source.tree_uid, branch, map, map.tree_uid === null ? [] : tree?.nodes);
	const label = map.kind === "project" ? t("maps.projectTree", { name: map.name }) : map.name;
	return (
		<Box>
			<FormControlLabel
				value={key}
				disabled={reason !== undefined}
				control={<Radio size="small" slotProps={{ input: { "data-testid": mindmapTestIds.branchTarget(key) } as never }} />}
				label={label}
			/>
			{reason && (
				<Typography variant="caption" color="text.secondary" component="p" sx={{ ml: 4, mt: -0.5 }} data-testid={mindmapTestIds.branchReason(key)}>
					{reason.kind === "sameTree" ? t("branch.sameTree") : t("branch.standing", { nodes: reason.nodes.join(", ") })}
				</Typography>
			)}
		</Box>
	);
}
