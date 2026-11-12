import { Alert, Box, Button, Checkbox, Dialog, DialogActions, DialogContent, DialogTitle, FormControlLabel, TextField, Typography } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { EditForm, EntityPicker, type Entity } from "../../shared";
import { toWriteError, useListIndexQuery, useTopicContentQuery, type IndexedMemo, type IndexedTopic, type TopicChoice, type WriteError } from "./api";
import { targetTopics } from "./model";
import { memosTestIds } from "./testIds";
import { useMemoWrite } from "./useMemoWrite";

const day = (moment: string | null | undefined) => (moment ? moment.slice(0, 10) : "");

interface FormProps {
	projectUid: string;
	/** The topic to rename or give a date; a new one is created if missing. */
	topic?: IndexedTopic;
	/** The parent of a new topic. */
	parentUid?: string | null;
	onDone: () => void;
	onCancel: () => void;
}

/** Name and due date of a topic: creates a new one (below `parentUid`) or changes an existing one. */
export function TopicForm({ projectUid, topic, parentUid = null, onDone, onCancel }: FormProps) {
	const { t } = useTranslation("memos");
	const write = useMemoWrite();
	const [name, setName] = useState(topic?.name ?? "");
	const [dueAt, setDueAt] = useState(day(topic?.due_at));

	const save = async () => {
		try {
			if (topic) {
				const fields: Record<string, unknown> = {};
				if (name !== topic.name) fields.name = name;
				if (dueAt !== day(topic.due_at)) fields.due_at = dueAt || null;
				if (Object.keys(fields).length > 0) await write.updateTopic(topic, fields);
			} else {
				await write.createTopic(projectUid, name, parentUid, dueAt || null);
			}
		} catch (failure) {
			throw toWriteError(failure);
		}
		onDone();
	};
	return (
		<Box data-testid={memosTestIds.topicDialog}>
			<EditForm
				onSave={save}
				onCancel={onCancel}
				onReload={() => undefined}
				labels={{ save: t("form.save"), cancel: t("form.cancel"), conflict: t("form.conflict"), reload: t("form.reload") }}
			>
				<TextField label={t("field.name")} value={name} onChange={(event) => setName(event.target.value)} required size="small" autoFocus disabled={topic?.system} slotProps={{ htmlInput: { "data-testid": memosTestIds.topicField("name") } }} />
				<TextField
					type="date"
					label={t("field.dueAt")}
					value={dueAt}
					onChange={(event) => setDueAt(event.target.value)}
					size="small"
					slotProps={{ inputLabel: { shrink: true }, htmlInput: { "data-testid": memosTestIds.topicField("due_at") } }}
				/>
			</EditForm>
		</Box>
	);
}

/** The topic form in a dialog. */
export function TopicFormDialog({ projectUid, topic, parentUid, onClose }: { projectUid: string; topic?: IndexedTopic; parentUid?: string | null; onClose: () => void }) {
	const { t } = useTranslation("memos");
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm">
			<DialogTitle>{topic ? t("topic.editTitle", { label: topic.label }) : t("topic.createTitle")}</DialogTitle>
			<DialogContent dividers>
				<TopicForm projectUid={projectUid} topic={topic} parentUid={parentUid} onDone={onClose} onCancel={onClose} />
			</DialogContent>
		</Dialog>
	);
}

type Moved = { kind: "topic"; topic: IndexedTopic } | { kind: "memo"; memo: IndexedMemo };

