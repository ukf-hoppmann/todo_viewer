import { Box, TextField } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { EditForm, EntityPicker, type Entity } from "../../shared";
import { toWriteError, useGetNoteQuery, useListIndexQuery, type NoteOut } from "./api";
import { targetTopics } from "./model";
import { notesTestIds } from "./testIds";
import { useNoteWrite } from "./useNoteWrite";

interface Props {
	projectUid: string;
	/** The note to edit; a new one is created if missing. */
	note?: NoteOut;
	/** The topic a new note starts in. */
	topicUid?: string | null;
	onDone: () => void;
	onCancel: () => void;
}

const day = (moment: string | null | undefined) => (moment ? moment.slice(0, 10) : "");

/**
 * The form to create or edit a note. The summary is required; an empty review date means the default
 * (today plus the review interval). Saving sends only what changed when editing, and a version conflict offers to
 * load the current state.
 */
export function NoteForm({ projectUid, note, topicUid = null, onDone, onCancel }: Props) {
	const { t } = useTranslation("notes");
	const write = useNoteWrite();
	const { data: index } = useListIndexQuery([projectUid]);
	const { refetch } = useGetNoteQuery(note?.uid ?? "", { skip: !note });
	const [summary, setSummary] = useState(note?.summary ?? "");
	const [body, setBody] = useState(note?.body ?? "");
	const [topic, setTopic] = useState<string | null>(note ? note.topic_uid : topicUid);
	const [reviewAt, setReviewAt] = useState(day(note?.review_at));

	const topics: Entity[] = useMemo(
		() => targetTopics(index?.topics ?? [], projectUid).map((entry) => ({ id: entry.uid, label: entry.label, title: entry.name })),
		[index, projectUid],
	);

	const save = async () => {
		try {
			if (note) {
				const fields: Record<string, unknown> = {};
				if (summary !== note.summary) fields.summary = summary;
				if (body !== (note.body ?? "")) fields.body = body;
				if (topic !== note.topic_uid) fields.topic = topic;
				if (reviewAt && reviewAt !== day(note.review_at)) fields.review_at = reviewAt;
				if (Object.keys(fields).length > 0) await write.updateNote(note, fields);
			} else {
				const fields: Record<string, unknown> = { summary };
				if (body.trim()) fields.body = body;
				if (topic) fields.topic = topic;
				if (reviewAt) fields.review_at = reviewAt;
				await write.createNote(projectUid, fields);
			}
		} catch (failure) {
			throw toWriteError(failure);
		}
		onDone();
	};

	return (
		<Box data-testid={notesTestIds.form}>
			<EditForm
				onSave={save}
				onCancel={onCancel}
				onReload={async () => {
					await refetch();
				}}
				labels={{ save: t("form.save"), cancel: t("form.cancel"), conflict: t("form.conflict"), reload: t("form.reload") }}
			>
				<TextField label={t("field.summary")} value={summary} onChange={(event) => setSummary(event.target.value)} required size="small" autoFocus slotProps={{ htmlInput: { "data-testid": notesTestIds.formField("summary") } }} />
				<EntityPicker label={t("field.topic")} options={topics} value={topic} onChange={setTopic} />
				<TextField
					type="date"
					label={t("field.reviewAt")}
					helperText={t("form.reviewHint")}
					value={reviewAt}
					onChange={(event) => setReviewAt(event.target.value)}
					size="small"
					slotProps={{ inputLabel: { shrink: true }, htmlInput: { "data-testid": notesTestIds.formField("review_at") } }}
				/>
				<TextField label={t("field.body")} value={body} onChange={(event) => setBody(event.target.value)} multiline minRows={4} size="small" slotProps={{ htmlInput: { "data-testid": notesTestIds.formField("body") } }} />
			</EditForm>
		</Box>
	);
}
