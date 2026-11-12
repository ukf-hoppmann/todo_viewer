import ArchiveIcon from "@mui/icons-material/Archive";
import CreateNewFolderIcon from "@mui/icons-material/CreateNewFolder";
import DeleteIcon from "@mui/icons-material/Delete";
import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import EditIcon from "@mui/icons-material/Edit";
import MemoAddIcon from "@mui/icons-material/NoteAdd";
import UnarchiveIcon from "@mui/icons-material/Unarchive";
import { Alert, Box, Button, Checkbox, Dialog, DialogContent, DialogTitle, FormControlLabel, IconButton, Tooltip, Typography } from "@mui/material";
import { useMemo, useState, type DragEvent } from "react";
import { useTranslation } from "react-i18next";
import { usePageDetail } from "../../../core";
import { ancestorChain, buildTree, IconAction, TreeView, type TreeNode } from "../../../shared";
import { useProjectSelection, useSearchText } from "../../workspace";
import { useListIndexQuery, type IndexedMemo, type IndexedTopic } from "../api";
import { MemoDetail } from "../MemoDetail";
import { MemoForm } from "../MemoForm";
import { collapsibleIds, dropChange, filterMemos, filterTopics, groupByProject, toFlatNodes, type DropChange } from "../model";
import { useMemosState } from "../state";
import { memosTestIds } from "../testIds";
import { MoveDialog, TopicChoiceDialog, TopicFormDialog } from "../TopicDialogs";
import { useMemoWrite } from "../useMemoWrite";

type DialogState =
	| { kind: "memo"; projectUid: string; topicUid: string | null }
	| { kind: "topic"; projectUid: string; topic?: IndexedTopic; parentUid?: string | null }
	| { kind: "move"; topic?: IndexedTopic; memo?: IndexedMemo }
	| { kind: "choice"; topic: IndexedTopic; mode: "delete" | "archive" };

/**
 * The memos: per project the tree Topic → Sub-topic → Memo with the open memos counted at every topic, due memos
 * first, filtered by status (sidebar) and the search text, and the detail of the selected memo in the detail column.
 * Memos and topics are moved by drag and drop (onto a topic, next to a node, or onto the project's name for
 * "no topic"); the actions of a topic show while the pointer is over its row.
 */
