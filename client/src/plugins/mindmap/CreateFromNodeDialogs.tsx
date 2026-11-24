import { Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, TextField } from "@mui/material";
import { useState, type FormEvent, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { PRIORITIES, TYPES } from "../backlog";
import { errorMessage, useCreateItemAtNodeMutation, useCreateMemoAtNodeMutation, type NodeOut } from "./api";
import { mindmapTestIds } from "./testIds";

interface Props {
	/** The node the item or memo is made from; its title and text are the suggestion. */
	node: NodeOut;
	onClose: () => void;
}

type Kind = "item" | "memo";

/** The frame of both dialogs: the form, the error of the server (the dialog stays open and keeps the input) and the buttons. */
function CreateDialog({ kind, title, valid, busy, error, onSubmit, onClose, children }: {
	kind: Kind;
	title: string;
	valid: boolean;
	busy: boolean;
	error: string | undefined;
	onSubmit: () => void;
	onClose: () => void;
	children: ReactNode;
}) {
	const { t } = useTranslation("mindmap");
	const submit = (event: FormEvent) => {
		event.preventDefault();
		if (valid && !busy) onSubmit();
	};
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm" data-testid={mindmapTestIds.createDialog(kind)}>
			<Box component="form" onSubmit={submit}>
				<DialogTitle>{title}</DialogTitle>
				<DialogContent sx={{ display: "flex", flexDirection: "column", gap: 1.5, pt: "8px !important" }}>
					{children}
					{error && (
						<Alert severity="error" data-testid={mindmapTestIds.createError(kind)}>
							{error}
						</Alert>
					)}
				</DialogContent>
				<DialogActions>
					<Button type="button" onClick={onClose} data-testid={mindmapTestIds.createCancel(kind)}>
						{t("form.cancel")}
					</Button>
					<Button type="submit" variant="contained" disabled={!valid || busy} data-testid={mindmapTestIds.createConfirm(kind)}>
						{t(`create.${kind}.confirm`)}
					</Button>
				</DialogActions>
			</Box>
		</Dialog>
	);
}

const field = (kind: Kind, name: string) => ({ htmlInput: { "data-testid": mindmapTestIds.createField(kind, name) } });

/**
 * "Item anlegen": the dialog for a new backlog item made from a node. Title and goal are the title and text of the node
 * (a suggestion to change); the type has no default because the person (or the AI) decides it per node; the completion
 * criteria are required and start empty because a node has none. The priority starts at "Normal". The server hangs the
 * item on the node; its error stays in the dialog with the input.
 */
export function ItemFromNodeDialog({ node, onClose }: Props) {
	const { t } = useTranslation("mindmap");
	const [createItem] = useCreateItemAtNodeMutation();
	const [type, setType] = useState("");
	const [title, setTitle] = useState(node.title);
	const [priority, setPriority] = useState("Normal");
	const [goal, setGoal] = useState(node.text ?? "");
	const [criteria, setCriteria] = useState("");
	const [error, setError] = useState<string>();
	const [busy, setBusy] = useState(false);

	const submit = async () => {
		setError(undefined);
		setBusy(true);
		const fields: Record<string, unknown> = { title: title.trim(), priority, completion_criteria: criteria };
		if (goal.trim()) fields.goal = goal;
		try {
			await createItem({ node: node.uid, type, fields }).unwrap();
			onClose();
		} catch (failure) {
			setError(errorMessage(failure, t("error.failed")));
			setBusy(false);
		}
	};
	return (
		<CreateDialog kind="item" title={t("create.item.title", { title: node.title })} valid={type !== "" && title.trim() !== "" && criteria.trim() !== ""} busy={busy} error={error} onSubmit={() => void submit()} onClose={onClose}>
			<TextField select required size="small" label={t("create.item.type")} value={type} onChange={(event) => setType(event.target.value)} slotProps={field("item", "type")}>
				{TYPES.map((value) => (
					<MenuItem key={value} value={value}>
						{t(`create.item.types.${value}`)}
					</MenuItem>
				))}
			</TextField>
			<TextField required autoFocus size="small" label={t("field.title")} value={title} onChange={(event) => setTitle(event.target.value)} slotProps={field("item", "title")} />
			<TextField select size="small" label={t("create.item.priority")} value={priority} onChange={(event) => setPriority(event.target.value)} slotProps={field("item", "priority")}>
				{PRIORITIES.map((value) => (
					<MenuItem key={value} value={value}>
						{t(`create.item.priorities.${value}`)}
					</MenuItem>
				))}
			</TextField>
			<TextField multiline minRows={2} size="small" label={t("create.item.goal")} value={goal} onChange={(event) => setGoal(event.target.value)} slotProps={field("item", "goal")} />
			<TextField required multiline minRows={2} size="small" label={t("create.item.criteria")} value={criteria} onChange={(event) => setCriteria(event.target.value)} slotProps={field("item", "completion_criteria")} />
		</CreateDialog>
	);
}

/**
 * "Memo anlegen": the dialog for a new memo made from a node. The summary is the title of the node, the text is the text
 * of the node (both to change). The server links the memo with the node; a memo does not change the state of the node.
 */
export function MemoFromNodeDialog({ node, onClose }: Props) {
	const { t } = useTranslation("mindmap");
	const [createMemo] = useCreateMemoAtNodeMutation();
	const [summary, setSummary] = useState(node.title);
	const [body, setBody] = useState(node.text ?? "");
	const [error, setError] = useState<string>();
	const [busy, setBusy] = useState(false);

	const submit = async () => {
		setError(undefined);
		setBusy(true);
		const fields: Record<string, unknown> = { summary: summary.trim() };
		if (body.trim()) fields.body = body;
		try {
			await createMemo({ node: node.uid, fields }).unwrap();
			onClose();
		} catch (failure) {
			setError(errorMessage(failure, t("error.failed")));
			setBusy(false);
		}
	};
	return (
		<CreateDialog kind="memo" title={t("create.memo.title", { title: node.title })} valid={summary.trim() !== ""} busy={busy} error={error} onSubmit={() => void submit()} onClose={onClose}>
			<TextField required autoFocus size="small" label={t("create.memo.summary")} value={summary} onChange={(event) => setSummary(event.target.value)} slotProps={field("memo", "summary")} />
			<TextField multiline minRows={3} size="small" label={t("create.memo.body")} value={body} onChange={(event) => setBody(event.target.value)} slotProps={field("memo", "body")} />
		</CreateDialog>
	);
}
