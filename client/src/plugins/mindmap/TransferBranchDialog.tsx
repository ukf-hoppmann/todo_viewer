import { Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, TextField, Typography } from "@mui/material";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { EntityPicker } from "../../shared";
import { TYPES, useListItemsQuery } from "../backlog";
import { errorMessage, useGetTreeQuery, useListMapsQuery, usePreviewBranchTransferQuery, useTransferBranchMutation, type BranchTransferOut, type ProblemOut } from "./api";
import type { BranchSource } from "./domain/branches";
import { branchRows, buildEntries, emptyChoice, relationTargets, type ChoiceKind, type Choices, type NodeChoice } from "./domain/transferPlan";
import { mindmapTestIds } from "./testIds";

/** How long the plan rests before the server checks it again. */
export const PREVIEW_DELAY_MS = 250;

const field = (uid: string, name: string) => ({ htmlInput: { "data-testid": mindmapTestIds.transferField(uid, name) } });

/** The problems of one entry or of the plan, in words; the code is translated, the message of the server is the fallback. */
function Problems({ problems, testId }: { problems: readonly ProblemOut[]; testId: string }) {
	const { t } = useTranslation("mindmap");
	if (problems.length === 0) return null;
	return (
		<Box component="ul" sx={{ m: 0, pl: 2.5, color: "error.main" }} data-testid={testId}>
			{problems.map((problem, index) => (
				<li key={`${problem.code}-${index}`} data-code={problem.code}>
					<Typography variant="caption">{t(`transfer.problem.${problem.code}`, { defaultValue: problem.message })}</Typography>
				</li>
			))}
		</Box>
	);
}

function ResultLine({ outcome }: { outcome: BranchTransferOut["entries"][number] }) {
	const { t } = useTranslation("mindmap");
	const text =
		outcome.status === "created" && outcome.created
			? t("transfer.result.created", { label: outcome.created.label })
			: outcome.status === "failed"
				? t("transfer.result.failed", { message: typeof outcome.error?.message === "string" ? outcome.error.message : t("error.failed") })
				: t(`transfer.result.${outcome.status}`, { defaultValue: outcome.status });
	return (
		<Typography variant="caption" color={outcome.status === "failed" ? "error" : "text.secondary"} data-testid={mindmapTestIds.transferResult(outcome.node)} data-status={outcome.status}>
			{text}
		</Typography>
	);
}

/**
 * "Ast überführen": the branch below a node as a tree. For every node the person chooses nothing, an item (with type)
 * or a memo, edits title, goal and completion criteria, and for an item the relation: "Kind von" (a node of the plan or an
 * existing item), "hängt ab von" (several) or none. Nothing is preset from level or depth. The server checks the plan
 * live (`preview_branch_transfer`, after a short rest) and the problems stand at the node; "Überführen" is possible only
 * for a plan without problems. The result of the transfer stands at every node; the dialog stays open until it is closed.
 * The input lives in the state of the dialog only.
 */
