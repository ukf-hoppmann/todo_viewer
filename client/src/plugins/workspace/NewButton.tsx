import AddIcon from "@mui/icons-material/Add";
import { Button, Dialog, DialogContent, DialogTitle, Menu, MenuItem } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useSlot, type SlotEntry } from "../../core";
import { CreateDialogState } from "./createDialog";
import { ProjectCard } from "./ProjectCard";
import { useProjectSelection } from "./state";
import { workspaceTestIds } from "./testIds";

type Chosen = { kind: "project" } | { kind: "entry"; entry: SlotEntry };

/**
 * The button "＋ New" in the app bar. Its menu offers a project and every create type that plugins hang into
 * the slot `workspace.create-types`: the entry's `component` is the form, its `name` the kind, and the title
 * is the text `create.<name>` in the namespace of the plugin that contributed it.
 */
export function NewButton() {
	const { t } = useTranslation("workspace");
	const entries = useSlot("workspace.create-types");
	const { projects, marked } = useProjectSelection();
	const [anchor, setAnchor] = useState<HTMLElement | null>(null);
	const [chosen, setChosen] = useState<Chosen>();
	const close = () => setChosen(undefined);
	const defaultProject = marked ?? projects.find((project) => project.builtin);

	return (
		<>
			<Button color="inherit" startIcon={<AddIcon />} onClick={(event) => setAnchor(event.currentTarget)} data-testid={workspaceTestIds.newButton}>
				{t("new.button")}
			</Button>
			<Menu anchorEl={anchor} open={anchor !== null} onClose={() => setAnchor(null)}>
				{entries.map((entry) => (
					<NewMenuItem
						key={`${entry.ownerId}/${entry.name}`}
						entry={entry}
						onChoose={() => {
							setAnchor(null);
							setChosen({ kind: "entry", entry });
						}}
					/>
				))}
				<MenuItem
					onClick={() => {
						setAnchor(null);
						setChosen({ kind: "project" });
					}}
					data-testid={workspaceTestIds.newMenuItem("project")}
				>
					{t("new.project")}
				</MenuItem>
			</Menu>
			{chosen?.kind === "project" && <ProjectCard onClose={close} />}
			{chosen?.kind === "entry" && (
				<CreateDialogState.Provider value={{ close, projectUid: defaultProject?.uid }}>
					<NewDialog entry={chosen.entry} onClose={close} />
				</CreateDialogState.Provider>
			)}
		</>
	);
}

function NewMenuItem({ entry, onChoose }: { entry: SlotEntry; onChoose: () => void }) {
	const { t } = useTranslation(entry.ownerId);
	return (
		<MenuItem onClick={onChoose} data-testid={workspaceTestIds.newMenuItem(entry.name)}>
			{t(`create.${entry.name}`)}
		</MenuItem>
	);
}

function NewDialog({ entry, onClose }: { entry: SlotEntry; onClose: () => void }) {
	const { t } = useTranslation(entry.ownerId);
	const Form = entry.component;
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": workspaceTestIds.newDialog } as never }}>
			<DialogTitle>{t(`create.${entry.name}`)}</DialogTitle>
			<DialogContent>
				<Form />
			</DialogContent>
		</Dialog>
	);
}
