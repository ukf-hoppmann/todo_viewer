import DescriptionIcon from "@mui/icons-material/Description";
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { LargeView, MarkdownEditor, MarkdownView } from "../../shared";
import {
	toWriteError,
	useAppendNoteMutation,
	useGetDocumentQuery,
	usePutDocumentMutation,
	type ItemOut,
	type WriteError,
} from "./api";
import { backlogTestIds } from "./testIds";

/** The section "Documents" of the detail panel: the notes and specs of the item, and the buttons to add to them. */
export function DocumentsSection({ item }: { item: ItemOut }) {
	const { t } = useTranslation("backlog");
	const [open, setOpen] = useState<string>();
	const [dialog, setDialog] = useState<"note" | "spec">();
	const names = [...item.notes, ...item.spec];

	return (
		<Stack spacing={1} data-testid={backlogTestIds.documents}>
			{names.length === 0 && (
				<Typography variant="body2" color="text.secondary">
					{t("documents.none")}
				</Typography>
			)}
			{names.map((name) => (
				<Button
					key={name}
					size="small"
					startIcon={<DescriptionIcon />}
					onClick={() => setOpen(name)}
					data-testid={backlogTestIds.document(name)}
					sx={{ justifyContent: "flex-start", textTransform: "none" }}
				>
					{name}
				</Button>
			))}
			{!item.deleted && (
				<Box sx={{ display: "flex", gap: 1 }}>
					<Button size="small" variant="outlined" onClick={() => setDialog("note")} data-testid={backlogTestIds.addNote}>
						{t("documents.addNote")}
					</Button>
					<Button size="small" variant="outlined" onClick={() => setDialog("spec")} data-testid={backlogTestIds.addSpec}>
						{t("documents.addSpec")}
					</Button>
				</Box>
			)}
			{open && <DocumentDialog item={item} name={open} onClose={() => setOpen(undefined)} />}
			{dialog === "note" && <NoteEntryDialog item={item} onClose={() => setDialog(undefined)} />}
			{dialog === "spec" && <SpecDialog item={item} onClose={() => setDialog(undefined)} onCreated={setOpen} />}
		</Stack>
	);
}

/** A document: the formatted text, and "Edit" with the editor, its preview and the way out of a conflict. */
function DocumentDialog({ item, name, onClose }: { item: ItemOut; name: string; onClose: () => void }) {
	const { t } = useTranslation("backlog");
	const { data: document, refetch } = useGetDocumentQuery({ uid: item.uid, name });
	const [put] = usePutDocumentMutation();
	const [draft, setDraft] = useState<string>();
	const [large, setLarge] = useState(false);
	const [current, setCurrent] = useState<string>();
	const [version, setVersion] = useState<number>();
	const editing = draft !== undefined;

	const save = async (force: boolean) => {
		if (!document || draft === undefined) return;
		let base = version ?? document.version;
		if (force) base = (await refetch()).data?.version ?? base;
		try {
			const saved = await put({ uid: item.uid, name, content: draft, version: base }).unwrap();
			setVersion(saved.version);
			setDraft(undefined);
		} catch (failure) {
			throw toWriteError(failure);
		}
	};

	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="md" slotProps={{ paper: { "data-testid": backlogTestIds.documentDialog } as never }}>
			<DialogTitle>{name}</DialogTitle>
			<DialogContent dividers>
				{!document && <Typography color="text.secondary">…</Typography>}
				{document && !editing && <MarkdownView source={document.content} />}
				{document && editing && (
					<MarkdownEditor
						ariaLabel={name}
						value={draft}
						onChange={setDraft}
						onSave={save}
						onShowCurrent={() => void refetch().then((result) => setCurrent(result.data?.content ?? ""))}
						labels={{ save: t("form.save"), conflict: t("documents.conflict"), showCurrent: t("documents.showCurrent"), saveAnyway: t("documents.saveAnyway") }}
					/>
				)}
				{current !== undefined && <LargeView open onClose={() => setCurrent(undefined)} title={`${name} (${t("documents.currentState")})`} markdown={current} closeLabel={t("form.close")} tocLabel={t("documents.toc")} />}
				{document && large && <LargeView open onClose={() => setLarge(false)} title={name} markdown={document.content} closeLabel={t("form.close")} tocLabel={t("documents.toc")} />}
			</DialogContent>
			<DialogActions>
				{document && !editing && (
					<>
						<Button onClick={() => setLarge(true)} data-testid={backlogTestIds.documentLarge}>
							{t("documents.large")}
						</Button>
						{!item.deleted && (
							<Button onClick={() => setDraft(document.content)} data-testid={backlogTestIds.documentEdit}>
								{t("action.edit")}
							</Button>
						)}
					</>
				)}
				{editing && <Button onClick={() => setDraft(undefined)}>{t("form.cancel")}</Button>}
				<Button onClick={onClose}>{t("form.close")}</Button>
			</DialogActions>
		</Dialog>
	);
}

