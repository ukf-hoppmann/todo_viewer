import CloseIcon from "@mui/icons-material/Close";
import { Alert, Box, Button, Stack, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { ConfirmDialog, EntityPicker, IconAction, type Entity } from "../../shared";
import { useShownStatuses } from "../backlog";
import { useSearchElementsQuery } from "../workspace";
import {
	errorMessage,
	toWriteError,
	useAssignItemMutation,
	useGetNodeContentQuery,
	useLinkMemoMutation,
	useUnassignItemMutation,
	useUnlinkMemoMutation,
	type NodeOut,
} from "./api";
import { mindmapTestIds } from "./testIds";

const ITEM_KINDS = ["epic", "story", "task"];
const ALREADY_ASSIGNED = "mindmap_item_assigned";

/** Finds elements of the project of the node by label and title; `kinds` limits what can be chosen. */
function useCandidates(projectUid: string, kinds: readonly string[]) {
	const [query, setQuery] = useState("");
	const { data: found = [] } = useSearchElementsQuery(query, { skip: query.trim() === "" });
	const options: Entity[] = found
		.filter((element) => element.project_uid === projectUid && !element.deleted && kinds.includes(element.kind))
		.map((element) => ({ id: element.uid, label: element.label, title: element.title }));
	return { options, setQuery, reset: () => setQuery("") };
}

/**
 * The section "Items und Memos" in the detail of a node: the items whose node it is (assigned to it or inherited from
 * their parent item; the status filter of the backlog decides which are listed) and the memos linked to it. An own
 * item can be released, an item or memo of the project can be added. A memo is not counted in the node's number.
 * An item that hangs on another node is moved only after a confirmation.
 */
export function NodeContentSection({ node }: { node: NodeOut }) {
	const { t } = useTranslation("mindmap");
	const statuses = useShownStatuses();
	const { data } = useGetNodeContentQuery({ node: node.uid, statuses });
	const [assignItem] = useAssignItemMutation();
	const [unassignItem] = useUnassignItemMutation();
	const [linkMemo] = useLinkMemoMutation();
	const [unlinkMemo] = useUnlinkMemoMutation();
	const itemSearch = useCandidates(node.project_uid, ITEM_KINDS);
	const memoSearch = useCandidates(node.project_uid, ["memo"]);
	const [item, setItem] = useState<string | null>(null);
	const [memo, setMemo] = useState<string | null>(null);
	const [replacing, setReplacing] = useState<Entity>();
	const [error, setError] = useState<string>();
	const fail = (failure: unknown) => setError(errorMessage(failure, t("error.failed")));

	const assign = (uid: string, replace: boolean) =>
		assignItem({ node: node.uid, item: uid, ...(replace ? { replace: true } : {}) })
			.unwrap()
			.then(() => {
				setItem(null);
				itemSearch.reset();
			})
			.catch((failure: unknown) => {
				const known = itemSearch.options.find((option) => option.id === uid);
				if (!replace && known && toWriteError(failure).code === ALREADY_ASSIGNED) setReplacing(known);
				else fail(failure);
			});

	return (
		<Stack spacing={1.5} data-testid={mindmapTestIds.content}>
			{error && (
				<Alert severity="error" onClose={() => setError(undefined)} data-testid={mindmapTestIds.contentError}>
					{error}
				</Alert>
			)}
			<Box>
				<Typography variant="overline" color="text.secondary">
					{t("content.items")}
				</Typography>
				{(data?.items.length ?? 0) === 0 && (
					<Typography variant="body2" color="text.secondary">
						{t("content.noItems")}
					</Typography>
				)}
				{data?.items.map((entry) => (
					<Stack key={entry.uid} direction="row" spacing={0.5} sx={{ alignItems: "center" }} data-testid={mindmapTestIds.contentItem(entry.uid)}>
						<Typography variant="body2" noWrap sx={{ flexGrow: 1, minWidth: 0 }} title={entry.title}>
							{entry.label} — {entry.title}
						</Typography>
						<Typography variant="caption" color="text.secondary">
							{entry.status}
							{entry.explicit ? "" : ` · ${t("content.inherited")}`}
						</Typography>
						{entry.explicit && (
							<IconAction label={t("content.unassign", { label: entry.label })} icon={CloseIcon} onClick={() => void unassignItem(entry.uid).unwrap().catch(fail)} testId={mindmapTestIds.unassign(entry.uid)} />
						)}
					</Stack>
				))}
				<Stack direction="row" spacing={1} sx={{ alignItems: "flex-start", mt: 1 }}>
					<Box sx={{ flexGrow: 1 }}>
						<EntityPicker label={t("content.assignItem")} options={itemSearch.options} noOptionsText={t("content.noMatch")} value={item} onChange={setItem} onInputChange={itemSearch.setQuery} />
					</Box>
					<Button size="small" variant="outlined" disabled={!item} onClick={() => item && void assign(item, false)} data-testid={mindmapTestIds.assignAdd}>
						{t("content.assign")}
					</Button>
				</Stack>
			</Box>
			<Box>
				<Typography variant="overline" color="text.secondary">
					{t("content.memos")}
				</Typography>
				{(data?.memos.length ?? 0) === 0 && (
					<Typography variant="body2" color="text.secondary">
						{t("content.noMemos")}
					</Typography>
				)}
				{data?.memos.map((entry) => (
					<Stack key={entry.uid} direction="row" spacing={0.5} sx={{ alignItems: "center" }} data-testid={mindmapTestIds.contentMemo(entry.uid)}>
						<Typography variant="body2" noWrap sx={{ flexGrow: 1, minWidth: 0 }} title={entry.title}>
							{entry.label} — {entry.title}
						</Typography>
						<IconAction label={t("content.unlink", { label: entry.label })} icon={CloseIcon} onClick={() => void unlinkMemo({ node: node.uid, memo: entry.uid }).unwrap().catch(fail)} testId={mindmapTestIds.unlink(entry.uid)} />
					</Stack>
				))}
				<Stack direction="row" spacing={1} sx={{ alignItems: "flex-start", mt: 1 }}>
					<Box sx={{ flexGrow: 1 }}>
						<EntityPicker label={t("content.linkMemo")} options={memoSearch.options} noOptionsText={t("content.noMatch")} value={memo} onChange={setMemo} onInputChange={memoSearch.setQuery} />
					</Box>
					<Button
						size="small"
						variant="outlined"
						disabled={!memo}
						onClick={() =>
							memo &&
							void linkMemo({ node: node.uid, memo })
								.unwrap()
								.then(() => {
									setMemo(null);
									memoSearch.reset();
								})
								.catch(fail)
						}
						data-testid={mindmapTestIds.memoAdd}
					>
						{t("content.link")}
					</Button>
				</Stack>
			</Box>
			<ConfirmDialog
				open={Boolean(replacing)}
				title={t("content.replaceTitle")}
				message={t("content.replaceMessage", { label: replacing?.label ?? "" })}
				confirmLabel={t("content.replace")}
				cancelLabel={t("content.cancel")}
				onConfirm={() => {
					const target = replacing;
					setReplacing(undefined);
					if (target) void assign(target.id, true);
				}}
				onCancel={() => setReplacing(undefined)}
			/>
		</Stack>
	);
}
