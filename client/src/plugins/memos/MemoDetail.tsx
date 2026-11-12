import CheckIcon from "@mui/icons-material/Check";
import CloseIcon from "@mui/icons-material/Close";
import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import RestoreIcon from "@mui/icons-material/Restore";
import SnoozeIcon from "@mui/icons-material/Snooze";
import NorthEastIcon from "@mui/icons-material/NorthEast";
import ThumbUpIcon from "@mui/icons-material/ThumbUp";
import { Alert, Box, Button, Chip, Dialog, DialogActions, DialogContent, DialogTitle, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { DetailField, DetailPanel, DetailSection, LargeView, MarkdownView, type DetailAction } from "../../shared";
import { DetailSections, LinksSection, useDeleteElement } from "../workspace";
import { useGetMemoQuery, type MemoOut, type WriteError } from "./api";
import { statusColor } from "./constants";
import { DocumentsSection } from "./DocumentsSection";
import { MemoForm } from "./MemoForm";
import { HintsSection } from "./HintsSection";
import { PromoteDialog } from "./PromoteDialog";
import { TriggersSection } from "./TriggersSection";
import { memosTestIds } from "./testIds";
import { useMemoWrite } from "./useMemoWrite";

const day = (moment: string | null | undefined) => (moment ? moment.slice(0, 10) : "");

/** The detail panel of a memo: status, topic path, review date, text, documents and links, and the actions. */
export function MemoDetail({ uid, onClose }: { uid: string; onClose?: () => void }) {
	const { t } = useTranslation("memos");
	const { data: memo, isError } = useGetMemoQuery(uid);
	if (isError) return <Typography color="error" sx={{ p: 2 }}>{t("detail.failed")}</Typography>;
	if (!memo) return null;
	return <Loaded memo={memo} onClose={onClose} />;
}

function Loaded({ memo, onClose }: { memo: MemoOut; onClose?: () => void }) {
	const { t } = useTranslation("memos");
	const write = useMemoWrite();
	const trash = useDeleteElement();
	const [dialog, setDialog] = useState<"edit" | "snooze" | "large" | "promote">();
	const [error, setError] = useState<string>();

	const run = (action: Promise<unknown>) => {
		setError(undefined);
		action.catch((failure: WriteError) => setError(failure.message));
	};
	const closed = memo.deleted;
	const archived = memo.archived;
	const actions: DetailAction[] = closed
		? []
		: archived
			? [
					{ id: "restore", label: t("action.restore"), icon: RestoreIcon, onClick: () => run(write.restore(memo)) },
					{ id: "large", label: t("action.large"), icon: FullscreenIcon, onClick: () => setDialog("large") },
					{ id: "delete", label: t("action.delete"), icon: DeleteIcon, onClick: () => void trash.requestDelete(memo.uid, memo.version) },
				]
			: [
					{ id: "edit", label: t("action.edit"), icon: EditIcon, onClick: () => setDialog("edit") },
					{ id: "done", label: t("action.done"), icon: CheckIcon, onClick: () => run(write.finish(memo, "done")) },
					{ id: "dropped", label: t("action.dropped"), icon: CloseIcon, onClick: () => run(write.finish(memo, "dropped")) },
					{ id: "snooze", label: t("action.snooze"), icon: SnoozeIcon, onClick: () => setDialog("snooze") },
					{ id: "promote", label: t("action.promote"), icon: NorthEastIcon, onClick: () => setDialog("promote") },
					{ id: "keep", label: t("action.keep"), icon: ThumbUpIcon, onClick: () => run(write.keep(memo)) },
					{ id: "delete", label: t("action.delete"), icon: DeleteIcon, onClick: () => void trash.requestDelete(memo.uid, memo.version) },
					{ id: "large", label: t("action.large"), icon: FullscreenIcon, onClick: () => setDialog("large") },
				];

	return (
		<Box data-testid={memosTestIds.detail}>
			<DetailPanel title={`${memo.label} — ${memo.summary}`} subtitle={memo.deleted ? t("detail.deleted") : t(`status.${memo.status}`)} actions={actions} onClose={onClose} closeLabel={t("form.close")}>
				{(error ?? trash.failed) && (
					<Alert severity="error" data-testid={memosTestIds.detailError} onClose={() => setError(undefined)}>
						{error ?? trash.failed}
					</Alert>
				)}
				<DetailField id="status" label={t("field.status")}>
					<Chip size="small" label={t(`status.${memo.status}`)} sx={{ bgcolor: statusColor(memo.status), color: "common.white" }} data-testid={memosTestIds.detailStatus} />
					{memo.archived && !["done", "dropped", "promoted"].includes(memo.stored_status) && <Chip size="small" variant="outlined" label={t("detail.archivedWithTopic")} sx={{ ml: 1 }} />}
				</DetailField>
				<DetailField id="topic" label={t("field.topic")}>
					<span data-testid={memosTestIds.detailPath}>{memo.path.length > 0 ? memo.path.map((entry) => entry.name).join(" › ") : t("detail.noTopic")}</span>
				</DetailField>
				<DetailField id="review" label={t("field.reviewAt")}>
					<span data-testid={memosTestIds.detailReview}>{day(memo.review_at) || "—"}</span>
				</DetailField>
				{memo.body && (
					<DetailField id="body" label={t("field.body")}>
						<span data-testid={memosTestIds.detailBody}>
							<MarkdownView source={memo.body} outlineLabel={t("documents.toc")} />
						</span>
					</DetailField>
				)}
				{memo.reason && !memo.archived && (
					<DetailField id="reason" label={t("field.reason")}>
						<span data-testid={memosTestIds.detailReason}>{t(`reason.${memo.reason}`)}</span>
					</DetailField>
				)}
				<DetailSection id="triggers" title={t("field.triggers")} defaultOpen={memo.triggers.length > 0}>
					<TriggersSection memo={memo} />
				</DetailSection>
				<DetailSection id="hints" title={t("field.hints")} defaultOpen={memo.hints.length > 0}>
					<HintsSection memo={memo} />
				</DetailSection>
				<DetailSection id="documents" title={t("field.documents")}>
					<DocumentsSection memo={memo} />
				</DetailSection>
				<DetailSection id="links" title={t("field.links")} defaultOpen={false}>
					<LinksSection elementUid={memo.uid} />
				</DetailSection>
				<DetailSections uid={memo.uid} label={memo.label} projectUid={memo.project_uid} />
			</DetailPanel>
			{dialog === "edit" && (
				<Dialog open onClose={() => setDialog(undefined)} fullWidth maxWidth="md" slotProps={{ paper: { "data-testid": memosTestIds.formDialog } as never }}>
					<DialogTitle>{t("form.editTitle", { label: memo.label })}</DialogTitle>
					<DialogContent dividers>
						<MemoForm key={memo.version} projectUid={memo.project_uid} memo={memo} onDone={() => setDialog(undefined)} onCancel={() => setDialog(undefined)} />
					</DialogContent>
				</Dialog>
			)}
			{dialog === "snooze" && (
				<SnoozeDialog
					memo={memo}
					onClose={() => setDialog(undefined)}
					onSnooze={async (reviewAt) => {
						await write.snooze(memo, reviewAt);
						setDialog(undefined);
					}}
				/>
			)}
			{dialog === "promote" && <PromoteDialog memo={memo} onClose={() => setDialog(undefined)} />}
			{dialog === "large" && (
				<LargeView open onClose={() => setDialog(undefined)} title={`${memo.label} — ${memo.summary}`} markdown={memo.body ?? ""} closeLabel={t("form.close")} tocLabel={t("documents.toc")} />
			)}
			{trash.dialog}
		</Box>
	);
}

/** Chooses until when a memo is snoozed; without a date it waits for the review interval. */
function SnoozeDialog({ memo, onClose, onSnooze }: { memo: MemoOut; onClose: () => void; onSnooze: (reviewAt?: string) => Promise<void> }) {
	const { t } = useTranslation("memos");
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
		<Dialog open onClose={onClose} fullWidth maxWidth="xs" slotProps={{ paper: { "data-testid": memosTestIds.snoozeDialog } as never }}>
			<DialogTitle>{t("snooze.title", { label: memo.label })}</DialogTitle>
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
					slotProps={{ inputLabel: { shrink: true }, htmlInput: { "data-testid": memosTestIds.snoozeDate } }}
				/>
				{error && <Alert severity="error">{error}</Alert>}
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{t("form.cancel")}</Button>
				<Button variant="contained" onClick={() => void confirm()} data-testid={memosTestIds.snoozeConfirm}>
					{t("action.snooze")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}