const lines = (text: string) => text.split("\n").map((line) => line.trim()).filter(Boolean);

/** A new entry in the notes: topic and one bullet per line. The first entry needs a summary of the item. */
function NoteEntryDialog({ item, onClose }: { item: ItemOut; onClose: () => void }) {
	const { t } = useTranslation("backlog");
	const [append] = useAppendNoteMutation();
	const [topic, setTopic] = useState("");
	const [discussed, setDiscussed] = useState("");
	const [decided, setDecided] = useState("");
	const [open, setOpen] = useState("");
	const [summary, setSummary] = useState(item.summary ?? "");
	const [error, setError] = useState<WriteError>();
	const needsSummary = item.notes.length === 0 && !item.summary;

	const save = async () => {
		setError(undefined);
		try {
			await append({
				uid: item.uid,
				topic,
				discussed: lines(discussed),
				decided: lines(decided),
				open: lines(open),
				summary: needsSummary ? summary : undefined,
			}).unwrap();
			onClose();
		} catch (failure) {
			setError(toWriteError(failure));
		}
	};
	const field = (name: string, label: string, value: string, set: (value: string) => void, multiline = true) => (
		<TextField
			label={label}
			value={value}
			onChange={(event) => set(event.target.value)}
			multiline={multiline}
			minRows={multiline ? 2 : undefined}
			size="small"
			helperText={multiline ? t("documents.onePerLine") : undefined}
			slotProps={{ htmlInput: { "data-testid": backlogTestIds.noteField(name) } }}
		/>
	);
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": backlogTestIds.noteDialog } as never }}>
			<DialogTitle>{t("documents.addNote")}</DialogTitle>
			<DialogContent>
				<Stack spacing={2} sx={{ pt: 1 }}>
					{field("topic", t("documents.topic"), topic, setTopic, false)}
					{field("discussed", t("documents.discussed"), discussed, setDiscussed)}
					{field("decided", t("documents.decided"), decided, setDecided)}
					{field("open", t("documents.open"), open, setOpen)}
					{needsSummary && field("summary", t("field.summary"), summary, setSummary)}
					{error && (
						<Alert severity="error" data-testid={backlogTestIds.documentError}>
							{error.message}
						</Alert>
					)}
				</Stack>
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{t("form.cancel")}</Button>
				<Button variant="contained" onClick={() => void save()} data-testid={backlogTestIds.noteSave}>
					{t("form.save")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}

/** A new spec document: its name follows the label (`<LABEL>_spec.md` or `<LABEL>_spec_<topic>.md`). */
function SpecDialog({ item, onClose, onCreated }: { item: ItemOut; onClose: () => void; onCreated: (name: string) => void }) {
	const { t } = useTranslation("backlog");
	const [put] = usePutDocumentMutation();
	const [name, setName] = useState(`${item.label}_spec.md`);
	const [error, setError] = useState<WriteError>();

	const create = async () => {
		setError(undefined);
		try {
			await put({ uid: item.uid, name: name.trim(), content: `# ${item.label} — ${item.title}\n` }).unwrap();
			onClose();
			onCreated(name.trim());
		} catch (failure) {
			setError(toWriteError(failure));
		}
	};
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm">
			<DialogTitle>{t("documents.addSpec")}</DialogTitle>
			<DialogContent>
				<TextField
					autoFocus
					fullWidth
					margin="dense"
					size="small"
					label={t("documents.specName")}
					helperText={t("documents.specNameHint", { label: item.label })}
					value={name}
					onChange={(event) => setName(event.target.value)}
					slotProps={{ htmlInput: { "data-testid": backlogTestIds.specName } }}
				/>
				{error && (
					<Alert severity="error" data-testid={backlogTestIds.documentError}>
						{error.message}
					</Alert>
				)}
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{t("form.cancel")}</Button>
				<Button variant="contained" onClick={() => void create()} data-testid={backlogTestIds.specSave}>
					{t("form.save")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}
