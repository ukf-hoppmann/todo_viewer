import AddAlertIcon from "@mui/icons-material/AddAlert";
import CloseIcon from "@mui/icons-material/Close";
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, IconButton, MenuItem, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { EntityPicker, IconAction, type Entity } from "../../shared";
import { useSearchElementsQuery } from "../workspace";
import { toWriteError, useAddTriggerMutation, useRemoveTriggerMutation, type MemoOut, type TriggerOut, type WriteError } from "./api";
import { EVENT_STATUSES } from "./constants";
import { memosTestIds } from "./testIds";

const ITEM_KINDS = new Set(["epic", "story", "task"]);

/** The section "Triggers" of the memo detail: what makes the memo due by itself, with add and remove. */
export function TriggersSection({ memo }: { memo: MemoOut }) {
	const { t } = useTranslation("memos");
	const [remove] = useRemoveTriggerMutation();
	const [adding, setAdding] = useState(false);
	const [error, setError] = useState<string>();
	const open = !memo.archived && !memo.deleted;

	return (
		<Stack spacing={1} data-testid={memosTestIds.triggers}>
			{memo.triggers.length === 0 && (
				<Typography variant="body2" color="text.secondary">
					{t("triggers.none")}
				</Typography>
			)}
			{memo.triggers.map((trigger) => (
				<Box key={trigger.uid} data-testid={memosTestIds.trigger(trigger.uid)} data-arrived={trigger.arrived} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
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
							data-testid={memosTestIds.triggerRemove(trigger.uid)}
						>
							<CloseIcon fontSize="small" />
						</IconButton>
					)}
				</Box>
			))}
			{error && <Alert severity="error">{error}</Alert>}
			{open && (
				<Box>
					<IconAction label={t("triggers.add")} icon={AddAlertIcon} onClick={() => setAdding(true)} testId={memosTestIds.addTrigger} />
				</Box>
			)}
			{adding && <AddTriggerDialog memo={memo} onClose={() => setAdding(false)} />}
		</Stack>
	);
}

function describe(trigger: TriggerOut, t: (key: string, options?: Record<string, unknown>) => string): string {
	if (trigger.kind === "topic_date") return t("triggers.topicDate");
	const target = trigger.target ? `${trigger.target.label} — ${trigger.target.title}` : "?";
	return t("triggers.event", { item: target, status: t(`itemStatus.${trigger.status ?? ""}`, { defaultValue: trigger.status ?? "" }) });
}

function AddTriggerDialog({ memo, onClose }: { memo: MemoOut; onClose: () => void }) {
	const { t } = useTranslation("memos");
	const [add] = useAddTriggerMutation();
	const hasTopicDate = memo.path.length > 0;
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
			await add({ uid: memo.uid, kind, ...(kind === "event" ? { target: target ?? undefined, status } : {}) }).unwrap();
			onClose();
		} catch (failure) {
			setError(toWriteError(failure));
		}
	};
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": memosTestIds.triggerDialog } as never }}>
			<DialogTitle>{t("triggers.addTitle", { label: memo.label })}</DialogTitle>
			<DialogContent>
				<Stack spacing={2} sx={{ pt: 1 }}>
					<TextField select size="small" label={t("triggers.kind")} value={kind} onChange={(event) => setKind(event.target.value as typeof kind)} slotProps={{ htmlInput: { "data-testid": memosTestIds.triggerKind } }}>
						<MenuItem value="event">{t("triggers.kinds.event")}</MenuItem>
						<MenuItem value="topic_date" disabled={!hasTopicDate}>
							{t("triggers.kinds.topic_date")}
						</MenuItem>
					</TextField>
					{kind === "event" && (
						<>
							<EntityPicker label={t("triggers.item")} options={options} value={target} onChange={setTarget} onInputChange={setQuery} noOptionsText={t("triggers.searchHint")} />
							<TextField select size="small" label={t("triggers.status")} value={status} onChange={(event) => setStatus(event.target.value)} slotProps={{ htmlInput: { "data-testid": memosTestIds.triggerStatus } }}>
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
				<Button variant="contained" disabled={kind === "event" && !target} onClick={() => void save()} data-testid={memosTestIds.triggerSave}>
					{t("form.save")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}
