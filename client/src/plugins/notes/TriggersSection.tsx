import CloseIcon from "@mui/icons-material/Close";
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { EntityPicker, type Entity } from "../../shared";
import { useSearchElementsQuery } from "../workspace";
import { toWriteError, useAddTriggerMutation, useRemoveTriggerMutation, type NoteOut, type TriggerOut, type WriteError } from "./api";
import { EVENT_STATUSES } from "./constants";
import { notesTestIds } from "./testIds";

const ITEM_KINDS = new Set(["epic", "story", "task"]);

/** The section "Triggers" of the note detail: what makes the note due by itself, with add and remove. */
export function TriggersSection({ note }: { note: NoteOut }) {
	const { t } = useTranslation("notes");
	const [remove] = useRemoveTriggerMutation();
	const [adding, setAdding] = useState(false);
	const [error, setError] = useState<string>();
	const open = !note.archived && !note.deleted;

	return (
		<Stack spacing={1} data-testid={notesTestIds.triggers}>
			{note.triggers.length === 0 && (
				<Typography variant="body2" color="text.secondary">
					{t("triggers.none")}
				</Typography>
			)}
			{note.triggers.map((trigger) => (
				<Box key={trigger.uid} data-testid={notesTestIds.trigger(trigger.uid)} data-arrived={trigger.arrived} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
					<Typography variant="body2" sx={{ flexGrow: 1 }}>
						{describe(trigger, t)}
					</Typography>
					{trigger.arrived && <Typography variant="caption" color="error">{t(trigger.already_met ? "triggers.alreadyMet" : "triggers.arrived")}</Typography>}
					{open && (
						<IconButton
							size="small"
							aria-label={t("triggers.remove")}
							onClick={() => {
								setError(undefined);
								remove(trigger.uid)
									.unwrap()
									.catch((failure: unknown) => setError(toWriteError(failure).message));
							}}
							data-testid={notesTestIds.triggerRemove(trigger.uid)}
						>
							<CloseIcon fontSize="small" />
						</IconButton>
					)}
				</Box>
			))}
			{error && <Alert severity="error">{error}</Alert>}
			{open && (
				<Box>
					<Button size="small" variant="outlined" onClick={() => setAdding(true)} data-testid={notesTestIds.addTrigger}>
						{t("triggers.add")}
					</Button>
				</Box>
			)}
			{adding && <AddTriggerDialog note={note} onClose={() => setAdding(false)} />}
		</Stack>
	);
}

function describe(trigger: TriggerOut, t: (key: string, options?: Record<string, unknown>) => string): string {
	if (trigger.kind === "topic_date") return t("triggers.topicDate");
	const target = trigger.target ? `${trigger.target.label} — ${trigger.target.title}` : "?";
	return t("triggers.event", { item: target, status: t(`itemStatus.${trigger.status ?? ""}`, { defaultValue: trigger.status ?? "" }) });
}

function AddTriggerDialog({ note, onClose }: { note: NoteOut; onClose: () => void }) {
	const { t } = useTranslation("notes");
	const [add] = useAddTriggerMutation();
	const hasTopicDate = note.path.length > 0;
	const [kind, setKind] = useState<"event" | "topic_date">("event");
	const [status, setStatus] = useState<string>("Completed");
	const [query, setQuery] = useState("");
	const [target, setTarget] = useState<string | null>(null);
	const [error, setError] = useState<WriteError>();
	const { data: found = [] } = useSearchElementsQuery(query, { skip: query.trim() === "" });
	const options: Entity[] = found.filter((element) => ITEM_KINDS.has(element.kind)).map((element) => ({ id: element.uid, label: element.label, title: element.title }));

	const save = async () => {
		setError(undefined);
		try {
			await add({ uid: note.uid, kind, ...(kind === "event" ? { target: target ?? undefined, status } : {}) }).unwrap();
			onClose();
		} catch (failure) {
			setError(toWriteError(failure));
		}
	};
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": notesTestIds.triggerDialog } as never }}>
			<DialogTitle>{t("triggers.addTitle", { label: note.label })}</DialogTitle>
			<DialogContent>
				<Stack spacing={2} sx={{ pt: 1 }}>
					<TextField select size="small" label={t("triggers.kind")} value={kind} onChange={(event) => setKind(event.target.value as typeof kind)} slotProps={{ htmlInput: { "data-testid": notesTestIds.triggerKind } }}>
						<MenuItem value="event">{t("triggers.kinds.event")}</MenuItem>
						<MenuItem value="topic_date" disabled={!hasTopicDate}>
							{t("triggers.kinds.topic_date")}
						</MenuItem>
					</TextField>
					{kind === "event" && (
						<>
							<EntityPicker label={t("triggers.item")} options={options} value={target} onChange={setTarget} onInputChange={setQuery} noOptionsText={t("triggers.searchHint")} />
							<TextField select size="small" label={t("triggers.status")} value={status} onChange={(event) => setStatus(event.target.value)} slotProps={{ htmlInput: { "data-testid": notesTestIds.triggerStatus } }}>
								{EVENT_STATUSES.map((value) => (
									<MenuItem key={value} value={value}>
										{t(`itemStatus.${value}`)}
									</MenuItem>
								))}
							</TextField>
						</>
					)}
					{error && <Alert severity="error">{error.message}</Alert>}
				</Stack>
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{t("form.cancel")}</Button>
				<Button variant="contained" disabled={kind === "event" && !target} onClick={() => void save()} data-testid={notesTestIds.triggerSave}>
					{t("form.save")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}
