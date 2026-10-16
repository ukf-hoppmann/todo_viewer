import { Button, Dialog, DialogActions, DialogContent, DialogTitle, TextField } from "@mui/material";
import { useState } from "react";
import { backlogTestIds } from "./testIds";

interface Props {
	title: string;
	label: string;
	initial?: string;
	multiline?: boolean;
	confirmLabel: string;
	cancelLabel: string;
	/** Called with the trimmed text; a rejection shows its message under the field and keeps the dialog. */
	onSubmit: (text: string) => void | Promise<void>;
	onCancel: () => void;
	testId?: string;
}

/** Asks for one text (a resolution, the name of a new area). Confirming needs a non-empty text. */
export function TextPromptDialog({ title, label, initial = "", multiline, confirmLabel, cancelLabel, onSubmit, onCancel, testId }: Props) {
	const [text, setText] = useState(initial);
	const [error, setError] = useState<string>();
	const submit = async () => {
		try {
			await onSubmit(text.trim());
		} catch (failure) {
			setError(failure instanceof Error ? failure.message : String(failure));
		}
	};
	return (
		<Dialog open onClose={onCancel} fullWidth maxWidth="sm" slotProps={{ paper: { "data-testid": testId ?? backlogTestIds.resolutionDialog } as never }}>
			<DialogTitle>{title}</DialogTitle>
			<DialogContent>
				<TextField
					autoFocus
					fullWidth
					margin="dense"
					size="small"
					label={label}
					value={text}
					multiline={multiline}
					onChange={(event) => setText(event.target.value)}
					error={Boolean(error)}
					helperText={error}
					slotProps={{ htmlInput: { "data-testid": backlogTestIds.resolutionInput } }}
				/>
			</DialogContent>
			<DialogActions>
				<Button onClick={onCancel}>{cancelLabel}</Button>
				<Button variant="contained" disabled={text.trim() === ""} onClick={() => void submit()} data-testid={backlogTestIds.resolutionConfirm}>
					{confirmLabel}
				</Button>
			</DialogActions>
		</Dialog>
	);
}
