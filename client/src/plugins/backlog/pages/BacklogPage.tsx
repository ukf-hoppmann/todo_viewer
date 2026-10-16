import { Box, Button, LinearProgress, Typography } from "@mui/material";
import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { buildTree, TreeView } from "../../../shared";
import { useProjectSelection, useSearchText } from "../../workspace";
import { useListItemsQuery } from "../api";
import { ItemDetail } from "../ItemDetail";
import { collapsibleIds, filterItems, groupByProject, projectProgress, toFlatNodes } from "../model";
import { useBacklogState } from "../state";
import { backlogTestIds } from "../testIds";

/**
 * The backlog: per project the tree Epic → Story → Task with the progress of every item, filtered by status,
 * priority (sidebar) and the search text, and the detail panel of the selected item at the right. The projects
 * shown are those switched on in the sidebar; a marked project limits the folding buttons to itself.
 */
export default function BacklogPage() {
	const { t } = useTranslation("backlog");
	const { visible, marked } = useProjectSelection();
	const [search] = useSearchText();
	const state = useBacklogState();
	const projectUids = useMemo(() => visible.map((project) => project.uid), [visible]);
	const { data: items = [] } = useListItemsQuery(projectUids, { skip: projectUids.length === 0 });

	const shown = useMemo(
		() => filterItems(items, { hiddenStatuses: new Set(state.hiddenStatuses), hiddenPriorities: new Set(state.hiddenPriorities), search }),
		[items, state.hiddenStatuses, state.hiddenPriorities, search],
	);
	const groups = useMemo(() => groupByProject(visible, shown), [visible, shown]);
	const scope = useMemo(() => new Set(marked ? [marked.uid] : []), [marked]);

	return (
		<Box sx={{ display: "flex", gap: 2, p: 2, alignItems: "flex-start" }} data-testid={backlogTestIds.page}>
			<Box sx={{ flex: "1 1 50%", minWidth: 0 }}>
				<Box sx={{ display: "flex", gap: 1, mb: 1 }}>
					{(["Epic", "Story"] as const).map((type) => {
						const ids = collapsibleIds(items, type, scope);
						const allCollapsed = ids.length > 0 && ids.every((id) => state.collapsed.includes(id));
						return (
							<Button
								key={type}
								size="small"
								variant="outlined"
								disabled={ids.length === 0}
								title={marked ? t("collapse.scope", { project: marked.name }) : t("collapse.scopeAll")}
								onClick={() => state.setAllCollapsed(ids, !allCollapsed)}
								data-testid={backlogTestIds.collapse(type)}
							>
								{t(allCollapsed ? `collapse.expand${type}` : `collapse.collapse${type}`)}
							</Button>
						);
					})}
				</Box>
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
								nodes={buildTree(toFlatNodes(projectItems))}
								expanded={new Set(projectItems.filter((item) => state.expanded(item.uid)).map((item) => item.uid))}
								onToggle={state.toggleCollapsed}
								selectedId={state.selected}
								onSelect={state.setSelected}
							/>
						</Box>
					);
				})}
			</Box>
			<Box sx={{ flex: "1 1 50%", minWidth: 0 }}>
				{state.selected ? (
					<ItemDetail uid={state.selected} onSelect={state.setSelected} />
				) : (
					<Typography color="text.secondary" data-testid={backlogTestIds.detailEmpty}>
						{t("detail.choose")}
					</Typography>
				)}
			</Box>
		</Box>
	);
}