/** Chooses the new parent of a topic or the new topic of a memo ("without topic" is the project itself). */
export function MoveDialog({ moved, onClose }: { moved: Moved; onClose: () => void }) {
	const { t } = useTranslation("memos");
	const write = useMemoWrite();
	const item = moved.kind === "topic" ? moved.topic : moved.memo;
	const { data: index } = useListIndexQuery([item.project_uid]);
	const [target, setTarget] = useState<string | null>(moved.kind === "topic" ? moved.topic.parent_uid : moved.memo.topic_uid);
	const [error, setError] = useState<WriteError>();
	const options: Entity[] = useMemo(
		() => targetTopics(index?.topics ?? [], item.project_uid, moved.kind === "topic" ? moved.topic.uid : undefined).map((entry) => ({ id: entry.uid, label: entry.label, title: entry.name })),
		[index, item.project_uid, moved],
	);
	const save = async () => {
		setError(undefined);
		try {
			if (moved.kind === "topic") await write.moveTopic(moved.topic, target);
			else await write.updateMemo(moved.memo, { topic: target });
			onClose();
		} catch (failure) {
			setError(toWriteError(failure));
		}
	};
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": memosTestIds.moveDialog } as never }}>
			<DialogTitle>{t("move.title", { label: item.label })}</DialogTitle>
			<DialogContent>
				<Box sx={{ pt: 1, display: "flex", flexDirection: "column", gap: 1 }}>
					<EntityPicker label={moved.kind === "topic" ? t("move.parent") : t("field.topic")} options={options} value={target} onChange={setTarget} />
					<Typography variant="caption" color="text.secondary">
						{t("move.noTopicHint")}
					</Typography>
					{error && <Alert severity="error">{error.message}</Alert>}
				</Box>
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{t("form.cancel")}</Button>
				<Button variant="contained" onClick={() => void save()} data-testid={memosTestIds.moveSave}>
					{t("form.save")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}

/**
 * Deleting or archiving a topic. A topic with content shows how many active and archived memos and sub-topics
 * it holds and asks what happens to the memos: archived ones can be kept (they move to the topic "Archived" of the
 * project) and active ones can be moved to another topic; what is not chosen goes with the topic (when archiving
 * the active memos are archived with it). "OK" does it all in one request, "Cancel" changes nothing.
 */
export function TopicChoiceDialog({ topic, mode, onClose }: { topic: IndexedTopic; mode: "delete" | "archive"; onClose: () => void }) {
	const { t } = useTranslation("memos");
	const write = useMemoWrite();
	const { data: content } = useTopicContentQuery(topic.uid);
	const { data: index } = useListIndexQuery([topic.project_uid]);
	const [keepArchived, setKeepArchived] = useState(false);
	const [moveActive, setMoveActive] = useState(false);
	const [target, setTarget] = useState<string | null>(null);
	const [error, setError] = useState<WriteError>();
	const options: Entity[] = useMemo(
		() => targetTopics(index?.topics ?? [], topic.project_uid, topic.uid).map((entry) => ({ id: entry.uid, label: entry.label, title: entry.name })),
		[index, topic],
	);
	const hasContent = content !== undefined && (content.topics > 0 || content.active > 0 || content.archived > 0);

	const confirm = async () => {
		setError(undefined);
		const choice: TopicChoice | undefined = hasContent
			? { keep_archived: keepArchived, active_memos: moveActive ? "move" : mode === "delete" ? "delete" : "archive", move_to: moveActive ? target : undefined }
			: undefined;
		try {
			if (mode === "delete") await write.deleteTopic(topic, choice);
			else await write.archiveTopic(topic, choice);
			onClose();
		} catch (failure) {
			setError(toWriteError(failure));
		}
	};

	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": memosTestIds.choiceDialog } as never }}>
			<DialogTitle>{t(`choice.${mode}Title`, { label: topic.label })}</DialogTitle>
			<DialogContent>
				{!content && <Typography color="text.secondary">…</Typography>}
				{content && !hasContent && <Typography>{t(`choice.${mode}Empty`)}</Typography>}
				{content && hasContent && (
					<Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
						<Typography data-testid={memosTestIds.choiceCounts}>{t("choice.counts", { active: content.active, archived: content.archived, topics: content.topics })}</Typography>
						{content.archived > 0 && (
							<FormControlLabel
								control={<Checkbox checked={keepArchived} onChange={(event) => setKeepArchived(event.target.checked)} slotProps={{ input: { "data-testid": memosTestIds.choiceKeepArchived } as never }} />}
								label={t("choice.keepArchived")}
							/>
						)}
						{content.active > 0 && (
							<>
								<FormControlLabel
									control={<Checkbox checked={moveActive} onChange={(event) => setMoveActive(event.target.checked)} slotProps={{ input: { "data-testid": memosTestIds.choiceMove } as never }} />}
									label={t("choice.moveActive")}
								/>
								{moveActive && <EntityPicker label={t("choice.target")} options={options} value={target} onChange={setTarget} />}
							</>
						)}
						<Typography variant="caption" color="text.secondary">
							{t(`choice.${mode}Rest`)}
						</Typography>
					</Box>
				)}
				{error && (
					<Alert severity="error" sx={{ mt: 1 }}>
						{error.message}
					</Alert>
				)}
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{t("form.cancel")}</Button>
				<Button variant="contained" disabled={!content} onClick={() => void confirm()} data-testid={memosTestIds.choiceConfirm}>
					{t("choice.ok")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}