export function TransferBranchDialog({ source, onClose }: { source: BranchSource; onClose: () => void }) {
	const { t } = useTranslation("mindmap");
	const { data: maps } = useListMapsQuery(source.project_uid);
	const sourceMap = maps?.find((map) => map.tree_uid === source.tree_uid);
	const { data: tree } = useGetTreeQuery(
		{ project: source.project_uid, statuses: "", ...(sourceMap?.kind === "free" ? { tree: sourceMap.tree_uid! } : {}) },
		{ skip: !sourceMap },
	);
	const { data: existing } = useListItemsQuery([source.project_uid]);
	const [transfer] = useTransferBranchMutation();
	const [choices, setChoices] = useState<Choices>({});
	const [result, setResult] = useState<BranchTransferOut>();
	const [error, setError] = useState<string>();
	const [busy, setBusy] = useState(false);

	const nodes = tree?.nodes;
	const rows = useMemo(() => branchRows(nodes ?? [], source.uid), [nodes, source.uid]);
	const branch = useMemo(() => rows.map((row) => row.node), [rows]);
	const entries = useMemo(() => buildEntries(branch, choices), [branch, choices]);
	const key = JSON.stringify(entries);
	const [settled, setSettled] = useState<{ key: string; entries: typeof entries }>({ key: "[]", entries: [] });
	useEffect(() => {
		const timer = setTimeout(() => setSettled({ key, entries }), PREVIEW_DELAY_MS);
		return () => clearTimeout(timer);
		// `entries` is the parsed form of `key`; only a changed plan restarts the rest.
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [key]);
	const treeArg = source.tree_uid ? { tree: source.tree_uid } : {};
	const { currentData: preview, isFetching, isError } = usePreviewBranchTransferQuery(
		{ root: source.uid, ...treeArg, entries: settled.entries },
		{ skip: settled.entries.length === 0 || result !== undefined },
	);
	const checked = settled.key === key && !isFetching && preview !== undefined;
	const problemsOf = (uid: string) => (checked ? (preview.entries.find((entry) => entry.node === uid)?.problems ?? []) : []);
	const canTransfer = entries.length > 0 && checked && preview.ok && !busy && result === undefined;

	const choiceOf = (uid: string): NodeChoice => choices[uid] ?? emptyChoice(branch.find((node) => node.uid === uid)!);
	const change = (uid: string, changes: Partial<NodeChoice>) => setChoices((current) => ({ ...current, [uid]: { ...choiceOf(uid), ...changes } }));

	const submit = async () => {
		setError(undefined);
		setBusy(true);
		try {
			setResult(await transfer({ root: source.uid, ...treeArg, entries }).unwrap());
		} catch (failure) {
			setError(errorMessage(failure, t("error.failed")));
		} finally {
			setBusy(false);
		}
	};
	const locked = result !== undefined || busy;
	const outcomeOf = (uid: string) => result?.entries.find((entry) => entry.node === uid);
	const existingTargets = useMemo(() => (existing ?? []).map((item) => ({ uid: item.uid, label: item.label, title: item.title })), [existing]);

	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="md" scroll="paper" data-testid={mindmapTestIds.transferDialog}>
			<DialogTitle>{t("transfer.title", { title: source.title })}</DialogTitle>
			<DialogContent dividers sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
				<Typography variant="body2" color="text.secondary">
					{t("transfer.hint")}
				</Typography>
				{checked && preview.problems.length > 0 && (
					<Alert severity="error" data-testid={mindmapTestIds.transferPlanProblems}>
						<Problems problems={preview.problems} testId={mindmapTestIds.transferPlanProblemList} />
					</Alert>
				)}
				{isError && !isFetching && (
					<Alert severity="warning" data-testid={mindmapTestIds.transferPreviewError}>
						{t("transfer.previewFailed")}
					</Alert>
				)}
				{rows.map(({ node, depth }) => {
					const choice = choiceOf(node.uid);
					const outcome = outcomeOf(node.uid);
					const problems = problemsOf(node.uid);
					const targets = relationTargets(branch, choices, node.uid, existingTargets);
					return (
						<Box
							key={node.uid}
							data-testid={mindmapTestIds.transferRow(node.uid)}
							sx={{ ml: depth * 3, pl: 1.5, borderLeft: 2, borderColor: problems.length > 0 ? "error.main" : "divider", display: "flex", flexDirection: "column", gap: 1 }}
						>
							<Box sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}>
								<Typography variant="body2" sx={{ fontWeight: 600 }}>
									{node.label} · {node.title}
								</Typography>
								<Chip size="small" variant="outlined" label={t(`state.${node.state}`, { defaultValue: node.state })} data-testid={mindmapTestIds.transferState(node.uid)} />
								<TextField
									select
									size="small"
									label={t("transfer.kind")}
									value={choice.kind}
									disabled={locked}
									onChange={(event) => change(node.uid, { kind: event.target.value as ChoiceKind })}
									sx={{ minWidth: 140, ml: "auto" }}
									slotProps={field(node.uid, "kind")}
								>
									<MenuItem value="skip">{t("transfer.kinds.skip")}</MenuItem>
									<MenuItem value="item">{t("transfer.kinds.item")}</MenuItem>
									<MenuItem value="memo">{t("transfer.kinds.memo")}</MenuItem>
								</TextField>
							</Box>
							{choice.kind === "item" && (
								<ItemFields uid={node.uid} choice={choice} locked={locked} change={change}>
									<Box data-testid={mindmapTestIds.transferParent(node.uid)}>
										<EntityPicker label={t("transfer.parent")} options={targets} value={choice.parent} onChange={(id) => change(node.uid, { parent: id })} noOptionsText={t("transfer.noTargets")} />
									</Box>
									<Box data-testid={mindmapTestIds.transferDepends(node.uid)}>
										<EntityPicker multiple label={t("transfer.dependsOn")} options={targets} value={choice.dependsOn} onChange={(ids) => change(node.uid, { dependsOn: ids })} noOptionsText={t("transfer.noTargets")} />
									</Box>
								</ItemFields>
							)}
							{choice.kind === "memo" && (
								<>
									<TextField size="small" label={t("create.memo.summary")} value={choice.title} disabled={locked} onChange={(event) => change(node.uid, { title: event.target.value })} slotProps={field(node.uid, "title")} />
									<TextField multiline minRows={2} size="small" label={t("create.memo.body")} value={choice.goal} disabled={locked} onChange={(event) => change(node.uid, { goal: event.target.value })} slotProps={field(node.uid, "goal")} />
								</>
							)}
							<Problems problems={problems} testId={mindmapTestIds.transferProblems(node.uid)} />
							{outcome && <ResultLine outcome={outcome} />}
						</Box>
					);
				})}
				{error && (
					<Alert severity="error" data-testid={mindmapTestIds.transferError}>
						{error}
					</Alert>
				)}
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose} data-testid={mindmapTestIds.transferClose}>
					{result ? t("transfer.close") : t("form.cancel")}
				</Button>
				<Button variant="contained" disabled={!canTransfer} onClick={() => void submit()} data-testid={mindmapTestIds.transferConfirm}>
					{t("transfer.confirm")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}

/** The fields of an item node: type, title, goal, completion criteria, and the relation pickers given as children. */
function ItemFields({ uid, choice, locked, change, children }: { uid: string; choice: NodeChoice; locked: boolean; change: (uid: string, changes: Partial<NodeChoice>) => void; children: ReactNode }) {
	const { t } = useTranslation("mindmap");
	return (
		<>
			<TextField select size="small" label={t("create.item.type")} value={choice.type} disabled={locked} onChange={(event) => change(uid, { type: event.target.value })} slotProps={field(uid, "type")}>
				{TYPES.map((value) => (
					<MenuItem key={value} value={value}>
						{t(`create.item.types.${value}`)}
					</MenuItem>
				))}
			</TextField>
			<TextField size="small" label={t("field.title")} value={choice.title} disabled={locked} onChange={(event) => change(uid, { title: event.target.value })} slotProps={field(uid, "title")} />
			<TextField multiline minRows={2} size="small" label={t("create.item.goal")} value={choice.goal} disabled={locked} onChange={(event) => change(uid, { goal: event.target.value })} slotProps={field(uid, "goal")} />
			<TextField multiline minRows={2} size="small" label={t("create.item.criteria")} value={choice.criteria} disabled={locked} onChange={(event) => change(uid, { criteria: event.target.value })} slotProps={field(uid, "completion_criteria")} />
			{children}
		</>
	);
}
