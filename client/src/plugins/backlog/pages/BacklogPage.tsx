import { Alert, Box, Button, Checkbox, FormControlLabel, LinearProgress, Typography } from "@mui/material";
import { useCallback, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { usePageDetail } from "../../../core";
import { ancestorChain, buildTree, TreeView, type DropPosition, type TreeDrop, type TreeNode } from "../../../shared";
import { useProjectSelection, useSearchText } from "../../workspace";
import { useListItemsQuery, type IndexItem } from "../api";
import { ItemDetail } from "../ItemDetail";
import { collapsibleIds, filterItems, groupByProject, placementOf, projectProgress, toFlatNodes, type Placement } from "../model";
import { NotesPeek } from "../NotesPeek";
import { useBacklogState } from "../state";
import { backlogTestIds } from "../testIds";
import { useItemWrite } from "../useItemWrite";

/**
 * The backlog: per project the tree Epic → Story → Task with the progress of every item, filtered by status,
 * priority (sidebar) and the search text, and the detail panel of the selected item in the detail column. The projects
 * shown are those switched on in the sidebar; a marked project limits the folding buttons to itself.
 */
export default function BacklogPage() {
	const { t } = useTranslation("backlog");
	const { visible, marked } = useProjectSelection();
	const [search] = useSearchText();
	const state = useBacklogState();
	const write = useItemWrite();
	const [error, setError] = useState<string>();
	const projectUids = useMemo(() => visible.map((project) => project.uid), [visible]);
	const { data: items = [] } = useListItemsQuery(projectUids, { skip: projectUids.length === 0 });

	const shown = useMemo(
		() => filterItems(items, { hiddenStatuses: new Set(state.hiddenStatuses), hiddenPriorities: new Set(state.hiddenPriorities), search }),
		[items, state.hiddenStatuses, state.hiddenPriorities, search],
	);
	const groups = useMemo(() => groupByProject(visible, shown), [visible, shown]);
	const scope = useMemo(() => new Set(marked ? [marked.uid] : []), [marked]);
	// A chosen row keeps its place when the filter ends: its closed ancestors (also those filtered out now) are opened.
	// `select` keeps its identity while the items stay the same, so choosing a row does not redraw the other rows.
	const parentUids = useMemo(() => new Map(items.map((item) => [item.uid, item.parent_uid])), [items]);
	const { expand, setSelected } = state;
	const select = useCallback(
		(uid: string) => {
			expand(ancestorChain((id) => parentUids.get(id), uid));
			setSelected(uid);
		},
		[parentUids, expand, setSelected],
	);
	usePageDetail(state.selected && <ItemDetail uid={state.selected} onSelect={select} onClose={() => state.setSelected(null)} />);

	return (
		<Box sx={{ p: 2 }} data-testid={backlogTestIds.page}>
			<Box>
				<Box sx={{ display: "flex", gap: 1, mb: 1, flexWrap: "wrap", alignItems: "center" }}>
					{(["Epic", "Story"] as const).map((type) => {
						const ids = collapsibleIds(items, type, scope);
						const allCollapsed = ids.length > 0 && ids.every((id) => state.collapsed.includes(id));
						return (
							<Button
								key={type}
								size="small"
								disabled={ids.length === 0}
								title={marked ? t("collapse.scope", { project: marked.name }) : t("collapse.scopeAll")}
								onClick={() => state.setAllCollapsed(ids, !allCollapsed)}
								data-testid={backlogTestIds.collapse(type)}
							>
								{t(allCollapsed ? `collapse.expand${type}` : `collapse.collapse${type}`)}
							</Button>
						);
					})}
					<FormControlLabel
						control={<Checkbox size="small" checked={state.extendedMarking} onChange={(event) => state.setExtendedMarking(event.target.checked)} slotProps={{ input: { "data-testid": backlogTestIds.marking } as never }} />}
						label={t("marking")}
					/>
				</Box>
				{error && (
					<Alert severity="error" onClose={() => setError(undefined)} data-testid={backlogTestIds.error} sx={{ mb: 1 }}>
						{error}
					</Alert>
				)}
				{groups.length === 0 && (
					<Typography color="text.secondary" data-testid={backlogTestIds.empty}>
						{t("empty")}
					</Typography>
				)}
				{groups.map(({ project, items: projectItems }) => (
					<ProjectTree
						key={project.uid}
						project={project}
						projectItems={projectItems}
						items={items}
						extendedMarking={state.extendedMarking}
						expandedOf={state.expanded}
						selected={state.selected}
						onSelect={select}
						onToggle={state.toggleCollapsed}
						onMove={(source, placement) => {
							setError(undefined);
							write.moveItem(source, placement.parent, placement.position).catch((failure: Error) => setError(failure.message));
						}}
					/>
				))}
			</Box>
			{write.dialog}
		</Box>
	);
}

interface ProjectTreeProps {
	project: { uid: string; name: string };
	/** The items of this project that pass the filters. */
	projectItems: readonly IndexItem[];
	/** All loaded items of all shown projects; moves and the progress are decided over these. */
	items: readonly IndexItem[];
	extendedMarking: boolean;
	expandedOf: (uid: string) => boolean;
	selected: string | null;
	onSelect: (uid: string) => void;
	onToggle: (uid: string) => void;
	onMove: (source: IndexItem, placement: Placement) => void;
}

/**
 * One project: its progress and its tree. Everything handed to `TreeView` is memoized, so choosing a row draws only
 * the two rows that change (see `TreeView`), not the whole tree.
 */
function ProjectTree({ project, projectItems, items, extendedMarking, expandedOf, selected, onSelect, onToggle, onMove }: ProjectTreeProps) {
	const progress = useMemo(() => projectProgress(items.filter((item) => item.project_uid === project.uid)), [items, project.uid]);
	const nodes = useMemo(() => buildTree(toFlatNodes(projectItems, extendedMarking)), [projectItems, extendedMarking]);
	const expanded = useMemo(() => new Set(projectItems.filter((item) => expandedOf(item.uid)).map((item) => item.uid)), [projectItems, expandedOf]);
	const notesStates = useMemo(() => new Map(projectItems.map((item) => [item.uid, item.notes_state])), [projectItems]);
	const trailing = useCallback(
		(node: TreeNode) => {
			const notesState = notesStates.get(node.id);
			return notesState ? <NotesPeek uid={node.id} state={notesState} /> : null;
		},
		[notesStates],
	);
	const canDrop = useCallback(
		(source: TreeNode, target: TreeNode, position: DropPosition) => placementOf(items, source.id, target.id, position) !== null,
		[items],
	);
	const onDrop = useCallback(
		({ sourceId, targetId, position }: TreeDrop) => {
			const placement = placementOf(items, sourceId, targetId, position);
			const source = items.find((item) => item.uid === sourceId);
			if (placement && source) onMove(source, placement);
		},
		[items, onMove],
	);
	return (
		<Box component="section" sx={{ mb: 2 }} data-testid={backlogTestIds.project(project.uid)}>
			<Typography variant="subtitle2" data-testid={backlogTestIds.projectProgress(project.uid)}>
				{`${project.name} (${progress.done}/${progress.total})`}
			</Typography>
			<LinearProgress variant="determinate" value={progress.total ? (progress.done / progress.total) * 100 : 0} sx={{ mb: 0.5 }} />
			<TreeView
				ariaLabel={project.name}
				canDrop={canDrop}
				onDrop={onDrop}
				nodes={nodes}
				expanded={expanded}
				onToggle={onToggle}
				selectedId={selected}
				onSelect={onSelect}
				trailing={trailing}
			/>
		</Box>
	);
}
