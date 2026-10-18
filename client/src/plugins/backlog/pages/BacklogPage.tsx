import { Alert, Box, Button, Checkbox, FormControlLabel, LinearProgress, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { usePageDetail } from "../../../core";
import { buildTree, TreeView } from "../../../shared";
import { useProjectSelection, useSearchText } from "../../workspace";
import { useListItemsQuery } from "../api";
import { ItemDetail } from "../ItemDetail";
import { collapsibleIds, filterItems, groupByProject, placementOf, projectProgress, toFlatNodes } from "../model";
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
	usePageDetail(state.selected && <ItemDetail uid={state.selected} onSelect={state.setSelected} onClose={() => state.setSelected(null)} />);

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
				{groups.map(({ project, items: projectItems }) => {
					const progress = projectProgress(items.filter((item) => item.project_uid === project.uid));
					return (
						<Box key={project.uid} component="section" sx={{ mb: 2 }} data-testid={backlogTestIds.project(project.uid)}>
							<Typography variant="subtitle2" data-testid={backlogTestIds.projectProgress(project.uid)}>
								{`${project.name} (${progress.done}/${progress.total})`}
							</Typography>
							<LinearProgress variant="determinate" value={progress.total ? (progress.done / progress.total) * 100 : 0} sx={{ mb: 0.5 }} />
							<TreeView
								ariaLabel={project.name}
								canDrop={(source, target, position) => placementOf(items, source.id, target.id, position) !== null}
								onDrop={({ sourceId, targetId, position }) => {
									const placement = placementOf(items, sourceId, targetId, position);
									const source = items.find((item) => item.uid === sourceId);
									if (!placement || !source) return;
									setError(undefined);
									write.moveItem(source, placement.parent, placement.position).catch((failure: Error) => setError(failure.message));
								}}
								nodes={buildTree(toFlatNodes(projectItems, state.extendedMarking))}
								expanded={new Set(projectItems.filter((item) => state.expanded(item.uid)).map((item) => item.uid))}
								onToggle={state.toggleCollapsed}
								selectedId={state.selected}
								onSelect={state.setSelected}
							/>
						</Box>
					);
				})}
			</Box>
			{write.dialog}
		</Box>
	);
}