export default function MemosPage() {
	const { t } = useTranslation("memos");
	const { visible } = useProjectSelection();
	const [search] = useSearchText();
	const state = useMemosState();
	const write = useMemoWrite();
	const [error, setError] = useState<string>();
	const [dialog, setDialog] = useState<DialogState>();
	const projectUids = useMemo(() => visible.map((project) => project.uid), [visible]);
	const { data: index } = useListIndexQuery(projectUids, { skip: projectUids.length === 0 });
	const allTopics = useMemo(() => index?.topics ?? [], [index]);
	const allMemos = useMemo(() => index?.memos ?? [], [index]);

	const filters = useMemo(
		() => ({ shownStatuses: new Set(state.shownStatuses), search, showArchivedTopics: state.showArchivedTopics }),
		[state.shownStatuses, search, state.showArchivedTopics],
	);
	const shownMemos = useMemo(() => filterMemos(allMemos, allTopics, filters), [allMemos, allTopics, filters]);
	const shownTopics = useMemo(() => filterTopics(allTopics, shownMemos, filters), [allTopics, shownMemos, filters]);
	const groups = useMemo(() => groupByProject(visible, shownTopics, shownMemos), [visible, shownTopics, shownMemos]);
	const folding = useMemo(() => collapsibleIds(shownTopics, shownMemos), [shownTopics, shownMemos]);
	const allCollapsed = folding.length > 0 && folding.every((id) => state.collapsed.includes(id));
	const searching = search.trim() !== "";

	const apply = (change: DropChange | null) => {
		if (!change) return;
		setError(undefined);
		const done = change.kind === "memo" ? write.updateMemo(change, { topic: change.topic }) : write.moveTopic(change, change.parent);
		done.catch((failure: Error) => setError(failure.message));
	};
	const dropOnProject = (event: DragEvent, projectUid: string) => {
		event.preventDefault();
		apply(dropChange(allTopics, allMemos, event.dataTransfer.getData("text/plain"), null, "inside", projectUid));
	};
	// A chosen row keeps its place when the search ends: its closed topics (also those filtered out now) are opened.
	const select = (uid: string) => {
		const parentUids = new Map<string, string | null | undefined>([...allTopics.map((topic) => [topic.uid, topic.parent_uid] as const), ...allMemos.map((memo) => [memo.uid, memo.topic_uid] as const)]);
		state.expand(ancestorChain((id) => parentUids.get(id), uid));
		state.setSelected(uid);
	};
	const selectedMemo = state.selected && allMemos.some((n) => n.uid === state.selected) ? state.selected : undefined;
	usePageDetail(
		selectedMemo && (
			<Box data-testid={memosTestIds.detail}>
				<MemoDetail uid={selectedMemo} onClose={() => state.setSelected(null)} />
			</Box>
		),
	);

	const topicActions = (node: TreeNode) => {
		const topic = allTopics.find((entry) => entry.uid === node.id);
		if (!topic) return null;
		const button = (action: string, label: string, icon: React.ReactNode, onClick: () => void) => (
			<Tooltip title={label} key={action}>
				<IconButton size="small" aria-label={label} onClick={onClick} data-testid={memosTestIds.topicAction(action, topic.uid)}>
					{icon}
				</IconButton>
			</Tooltip>
		);
		if (topic.archived) {
			return button("reactivate", t("topic.reactivate"), <UnarchiveIcon fontSize="small" />, () => {
				setError(undefined);
				write.reactivateTopic(topic).catch((failure: Error) => setError(failure.message));
			});
		}
		return (
			<>
				{button("memo", t("topic.newMemo"), <MemoAddIcon fontSize="small" />, () => setDialog({ kind: "memo", projectUid: topic.project_uid, topicUid: topic.uid }))}
				{button("subtopic", t("topic.newSubtopic"), <CreateNewFolderIcon fontSize="small" />, () => setDialog({ kind: "topic", projectUid: topic.project_uid, parentUid: topic.uid }))}
				{!topic.system && button("edit", t("topic.edit"), <EditIcon fontSize="small" />, () => setDialog({ kind: "topic", projectUid: topic.project_uid, topic }))}
				{!topic.system && button("move", t("topic.move"), <DriveFileMoveIcon fontSize="small" />, () => setDialog({ kind: "move", topic }))}
				{!topic.system && button("archive", t("topic.archive"), <ArchiveIcon fontSize="small" />, () => setDialog({ kind: "choice", topic, mode: "archive" }))}
				{!topic.system && button("delete", t("topic.delete"), <DeleteIcon fontSize="small" />, () => setDialog({ kind: "choice", topic, mode: "delete" }))}
			</>
		);
	};

	return (
		<Box sx={{ p: 2 }} data-testid={memosTestIds.page}>
			<Box>
				<Box sx={{ display: "flex", gap: 1, mb: 1, flexWrap: "wrap", alignItems: "center" }}>
					<Button size="small" disabled={folding.length === 0} onClick={() => state.setAllCollapsed(folding, !allCollapsed)} data-testid={memosTestIds.collapse}>
						{t(allCollapsed ? "collapse.expand" : "collapse.collapse")}
					</Button>
					<FormControlLabel
						control={<Checkbox size="small" checked={state.extendedMarking} onChange={(event) => state.setExtendedMarking(event.target.checked)} slotProps={{ input: { "data-testid": memosTestIds.marking } as never }} />}
						label={t("marking")}
					/>
				</Box>
				{error && (
					<Alert severity="error" onClose={() => setError(undefined)} data-testid={memosTestIds.error} sx={{ mb: 1 }}>
						{error}
					</Alert>
				)}
				{index && groups.every((group) => group.topics.length === 0 && group.memos.length === 0) && (
					<Typography color="text.secondary" data-testid={memosTestIds.empty}>
						{t("empty")}
					</Typography>
				)}
				{groups.map(({ project, topics, memos }) => {
					const nodes = buildTree(toFlatNodes(topics, memos, state.extendedMarking));
					const ids = [...topics.map((entry) => entry.uid), ...memos.map((entry) => entry.uid)];
					return (
						<Box key={project.uid} component="section" sx={{ mb: 2, pb: 1, borderBottom: 2, borderColor: "divider" }} data-testid={memosTestIds.project(project.uid)}>
							<Box
								sx={{ display: "flex", alignItems: "center", gap: 1 }}
								onDragOver={(event) => event.preventDefault()}
								onDrop={(event) => dropOnProject(event, project.uid)}
								data-testid={memosTestIds.projectDrop(project.uid)}
							>
								<Typography variant="subtitle2" sx={{ flexGrow: 1 }}>{`${project.name} (${memos.length})`}</Typography>
								<IconAction label={t("project.newMemo")} icon={MemoAddIcon} onClick={() => setDialog({ kind: "memo", projectUid: project.uid, topicUid: null })} testId={memosTestIds.newMemo(project.uid)} />
								<IconAction label={t("project.newTopic")} icon={CreateNewFolderIcon} onClick={() => setDialog({ kind: "topic", projectUid: project.uid })} testId={memosTestIds.newTopic(project.uid)} />
							</Box>
							<TreeView
								ariaLabel={project.name}
								nodes={nodes}
								expanded={new Set(searching ? ids : ids.filter((id) => state.expanded(id)))}
								onToggle={state.toggleCollapsed}
								selectedId={state.selected}
								onSelect={select}
								actions={topicActions}
								canDrop={(source, target, position) => dropChange(allTopics, allMemos, source.id, target.id, position) !== null}
								onDrop={({ sourceId, targetId, position }) => apply(dropChange(allTopics, allMemos, sourceId, targetId, position))}
							/>
						</Box>
					);
				})}
			</Box>
			{dialog?.kind === "memo" && (
				<Dialog open onClose={() => setDialog(undefined)} fullWidth maxWidth="md" slotProps={{ paper: { "data-testid": memosTestIds.formDialog } as never }}>
					<DialogTitle>{t("form.createTitle")}</DialogTitle>
					<DialogContent dividers>
						<MemoForm projectUid={dialog.projectUid} topicUid={dialog.topicUid} onDone={() => setDialog(undefined)} onCancel={() => setDialog(undefined)} />
					</DialogContent>
				</Dialog>
			)}
			{dialog?.kind === "topic" && <TopicFormDialog projectUid={dialog.projectUid} topic={dialog.topic} parentUid={dialog.parentUid} onClose={() => setDialog(undefined)} />}
			{dialog?.kind === "move" && dialog.topic && <MoveDialog moved={{ kind: "topic", topic: dialog.topic }} onClose={() => setDialog(undefined)} />}
			{dialog?.kind === "move" && dialog.memo && <MoveDialog moved={{ kind: "memo", memo: dialog.memo }} onClose={() => setDialog(undefined)} />}
			{dialog?.kind === "choice" && <TopicChoiceDialog topic={dialog.topic} mode={dialog.mode} onClose={() => setDialog(undefined)} />}
		</Box>
	);
}
