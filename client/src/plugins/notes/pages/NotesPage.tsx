import ArchiveIcon from "@mui/icons-material/Archive";
import CreateNewFolderIcon from "@mui/icons-material/CreateNewFolder";
import DeleteIcon from "@mui/icons-material/Delete";
import DriveFileMoveIcon from "@mui/icons-material/DriveFileMove";
import EditIcon from "@mui/icons-material/Edit";
import FilterAltOffIcon from "@mui/icons-material/FilterAltOff";
import NoteAddIcon from "@mui/icons-material/NoteAdd";
import UnarchiveIcon from "@mui/icons-material/Unarchive";
import UnfoldLessIcon from "@mui/icons-material/UnfoldLess";
import UnfoldMoreIcon from "@mui/icons-material/UnfoldMore";
import { Alert, Box, Checkbox, Dialog, DialogContent, DialogTitle, FormControlLabel, IconButton, Tooltip, Typography } from "@mui/material";
import { useMemo, useState, type DragEvent } from "react";
import { useTranslation } from "react-i18next";
import { usePageDetail } from "../../../core";
import { buildTree, IconAction, TreeView, type TreeNode } from "../../../shared";
import { useProjectSelection, useSearchText } from "../../workspace";
import { useListIndexQuery, type IndexedNote, type IndexedTopic } from "../api";
import { NoteDetail } from "../NoteDetail";
import { NoteForm } from "../NoteForm";
import { collapsibleIds, dropChange, filterNotes, filterTopics, groupByProject, toFlatNodes, type DropChange } from "../model";
import { useNotesState } from "../state";
import { notesTestIds } from "../testIds";
import { MoveDialog, TopicChoiceDialog, TopicFormDialog } from "../TopicDialogs";
import { useNoteWrite } from "../useNoteWrite";

type DialogState =
	| { kind: "note"; projectUid: string; topicUid: string | null }
	| { kind: "topic"; projectUid: string; topic?: IndexedTopic; parentUid?: string | null }
	| { kind: "move"; topic?: IndexedTopic; note?: IndexedNote }
	| { kind: "choice"; topic: IndexedTopic; mode: "delete" | "archive" };

/**
 * The notes: per project the tree Topic → Sub-topic → Note with the open notes counted at every topic, due notes
 * first, filtered by status (sidebar) and the search text, and the detail of the selected note in the detail column.
 * Notes and topics are moved by drag and drop (onto a topic, next to a node, or onto the project's name for
 * "no topic"); the actions of a topic show while the pointer is over its row.
 */
