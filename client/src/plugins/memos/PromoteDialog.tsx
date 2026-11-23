import { Alert, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField } from "@mui/material";
import { useState, type FormEvent } from "react";
import { useTranslation } from "react-i18next";
import { toWriteError, useDecideHintMutation, usePromoteMemoMutation, type MemoOut, type WriteError } from "./api";
import { memosTestIds } from "./testIds";

const TYPES = ["Epic", "Story", "Task"] as const;

interface Props {
	memo: Pick<MemoOut, "uid" | "label" | "summary" | "version">;
	/** The hint this promotion decides (the decision `promote`); without it the memo is promoted on its own. */
	hintUid?: string;
	onClose: () => void;
}

/**
 * Promotes a memo to an item: the type and the fields the backlog requires (goal, completion criteria);
 * the title is the summary of the memo unless another is given. The server refuses what the backlog refuses and
 * the message stays in the dialog.
 */
export function PromoteDialog({ memo, hintUid, onClose }: Props) {
	const { t } = useTranslation("memos");
	const [promote] = usePromoteMemoMutation();
	const [decide] = useDecideHintMutation();
	const [type, setType] = useState<(typeof TYPES)[number]>("Task");
	const [title, setTitle] = useState("");
	const [goal, setGoal] = useState("");
	const [criteria, setCriteria] = useState("");
	const [error, setError] = useState<WriteError>();

	const submit = async (event: FormEvent) => {
		event.preventDefault();
		setError(undefined);
		const fields: Record<string, unknown> = { goal, completion_criteria: criteria };
		if (title.trim()) fields.title = title;
		try {
			if (hintUid) await decide({ uid: hintUid, decision: "promote", version: memo.version, type, fields }).unwrap();
			else await promote({ uid: memo.uid, version: memo.version, type, fields }).unwrap();
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
			slotProps={{ htmlInput: { "data-testid": memosTestIds.promoteField(name) } }}
		/>
	);
	return (
		<Dialog open onClose={onClose} fullWidth maxWidth="sm" slotProps={{ paper: { component: "form", onSubmit: submit, "data-testid": memosTestIds.promoteDialog } as never }}>
			<DialogTitle>{t("promote.title", { label: memo.label })}</DialogTitle>
			<DialogContent>
				<Stack spacing={2} sx={{ pt: 1 }}>
					<TextField select size="small" label={t("promote.type")} value={type} onChange={(event) => setType(event.target.value as typeof type)} slotProps={{ htmlInput: { "data-testid": memosTestIds.promoteField("type") } }}>
						{TYPES.map((value) => (
							<MenuItem key={value} value={value}>
								{value}
							</MenuItem>
						))}
					</TextField>
					{field("title", t("promote.itemTitle"), title, setTitle, { placeholder: memo.summary })}
					{field("goal", t("promote.goal"), goal, setGoal, { required: true, multiline: true })}
					{field("completion_criteria", t("promote.criteria"), criteria, setCriteria, { required: true, multiline: true })}
					<Alert severity="info">{t("promote.hint")}</Alert>
					{error && (
						<Alert severity="error" data-testid={memosTestIds.promoteError}>
							{error.message}
						</Alert>
					)}
				</Stack>
			</DialogContent>
			<DialogActions>
				<Button onClick={onClose}>{t("form.cancel")}</Button>
				<Button type="submit" variant="contained" data-testid={memosTestIds.promoteConfirm}>
					{t("promote.confirm")}
				</Button>
			</DialogActions>
		</Dialog>
	);
}
