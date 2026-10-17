import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import RestoreIcon from "@mui/icons-material/Restore";
import SnoozeIcon from "@mui/icons-material/Snooze";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";
import { Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { DetailField, DetailPanel, DetailSection, LargeView, MarkdownView, type DetailAction } from "../../shared";
import { LinksSection, useDeleteElement } from "../workspace";
import { useGetNoteQuery, type NoteOut, type WriteError } from "./api";
import { statusColor } from "./constants";
import { DocumentsSection } from "./DocumentsSection";
import { NoteForm } from "./NoteForm";
import { notesTestIds } from "./testIds";
import { useNoteWrite } from "./useNoteWrite";

const day = (moment: string | null | undefined) => (moment ? moment.slice(0, 10) : "");

/** The detail panel of a note: status, topic path, review date, text, documents and links, and the actions. */
export function NoteDetail({ uid }: { uid: string }) {
	const { t } = useTranslation("notes");
	const { data: note, isError } = useGetNoteQuery(uid);
	if (isError) return <Typography color="error" sx={{ p: 2 }}>{t("detail.failed")}</Typography>;
	if (!note) return null;
	return <Loaded note={note} />;
}

function Loaded({ note }: { note: NoteOut }) {
	const { t } = useTranslation("notes");
	const write = useNoteWrite();
	const trash = useDeleteElement();
	const [dialog, setDialog] = useState<"edit" | "snooze" | "large">();
	const [error, setError] = useState<string>();

	const run = (action: Promise<unknown>) => {
		setError(undefined);
		action.catch((failure: WriteError) => setError(failure.message));
	};
	const closed = note.deleted;
	const archived = note.archived;
	const actions: DetailAction[] = closed
		? []
		: archived
			? [
					{ id: "restore", label: t("action.restore"), icon: RestoreIcon, onClick: () => run(write.restore(note)) },
					{ id: "large", label: t("action.large"), icon: FullscreenIcon, onClick: () => setDialog("large") },
					{ id: "delete", label: t("action.delete"), icon: DeleteIcon, onClick: () => void trash.requestDelete(note.uid, note.version) },
				]
			: [
					{ id: "edit", label: t("action.edit"), icon: EditIcon, onClick: () => setDialog("edit") },
					{ id: "done", label: t("action.done"), icon: CheckIcon, onClick: () => run(write.finish(note, "done")) },
					{ id: "dropped", label: t("action.dropped"), icon: CloseIcon, onClick: () => run(write.finish(note, "dropped")) },
					{ id: "snooze", label: t("action.snooze"), icon: SnoozeIcon, onClick: () => setDialog("snooze") },
					{ id: "keep", label: t("action.keep"), icon: ThumbUpIcon, onClick: () => run(write.keep(note)) },
					{ id: "delete", label: t("action.delete"), icon: DeleteIcon, onClick: () => void trash.requestDelete(note.uid, note.version) },
					{ id: "large", label: t("action.large"), icon: FullscreenIcon, onClick: () => setDialog("large") },
				];

	return (
		<Box data-testid={notesTestIds.detail}>
			<DetailPanel title={`${note.label} — ${note.summary}`} subtitle={note.deleted ? t("detail.deleted") : t(`status.${note.status}`)} actions={actions}>
				{(error ?? trash.failed) && (
					<Alert severity="error" data-testid={notesTestIds.detailError} onClose={() => setError(undefined)}>
						{error ?? trash.failed}
					</Alert>
				)}
				<DetailField id="status" label={t("field.status")}>
					<Chip size="small" label={t(`status.${note.status}`)} sx={{ bgcolor: statusColor(note.status), color: "common.white" }} data-testid={notesTestIds.detailStatus} />
					{note.archived && !["done", "dropped", "promoted"].includes(note.stored_status) && <Chip size="small" variant="outlined" label={t("detail.archivedWithTopic")} sx={{ ml: 1 }} />}
				</DetailField>
				<DetailField id="topic" label={t("field.topic")}>
					<span data-testid={notesTestIds.detailPath}>{note.path.length > 0 ? note.path.map((entry) => entry.name).join(" › ") : t("detail.noTopic")}</span>
				</DetailField>
				<DetailField id="review" label={t("field.reviewAt")}>
					<span data-testid={notesTestIds.detailReview}>{day(note.review_at) || "—"}</span>
				</DetailField>
				{note.body && (
					<DetailField id="body" label={t("field.body")}>
						<span data-testid={notesTestIds.detailBody}>
							<MarkdownView source={note.body} />
						</span>
					</DetailField>
				)}
				<DetailSection id="documents" title={t("field.documents")}>
					<DocumentsSection note={note} />
				</DetailSection>
				<DetailSection id="links" title={t("field.links")} defaultOpen={false}>
					<LinksSection elementUid={note.uid} />
				</DetailSection>
			</DetailPanel>
			{dialog === "edit" && (
				<Dialog open onClose={() => setDialog(undefined)} fullWidth maxWidth="md" slotProps={{ paper: { "data-testid": notesTestIds.formDialog } as never }}>
					<DialogTitle>{t("form.editTitle", { label: note.label })}</DialogTitle>
					<DialogContent dividers>
						<NoteForm key={note.version} projectUid={note.project_uid} note={note} onDone={() => setDialog(undefined)} onCancel={() => setDialog(undefined)} />
					</DialogContent>
				</Dialog>
			)}
			{dialog === "snooze" && (
				<SnoozeDialog
					note={note}
					onClose={() => setDialog(undefined)}
					onSnooze={async (reviewAt) => {
						await write.snooze(note, reviewAt);
						setDialog(undefined);
					}}
				/>
			)}
			{dialog === "large" && (
				<LargeView open onClose={() => setDialog(undefined)} title={`${note.label} — ${note.summary}`} markdown={note.body ?? ""} closeLabel={t("form.close")} tocLabel={t("documents.toc")} />
			)}
			{trash.dialog}
		</Box>
	);
}

/** Chooses until when a note is snoozed; without a date it waits for the review interval. */
function SnoozeDialog({ note, onClose, onSnooze }: { note: NoteOut; onClose: () => void; onSnooze: (reviewAt?: string) => Promise<void> }) {
	const { t } = useTranslation("notes");
	const [date, setDate] = useState("");
	const [error, setError] = useState<string>();
	const confirm = async () => {
		try {
			await onSnooze(date || undefined);
		} catch (failure) {
			setError(failure instanceof Error ? failure.message : String(failure));
		}
	};
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="xs" slotProps={{ paper: { "data-testid": notesTestIds.snoozeDialog } as never }}>
			<DialogTitle>{t("snooze.title", { label: note.label })}</DialogTitle>
			<DialogContent>
				<TextField
					type="date"
					fullWidth
					margin="dense"
					size="small"
					label={t("snooze.until")}
					helperText={t("snooze.hint")}
					value={date}
					onChange={(event) => setDate(event.target.value)}
					slotProps={{ inputLabel: { shrink: true }, htmlInput: { "data-testid": notesTestIds.snoozeDate } }}
				/>
				{error && <Alert severity="error">{error}</Alert>}
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{t("form.cancel")}</Button>
				<Button variant="contained" onClick={() => void confirm()} data-testid={notesTestIds.snoozeConfirm}>
					{t("action.snooze")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}
