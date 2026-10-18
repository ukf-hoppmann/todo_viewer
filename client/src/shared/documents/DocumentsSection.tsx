import CloseIcon from "@mui/icons-material/Close";
import DescriptionIcon from "@mui/icons-material/Description";
import EditIcon from "@mui/icons-material/Edit";
import NoteAddIcon from "@mui/icons-material/NoteAdd";
import OpenInFullIcon from "@mui/icons-material/OpenInFull";
import PostAddIcon from "@mui/icons-material/PostAdd";
import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Stack, TextField, Typography } from "@mui/material";
import { useState } from "react";
import { IconAction } from "../IconAction";
import { LargeView } from "../markdown/LargeView";
import { MarkdownEditor } from "../markdown/MarkdownEditor";
import { MarkdownView } from "../markdown/MarkdownView";
import { sharedTestIds as ids } from "../testIds";

export interface StoredDocument {
	content: string;
	version: number;
}

/** A new entry in the notes document: topic and one bullet per line in each list. */
export interface NotesEntry {
	topic: string;
	discussed: string[];
	decided: string[];
	open: string[];
	summary?: string;
}

export interface DocumentsLabels {
	none: string;
	addEntry: string;
	addSpec: string;
	large: string;
	edit: string;
	close: string;
	cancel: string;
	save: string;
	topic: string;
	discussed: string;
	decided: string;
	open: string;
	onePerLine: string;
	summary: string;
	specName: string;
	specNameHint: string;
	conflict: string;
	showCurrent: string;
	saveAnyway: string;
	currentState: string;
	toc: string;
}

export interface DocumentsSectionProps {
	/** Uid of the element the documents belong to; passed to `useDocument`. */
	owner: string;
	names: string[];
	/** No adding and no editing (e.g. an element in the trash). */
	readOnly: boolean;
	/** Proposed name and first line of a new spec. */
	spec: { name: string; content: string };
	/** When set, the entry dialog asks for a summary with this initial value. */
	summary?: string;
	/** The owner's query hook for one document. */
	useDocument: (owner: string, name: string) => { document?: StoredDocument; refetch: () => Promise<StoredDocument | undefined> };
	/** Writes a document; without `version` it is created. Rejects with `code: "version_conflict"` for a conflict. */
	saveDocument: (name: string, content: string, version?: number) => Promise<StoredDocument>;
	appendEntry: (entry: NotesEntry) => Promise<void>;
	/** The message to show for a refused write. */
	errorMessage: (failure: unknown) => string;
	labels: DocumentsLabels;
}

/** The section "Documents" of a detail panel: the notes and specs of an element, and the actions to add to them. */
export function DocumentsSection(props: DocumentsSectionProps) {
	const { names, readOnly, labels } = props;
	const [open, setOpen] = useState<string>();
	const [dialog, setDialog] = useState<"entry" | "spec">();

	return (
		<Stack spacing={1} data-testid={ids.documents}>
			{names.length === 0 && (
				<Typography variant="body2" color="text.secondary">
					{labels.none}
				</Typography>
			)}
			{names.map((name) => (
				<Button
					key={name}
					size="small"
					startIcon={<DescriptionIcon />}
					onClick={() => setOpen(name)}
					data-testid={ids.document(name)}
					sx={{ justifyContent: "flex-start", textTransform: "none" }}
				>
					{name}
				</Button>
			))}
			{!readOnly && (
				<Box sx={{ display: "flex", gap: 0.5 }}>
					<IconAction label={labels.addEntry} icon={NoteAddIcon} onClick={() => setDialog("entry")} testId={ids.documentsAddEntry} />
					<IconAction label={labels.addSpec} icon={PostAddIcon} onClick={() => setDialog("spec")} testId={ids.documentsAddSpec} />
				</Box>
			)}
			{open && <DocumentDialog {...props} name={open} onClose={() => setOpen(undefined)} />}
			{dialog === "entry" && <EntryDialog {...props} onClose={() => setDialog(undefined)} />}
			{dialog === "spec" && <SpecDialog {...props} onClose={() => setDialog(undefined)} onCreated={setOpen} />}
		</Stack>
	);
}

