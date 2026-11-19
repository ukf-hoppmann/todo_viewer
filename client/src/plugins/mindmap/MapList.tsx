import AddIcon from "@mui/icons-material/Add";
import MoreVertIcon from "@mui/icons-material/MoreVert";
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, List, ListItemButton, ListItemText, Menu, MenuItem, TextField, Typography } from "@mui/material";
import { useState, type DragEvent, type FormEvent, type MouseEvent } from "react";
import { useTranslation } from "react-i18next";
import { ConfirmDialog } from "../../shared";
import { useProjectSelection } from "../workspace";
import { errorMessage, useCreateMapMutation, useDeleteMapMutation, useListMapsQuery, useRenameMapMutation, type MapOut } from "./api";
import { BranchDialog } from "./BranchDialog";
import { NODE_MIME, type BranchSource } from "./domain/branches";
import { chooseMap, deleteQuestion, mapKey } from "./domain/maps";
import { shownProject } from "./domain/tree";
import { useMindmapState } from "./state";
import { mindmapTestIds } from "./testIds";

type Naming = { kind: "new" } | { kind: "rename"; map: MapOut };

/**
 * Sidebar section "Maps in <project>": the project tree first, then the free maps, each with its node count. A click
 * chooses the map the page shows (kept per project in the UI state). "+ Neue Map" creates a free map; the menu of a
 * free map (button or right click) renames it or puts it into the trash. The project tree has no menu: it cannot be
 * renamed or deleted. Only the single view has maps to choose from; the overall view shows project trees only.
 */
