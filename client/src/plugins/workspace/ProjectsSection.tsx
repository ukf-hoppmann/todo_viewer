import AddIcon from "@mui/icons-material/Add";
import EditIcon from "@mui/icons-material/Edit";
import { Box, Checkbox, IconButton, Tooltip, Typography } from "@mui/material";
import { useState, type DragEvent } from "react";
import { useTranslation } from "react-i18next";
import { useMoveProjectMutation, type Project } from "./api";
import { ProjectCard } from "./ProjectCard";
import { SyncIndicator } from "./SyncIndicator";
import { useProjectSelection } from "./state";
import { workspaceTestIds } from "./testIds";

/**
 * The projects in the sidebar: the checkbox shows or hides a project, a click marks it, the pencil in the header (or a
 * double click on the name) opens the card of the marked project, and the order is changed by dragging. The sync
 * indicators of the mirror come with the sync UI.
 */
export function ProjectsSection() {
	const { t } = useTranslation("workspace");
	const { projects, visible, marked, toggleVisible, mark } = useProjectSelection();
	const [move] = useMoveProjectMutation();
	const [card, setCard] = useState<{ project?: Project }>();
	const [dragged, setDragged] = useState<string>();
	const [over, setOver] = useState<string>();

	const drop = (target: Project) => {
		const source = projects.find((project) => project.uid === dragged);
		setDragged(undefined);
		setOver(undefined);
		if (source && source.uid !== target.uid) void move({ uid: source.uid, version: source.version, position: target.position });
	};

	return (
		<Box>
			<Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
				<Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
					{t("projects.title")}
				</Typography>
				<Tooltip title={marked ? t("projects.editMarked") : t("projects.selectFirst")}>
					<span aria-label={marked ? undefined : t("projects.selectFirst")} data-testid={workspaceTestIds.projectEditHint}>
						<IconButton
							size="small"
							aria-label={t("projects.editMarked")}
							disabled={!marked}
							onClick={() => marked && setCard({ project: marked })}
							data-testid={workspaceTestIds.projectEditMarked}
						>
							<EditIcon fontSize="small" />
						</IconButton>
					</span>
				</Tooltip>
				<IconButton size="small" aria-label={t("projects.add")} onClick={() => setCard({})} data-testid={workspaceTestIds.projectAdd}>
					<AddIcon fontSize="small" />
				</IconButton>
			</Box>
			<Box component="ul" sx={{ listStyle: "none", p: 0, m: 0 }} data-testid={workspaceTestIds.projectList}>
				{projects.map((project) => (
					<Box
						component="li"
						key={project.uid}
						draggable
						onDragStart={(event: DragEvent) => {
							setDragged(project.uid);
							event.dataTransfer?.setData("text/plain", project.uid);
						}}
						onDragOver={(event: DragEvent) => {
							event.preventDefault();
							setOver(project.uid);
						}}
						onDrop={(event: DragEvent) => {
							event.preventDefault();
							drop(project);
						}}
						onDragEnd={() => {
							setDragged(undefined);
							setOver(undefined);
						}}
						data-testid={workspaceTestIds.project(project.uid)}
						data-marked={marked?.uid === project.uid}
						sx={{
							display: "flex",
							alignItems: "center",
							borderRadius: 1,
							bgcolor: marked?.uid === project.uid ? "action.selected" : undefined,
							borderTop: over === project.uid && dragged !== project.uid ? "2px solid" : "2px solid transparent",
							borderColor: over === project.uid ? "primary.main" : "transparent",
						}}
					>
						<Checkbox
							size="small"
							checked={visible.some((entry) => entry.uid === project.uid)}
							onChange={() => toggleVisible(project.uid)}
							slotProps={{ input: { "aria-label": t("projects.visible", { name: project.name }), "data-testid": workspaceTestIds.projectVisible(project.uid) } as never }}
						/>
						<Box
							role="button"
							tabIndex={0}
							onClick={() => mark(marked?.uid === project.uid ? null : project.uid)}
							onDoubleClick={() => {
								mark(project.uid);
								setCard({ project });
							}}
							onKeyDown={(event) => (event.key === "Enter" || event.key === " ") && mark(marked?.uid === project.uid ? null : project.uid)}
							data-testid={workspaceTestIds.projectName(project.uid)}
							sx={{ flexGrow: 1, cursor: "pointer", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}
						>
							{project.name}
						</Box>
						<SyncIndicator project={project} />
					</Box>
				))}
			</Box>
			{card && <ProjectCard project={card.project} onClose={() => setCard(undefined)} />}
		</Box>
	);
}
