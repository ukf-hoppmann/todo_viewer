import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField } from "@mui/material";
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { toWriteError, useDecideNoticeMutation, usePromoteNoteMutation, type NoteOut, type WriteError } from "./api";
import { notesTestIds } from "./testIds";

const TYPES = ["Epic", "Story", "Task"] as const;

interface Props {
	note: Pick<NoteOut, "uid" | "label" | "summary" | "version">;
	/** The notice this promotion decides (the decision `promote`); without it the note is promoted on its own. */
	noticeUid?: string;
	onClose: () => void;
}

/**
 * Promotes a note to an item: the type and the fields the backlog requires (area, goal, completion criteria);
 * the title is the summary of the note unless another is given. The server refuses what the backlog refuses and
 * the message stays in the dialog.
 */
export function PromoteDialog({ note, noticeUid, onClose }: Props) {
	const { t } = useTranslation("notes");
	const [promote] = usePromoteNoteMutation();
	const [decide] = useDecideNoticeMutation();
	const [type, setType] = useState<(typeof TYPES)[number]>("Task");
	const [title, setTitle] = useState("");
	const [area, setArea] = useState("");
	const [goal, setGoal] = useState("");
	const [criteria, setCriteria] = useState("");
	const [error, setError] = useState<WriteError>();

	const submit = async (event: FormEvent) => {
		event.preventDefault();
		setError(undefined);
		const fields: Record<string, unknown> = { area, goal, completion_criteria: criteria };
		if (title.trim()) fields.title = title;
		try {
			if (noticeUid) await decide({ uid: noticeUid, decision: "promote", version: note.version, type, fields }).unwrap();
			else await promote({ uid: note.uid, version: note.version, type, fields }).unwrap();
			onClose();
		} catch (failure) {
			setError(toWriteError(failure));
		}
	};
	const field = (name: string, label: string, value: string, set: (value: string) => void, extra: { required?: boolean; multiline?: boolean; placeholder?: string } = {}) => (
		<TextField
			label={label}
			value={value}
			onChange={(event) => set(event.target.value)}
			size="small"
			multiline={extra.multiline}
			minRows={extra.multiline ? 2 : undefined}
			required={extra.required}
			placeholder={extra.placeholder}
			slotProps={{ htmlInput: { "data-testid": notesTestIds.promoteField(name) } }}
		/>
	);
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm" slotProps={{ paper: { component: "form", onSubmit: submit, "data-testid": notesTestIds.promoteDialog } as never }}>
			<DialogTitle>{t("promote.title", { label: note.label })}</DialogTitle>
			<DialogContent>
				<Stack spacing={2} sx={{ pt: 1 }}>
					<TextField select size="small" label={t("promote.type")} value={type} onChange={(event) => setType(event.target.value as typeof type)} slotProps={{ htmlInput: { "data-testid": notesTestIds.promoteField("type") } }}>
						{TYPES.map((value) => (
							<MenuItem key={value} value={value}>
								{value}
							</MenuItem>
						))}
					</TextField>
					{field("title", t("promote.itemTitle"), title, setTitle, { placeholder: note.summary })}
					{field("area", t("promote.area"), area, setArea, { required: true })}
					{field("goal", t("promote.goal"), goal, setGoal, { required: true, multiline: true })}
					{field("completion_criteria", t("promote.criteria"), criteria, setCriteria, { required: true, multiline: true })}
					<Alert severity="info">{t("promote.hint")}</Alert>
					{error && (
						<Alert severity="error" data-testid={notesTestIds.promoteError}>
							{error.message}
						</Alert>
					)}
				</Stack>
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{t("form.cancel")}</Button>
				<Button type="submit" variant="contained" data-testid={notesTestIds.promoteConfirm}>
					{t("promote.confirm")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}
