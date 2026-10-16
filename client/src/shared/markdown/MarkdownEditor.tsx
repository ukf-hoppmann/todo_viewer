import { Alert, Box, Button, TextField } from "@mui/material";
import { useState } from "react";
import { sharedTestIds } from "../testIds";
import { MarkdownView } from "./MarkdownView";

export interface MarkdownEditorLabels {
	save: string;
	conflict: string;
	showCurrent: string;
	saveAnyway: string;
}

const defaultLabels: MarkdownEditorLabels = {
	save: "Save",
	conflict: "The document was changed in the meantime.",
	showCurrent: "Show current state",
	saveAnyway: "Save anyway",
};

interface MarkdownEditorProps {
	value: string;
	onChange: (value: string) => void;
	/** Saves; `force` is true after the user chose "Save anyway". Reject with `code: "version_conflict"` for a conflict. */
	onSave: (force: boolean) => Promise<void>;
	/** Shows the current state of the document (e.g. in a dialog); the edit stays. */
	onShowCurrent: () => void;
	labels?: Partial<MarkdownEditorLabels>;
	/** Accessible name of the text area. */
	ariaLabel: string;
}

/** An editor for markdown with the preview next to it, and the way out of a save conflict. */
export function MarkdownEditor({ value, onChange, onSave, onShowCurrent, labels, ariaLabel }: MarkdownEditorProps) {
	const text = { ...defaultLabels, ...labels };
	const [conflict, setConflict] = useState(false);
	const [saving, setSaving] = useState(false);

	const save = async (force: boolean) => {
		setSaving(true);
		try {
			await onSave(force);
			setConflict(false);
		} catch (error) {
			if (typeof error === "object" && error !== null && (error as { code?: unknown }).code === "version_conflict") setConflict(true);
			else throw error;
		} finally {
			setSaving(false);
		}
	};

	return (
		<Box data-testid={sharedTestIds.markdownEditor} sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
			{conflict && (
				<Alert
					severity="warning"
					data-testid={sharedTestIds.markdownConflict}
					action={
						<>
							<Button color="inherit" size="small" onClick={onShowCurrent} data-testid={sharedTestIds.markdownShowCurrent}>
								{text.showCurrent}
							</Button>
							<Button color="inherit" size="small" onClick={() => void save(true)} data-testid={sharedTestIds.markdownSaveAnyway}>
								{text.saveAnyway}
							</Button>
						</>
					}
				>
					{text.conflict}
				</Alert>
			)}
			<Box sx={{ display: "flex", gap: 2, alignItems: "stretch" }}>
				<TextField
					multiline
					minRows={12}
					fullWidth
					value={value}
					onChange={(event) => onChange(event.target.value)}
					slotProps={{
						htmlInput: { "aria-label": ariaLabel, "data-testid": sharedTestIds.markdownInput, style: { fontFamily: "monospace" } },
					}}
					sx={{ flex: 1, minWidth: 0 }}
				/>
				<Box data-testid={sharedTestIds.markdownPreview} sx={{ flex: 1, minWidth: 0, overflow: "auto", p: 1, border: 1, borderColor: "divider", borderRadius: 1 }}>
					<MarkdownView source={value} />
				</Box>
			</Box>
			<Box sx={{ display: "flex", justifyContent: "flex-end" }}>
				<Button variant="contained" disabled={saving || conflict} onClick={() => void save(false)} data-testid={sharedTestIds.markdownSave}>
					{text.save}
				</Button>
			</Box>
		</Box>
	);
}