/** A document: the formatted text, and "Edit" with the editor, its preview and the way out of a conflict. */
function DocumentDialog({ owner, name, readOnly, useDocument, saveDocument, labels, onClose }: DocumentsSectionProps & { name: string; onClose: () => void }) {
	const { document, refetch } = useDocument(owner, name);
	const [draft, setDraft] = useState<string>();
	const [large, setLarge] = useState(false);
	const [current, setCurrent] = useState<string>();
	const [version, setVersion] = useState<number>();
	const editing = draft !== undefined;

	const save = async (force: boolean) => {
		if (!document || draft === undefined) return;
		let base = version ?? document.version;
		if (force) base = (await refetch())?.version ?? base;
		const saved = await saveDocument(name, draft, base);
		setVersion(saved.version);
		setDraft(undefined);
	};

	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="md" slotProps={{ paper: { "data-testid": ids.documentDialog } as never }}>
			<DialogTitle sx={{ display: "flex", alignItems: "center", gap: 0.5, pr: 1.5 }}>
				<Box component="span" sx={{ flexGrow: 1, minWidth: 0, overflowWrap: "anywhere" }}>
					{name}
				</Box>
				{document && !editing && <IconAction label={labels.large} icon={OpenInFullIcon} onClick={() => setLarge(true)} testId={ids.documentLarge} />}
				{document && !editing && !readOnly && <IconAction label={labels.edit} icon={EditIcon} onClick={() => setDraft(document.content)} testId={ids.documentEdit} />}
				<IconAction label={labels.close} icon={CloseIcon} onClick={onClose} testId={ids.documentClose} />
			</DialogTitle>
			<DialogContent dividers>
				{!document && <Typography color="text.secondary">…</Typography>}
				{document && !editing && <MarkdownView source={document.content} />}
				{document && editing && (
					<MarkdownEditor
						ariaLabel={name}
						value={draft}
						onChange={setDraft}
						onSave={save}
						onShowCurrent={() => void refetch().then((result) => setCurrent(result?.content ?? ""))}
						labels={{ save: labels.save, conflict: labels.conflict, showCurrent: labels.showCurrent, saveAnyway: labels.saveAnyway }}
					/>
				)}
				{current !== undefined && <LargeView open onClose={() => setCurrent(undefined)} title={`${name} (${labels.currentState})`} markdown={current} closeLabel={labels.close} tocLabel={labels.toc} />}
				{document && large && <LargeView open onClose={() => setLarge(false)} title={name} markdown={document.content} closeLabel={labels.close} tocLabel={labels.toc} />}
			</DialogContent>
			{editing && (
				<DialogActions>
					<Button onClick={() => setDraft(undefined)} data-testid={ids.documentCancel}>
						{labels.cancel}
					</Button>
				</DialogActions>
			)}
		</Dialog>
	);
}

const lines = (text: string) => text.split("\n").map((line) => line.trim()).filter(Boolean);

/** A new entry in the notes: topic and one bullet per line, and the summary of the element when it is asked for. */
function EntryDialog({ summary: initialSummary, appendEntry, errorMessage, labels, onClose }: DocumentsSectionProps & { onClose: () => void }) {
	const [topic, setTopic] = useState("");
	const [discussed, setDiscussed] = useState("");
	const [decided, setDecided] = useState("");
	const [open, setOpen] = useState("");
	const [summary, setSummary] = useState(initialSummary ?? "");
	const [error, setError] = useState<string>();
	const needsSummary = initialSummary !== undefined;

	const save = async () => {
		setError(undefined);
		try {
			await appendEntry({
				topic,
				discussed: lines(discussed),
				decided: lines(decided),
				open: lines(open),
				...(needsSummary ? { summary } : {}),
			});
			onClose();
		} catch (failure) {
			setError(errorMessage(failure));
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
			helperText={multiline ? labels.onePerLine : undefined}
			slotProps={{ htmlInput: { "data-testid": ids.entryField(name) } }}
		/>
	);
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": ids.entryDialog } as never }}>
			<DialogTitle>{labels.addEntry}</DialogTitle>
			<DialogContent>
				<Stack spacing={2} sx={{ pt: 1 }}>
					{field("topic", labels.topic, topic, setTopic, false)}
					{field("discussed", labels.discussed, discussed, setDiscussed)}
					{field("decided", labels.decided, decided, setDecided)}
					{field("open", labels.open, open, setOpen)}
					{needsSummary && field("summary", labels.summary, summary, setSummary)}
					{error && (
						<Alert severity="error" data-testid={ids.documentError}>
							{error}
						</Alert>
					)}
				</Stack>
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{labels.cancel}</Button>
				<Button variant="contained" onClick={() => void save()} data-testid={ids.entrySave}>
					{labels.save}
				</Button>
			</DialogActions>
		</Dialog>
	);
}

/** A new spec document under the proposed name, opened right after it was created. */
function SpecDialog({ spec, saveDocument, errorMessage, labels, onClose, onCreated }: DocumentsSectionProps & { onClose: () => void; onCreated: (name: string) => void }) {
	const [name, setName] = useState(spec.name);
	const [error, setError] = useState<string>();

	const create = async () => {
		setError(undefined);
		try {
			await saveDocument(name.trim(), spec.content);
			onClose();
			onCreated(name.trim());
		} catch (failure) {
			setError(errorMessage(failure));
		}
	};
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm">
			<DialogTitle>{labels.addSpec}</DialogTitle>
			<DialogContent>
				<TextField
					autoFocus
					fullWidth
					margin="dense"
					size="small"
					label={labels.specName}
					helperText={labels.specNameHint}
					value={name}
					onChange={(event) => setName(event.target.value)}
					slotProps={{ htmlInput: { "data-testid": ids.specName } }}
				/>
				{error && (
					<Alert severity="error" data-testid={ids.documentError}>
						{error}
					</Alert>
				)}
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{labels.cancel}</Button>
				<Button variant="contained" onClick={() => void create()} data-testid={ids.specSave}>
					{labels.save}
				</Button>
			</DialogActions>
		</Dialog>
	);
}