export function MapList() {
	const { t } = useTranslation("mindmap");
	const { visible, marked } = useProjectSelection();
	const { view, chosenMaps, chooseMapOf } = useMindmapState();
	const project = shownProject(visible, marked);
	const { data: maps } = useListMapsQuery(project?.uid ?? "", { skip: !project || view === "all" });
	const [createMap] = useCreateMapMutation();
	const [renameMap] = useRenameMapMutation();
	const [deleteMap] = useDeleteMapMutation();
	const [menu, setMenu] = useState<{ map: MapOut; anchor: HTMLElement | { top: number; left: number } }>();
	const [naming, setNaming] = useState<Naming>();
	const [name, setName] = useState("");
	const [nameError, setNameError] = useState<string>();
	const [deleting, setDeleting] = useState<MapOut>();
	const [error, setError] = useState<string>();
	// A node dragged onto an entry: the dialog then asks whether to hang it over or transfer it. `over` is the entry the drag is above.
	const [over, setOver] = useState<string>();
	const [dropped, setDropped] = useState<{ source: BranchSource; target: string }>();
	if (!project || view === "all") return null;

	const current = chooseMap(maps, chosenMaps[project.uid]);
	const openMenu = (map: MapOut, anchor: HTMLElement | { top: number; left: number }) => setMenu({ map, anchor });
	const startNaming = (next: Naming) => {
		setNaming(next);
		setName(next.kind === "rename" ? next.map.name : "");
		setNameError(undefined);
	};
	const submit = async (event: FormEvent) => {
		event.preventDefault();
		if (!naming) return;
		const wanted = name.trim();
		if (wanted === "") return setNameError(t("maps.nameEmpty"));
		const result =
			naming.kind === "new"
				? await createMap({ project: project.uid, name: wanted })
				: await renameMap({ tree: naming.map.tree_uid!, version: naming.map.version, name: wanted });
		if ("error" in result) return setNameError(errorMessage(result.error, t("error.failed")));
		if (naming.kind === "new" && result.data.tree_uid) chooseMapOf(project.uid, result.data.tree_uid);
		setNaming(undefined);
	};
	const confirmDelete = async () => {
		const map = deleting;
		setDeleting(undefined);
		if (!map?.tree_uid) return;
		setError(undefined);
		const result = await deleteMap({ tree: map.tree_uid, version: map.version });
		if ("error" in result) setError(errorMessage(result.error, t("error.failed")));
		else if (chosenMaps[project.uid] === map.tree_uid) chooseMapOf(project.uid, null);
	};
	const question = deleting ? deleteQuestion(deleting) : { going: 0, kept: 0 };

	return (
		<Box data-testid={mindmapTestIds.mapList} component="section" aria-label={t("maps.title", { project: project.name })}>
			<Typography variant="overline" color="text.secondary" component="h3">
				{t("maps.title", { project: project.name })}
			</Typography>
			{error && (
				<Alert severity="error" onClose={() => setError(undefined)} data-testid={mindmapTestIds.mapError}>
					{error}
				</Alert>
			)}
			<List dense disablePadding>
				{(maps ?? []).map((map) => {
					const key = mapKey(map);
					const free = map.kind === "free";
					return (
						<ListItemButton
							key={key}
							selected={current !== undefined && mapKey(current) === key}
							onClick={() => chooseMapOf(project.uid, free ? map.tree_uid : null)}
							onContextMenu={free ? (event: MouseEvent<HTMLElement>) => {
								event.preventDefault();
								openMenu(map, { top: event.clientY, left: event.clientX });
							} : undefined}
							data-testid={mindmapTestIds.mapEntry(key)}
							data-drop={over === key ? "over" : undefined}
							onDragOver={(event: DragEvent<HTMLElement>) => {
								if (!event.dataTransfer.types.includes(NODE_MIME)) return;
								event.preventDefault();
								event.dataTransfer.dropEffect = "move";
								setOver(key);
							}}
							onDragLeave={() => setOver((current) => (current === key ? undefined : current))}
							onDrop={(event: DragEvent<HTMLElement>) => {
								setOver(undefined);
								const carried = event.dataTransfer.getData(NODE_MIME);
								if (!carried) return;
								event.preventDefault();
								setDropped({ source: JSON.parse(carried) as BranchSource, target: key });
							}}
							sx={{ pr: 0.5, ...(over === key ? { outline: "2px dashed", outlineColor: "primary.main" } : {}) }}
						>
							<ListItemText primary={map.kind === "project" ? t("maps.projectTree", { name: map.name }) : map.name} slotProps={{ primary: { noWrap: true } }} />
							<Typography variant="caption" color="text.secondary" data-testid={mindmapTestIds.mapCount(key)} aria-label={t("maps.nodes", { count: map.node_count })}>
								{map.node_count}
							</Typography>
							{free ? (
								<IconButton
									size="small"
									aria-label={t("maps.menu", { name: map.name })}
									onClick={(event) => {
										event.stopPropagation();
										openMenu(map, event.currentTarget);
									}}
									data-testid={mindmapTestIds.mapMenuButton(key)}
								>
									<MoreVertIcon fontSize="small" />
								</IconButton>
							) : (
								<Box sx={{ width: 30 }} />
							)}
						</ListItemButton>
					);
				})}
			</List>
			<Button size="small" startIcon={<AddIcon />} onClick={() => startNaming({ kind: "new" })} data-testid={mindmapTestIds.mapNew}>
				{t("maps.new")}
			</Button>
			<Menu
				open={menu !== undefined}
				onClose={() => setMenu(undefined)}
				anchorEl={menu && menu.anchor instanceof HTMLElement ? menu.anchor : undefined}
				anchorReference={menu && !(menu.anchor instanceof HTMLElement) ? "anchorPosition" : "anchorEl"}
				anchorPosition={menu && !(menu.anchor instanceof HTMLElement) ? menu.anchor : undefined}
			>
				<MenuItem
					onClick={() => {
						if (menu) startNaming({ kind: "rename", map: menu.map });
						setMenu(undefined);
					}}
					data-testid={menu ? mindmapTestIds.mapRename(mapKey(menu.map)) : undefined}
				>
					{t("maps.rename")}
				</MenuItem>
				<MenuItem
					onClick={() => {
						setDeleting(menu?.map);
						setMenu(undefined);
					}}
					data-testid={menu ? mindmapTestIds.mapDelete(mapKey(menu.map)) : undefined}
				>
					{t("maps.delete")}
				</MenuItem>
			</Menu>
			<Dialog open={naming !== undefined} onClose={() => setNaming(undefined)} fullWidth maxWidth="xs">
				<form onSubmit={(event) => void submit(event)}>
					<DialogTitle>{t(naming?.kind === "rename" ? "maps.renameTitle" : "maps.newTitle")}</DialogTitle>
					<DialogContent>
						<TextField
							autoFocus
							fullWidth
							margin="dense"
							label={t("maps.name")}
							value={name}
							onChange={(event) => setName(event.target.value)}
							slotProps={{ htmlInput: { "data-testid": mindmapTestIds.mapNameInput, maxLength: 100 } }}
						/>
						{nameError && (
							<Alert severity="error" sx={{ mt: 1 }} data-testid={mindmapTestIds.mapNameError}>
								{nameError}
							</Alert>
						)}
					</DialogContent>
					<DialogActions>
						<Button onClick={() => setNaming(undefined)}>{t("form.cancel")}</Button>
						<Button type="submit" variant="contained">
							{t("form.save")}
						</Button>
					</DialogActions>
				</form>
			</Dialog>
			{dropped && <BranchDialog source={dropped.source} target={dropped.target} onClose={() => setDropped(undefined)} />}
			<ConfirmDialog
				open={deleting !== undefined}
				title={t("maps.deleteTitle", { name: deleting?.name ?? "" })}
				message={
					<>
						{t("maps.deleteMessage", { count: question.going })}
						{question.kept > 0 && <> {t("maps.deleteKept", { count: question.kept })}</>}
					</>
				}
				confirmLabel={t("maps.deleteConfirm")}
				cancelLabel={t("form.cancel")}
				onCancel={() => setDeleting(undefined)}
				onConfirm={() => void confirmDelete()}
			/>
		</Box>
	);
}