export default function NotesPage() {
	const { t } = useTranslation("notes");
	const { visible } = useProjectSelection();
	const [search] = useSearchText();
	const state = useNotesState();
	const write = useNoteWrite();
	const [error, setError] = useState<string>();
	const [dialog, setDialog] = useState<DialogState>();
	const projectUids = useMemo(() => visible.map((project) => project.uid), [visible]);
	const { data: index } = useListIndexQuery(projectUids, { skip: projectUids.length === 0 });
	const allTopics = useMemo(() => index?.topics ?? [], [index]);
	const allNotes = useMemo(() => index?.notes ?? [], [index]);

	const filters = useMemo(
		() => ({ shownStatuses: new Set(state.shownStatuses), search, showArchivedTopics: state.showArchivedTopics }),
		[state.shownStatuses, search, state.showArchivedTopics],
	);
	const shownNotes = useMemo(() => filterNotes(allNotes, allTopics, filters), [allNotes, allTopics, filters]);
	const shownTopics = useMemo(() => filterTopics(allTopics, shownNotes, filters), [allTopics, shownNotes, filters]);
	const groups = useMemo(() => groupByProject(visible, shownTopics, shownNotes), [visible, shownTopics, shownNotes]);
	const folding = useMemo(() => collapsibleIds(shownTopics, shownNotes), [shownTopics, shownNotes]);
	const allCollapsed = folding.length > 0 && folding.every((id) => state.collapsed.includes(id));
	const searching = search.trim() !== "";

	const apply = (change: DropChange | null) => {
		if (!change) return;
		setError(undefined);
		const done = change.kind === "note" ? write.updateNote(change, { topic: change.topic }) : write.moveTopic(change, change.parent);
		done.catch((failure: Error) => setError(failure.message));
	};
	const dropOnProject = (event: DragEvent, projectUid: string) => {
		event.preventDefault();
		apply(dropChange(allTopics, allNotes, event.dataTransfer.getData("text/plain"), null, "inside", projectUid));
	};
	const selectedNote = state.selected && allNotes.some((n) => n.uid === state.selected) ? state.selected : undefined;
	usePageDetail(
		selectedNote && (
			<Box data-testid={notesTestIds.detail}>
				<NoteDetail uid={selectedNote} onClose={() => state.setSelected(null)} />
			</Box>
		),
	);

	const topicActions = (node: TreeNode) => {
		const topic = allTopics.find((entry) => entry.uid === node.id);
		if (!topic) return null;
		const button = (action: string, label: string, icon: React.ReactNode, onClick: () => void) => (
			<Tooltip title={label} key={action}>
				<IconButton size="small" aria-label={label} onClick={onClick} data-testid={notesTestIds.topicAction(action, topic.uid)}>
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
				{button("note", t("topic.newNote"), <NoteAddIcon fontSize="small" />, () => setDialog({ kind: "note", projectUid: topic.project_uid, topicUid: topic.uid }))}
				{button("subtopic", t("topic.newSubtopic"), <CreateNewFolderIcon fontSize="small" />, () => setDialog({ kind: "topic", projectUid: topic.project_uid, parentUid: topic.uid }))}
				{!topic.system && button("edit", t("topic.edit"), <EditIcon fontSize="small" />, () => setDialog({ kind: "topic", projectUid: topic.project_uid, topic }))}
				{!topic.system && button("move", t("topic.move"), <DriveFileMoveIcon fontSize="small" />, () => setDialog({ kind: "move", topic }))}
				{!topic.system && button("archive", t("topic.archive"), <ArchiveIcon fontSize="small" />, () => setDialog({ kind: "choice", topic, mode: "archive" }))}
				{!topic.system && button("delete", t("topic.delete"), <DeleteIcon fontSize="small" />, () => setDialog({ kind: "choice", topic, mode: "delete" }))}
			</>
		);
	};

	return (
		<Box sx={{ p: 2 }} data-testid={notesTestIds.page}>
			<Box>
				<Box sx={{ display: "flex", gap: 1, mb: 1, flexWrap: "wrap", alignItems: "center" }}>
					<IconAction
						label={t(allCollapsed ? "collapse.expand" : "collapse.collapse")}
						icon={allCollapsed ? UnfoldMoreIcon : UnfoldLessIcon}
						disabled={folding.length === 0}
						onClick={() => state.setAllCollapsed(folding, !allCollapsed)}
						testId={notesTestIds.collapse}
					/>
					<FormControlLabel
						control={<Checkbox size="small" checked={state.extendedMarking} onChange={(event) => state.setExtendedMarking(event.target.checked)} slotProps={{ input: { "data-testid": notesTestIds.marking } as never }} />}
						label={t("marking")}
					/>
					<FormControlLabel
						control={<Checkbox size="small" checked={state.showArchivedTopics} onChange={(event) => state.setShowArchivedTopics(event.target.checked)} slotProps={{ input: { "data-testid": notesTestIds.archivedTopics } as never }} />}
						label={t("archivedTopics")}
					/>
					<IconAction label={t("resetFilters")} icon={FilterAltOffIcon} onClick={() => state.resetFilters()} testId={notesTestIds.resetFilters} />
				</Box>
				{error && (
					<Alert severity="error" onClose={() => setError(undefined)} data-testid={notesTestIds.error} sx={{ mb: 1 }}>
						{error}
					</Alert>
				)}
				{index && groups.every((group) => group.topics.length === 0 && group.notes.length === 0) && (
					<Typography color="text.secondary" data-testid={notesTestIds.empty}>
						{t("empty")}
					</Typography>
				)}
				{groups.map(({ project, topics, notes }) => {
					const nodes = buildTree(toFlatNodes(topics, notes, state.extendedMarking));
					const ids = [...topics.map((entry) => entry.uid), ...notes.map((entry) => entry.uid)];
					return (
						<Box key={project.uid} component="section" sx={{ mb: 2, pb: 1, borderBottom: 2, borderColor: "divider" }} data-testid={notesTestIds.project(project.uid)}>
							<Box
								sx={{ display: "flex", alignItems: "center", gap: 1 }}
								onDragOver={(event) => event.preventDefault()}
								onDrop={(event) => dropOnProject(event, project.uid)}
								data-testid={notesTestIds.projectDrop(project.uid)}
							>
								<Typography variant="subtitle2" sx={{ flexGrow: 1 }}>{`${project.name} (${notes.length})`}</Typography>
								<IconAction label={t("project.newNote")} icon={NoteAddIcon} onClick={() => setDialog({ kind: "note", projectUid: project.uid, topicUid: null })} testId={notesTestIds.newNote(project.uid)} />
								<IconAction label={t("project.newTopic")} icon={CreateNewFolderIcon} onClick={() => setDialog({ kind: "topic", projectUid: project.uid })} testId={notesTestIds.newTopic(project.uid)} />
							</Box>
							<TreeView
								ariaLabel={project.name}
								nodes={nodes}
								expanded={new Set(searching ? ids : ids.filter((id) => state.expanded(id)))}
								onToggle={state.toggleCollapsed}
								selectedId={state.selected}
								onSelect={state.setSelected}
								actions={topicActions}
								canDrop={(source, target, position) => dropChange(allTopics, allNotes, source.id, target.id, position) !== null}
								onDrop={({ sourceId, targetId, position }) => apply(dropChange(allTopics, allNotes, sourceId, targetId, position))}
							/>
						</Box>
					);
				})}
			</Box>
			{dialog?.kind === "note" && (
				<Dialog open onClose={() => setDialog(undefined)} fullWidth maxWidth="md" slotProps={{ paper: { "data-testid": notesTestIds.formDialog } as never }}>
					<DialogTitle>{t("form.createTitle")}</DialogTitle>
					<DialogContent dividers>
						<NoteForm projectUid={dialog.projectUid} topicUid={dialog.topicUid} onDone={() => setDialog(undefined)} onCancel={() => setDialog(undefined)} />
					</DialogContent>
				</Dialog>
			)}
			{dialog?.kind === "topic" && <TopicFormDialog projectUid={dialog.projectUid} topic={dialog.topic} parentUid={dialog.parentUid} onClose={() => setDialog(undefined)} />}
			{dialog?.kind === "move" && dialog.topic && <MoveDialog moved={{ kind: "topic", topic: dialog.topic }} onClose={() => setDialog(undefined)} />}
			{dialog?.kind === "move" && dialog.note && <MoveDialog moved={{ kind: "note", note: dialog.note }} onClose={() => setDialog(undefined)} />}
			{dialog?.kind === "choice" && <TopicChoiceDialog topic={dialog.topic} mode={dialog.mode} onClose={() => setDialog(undefined)} />}
		</Box>
	);
}
