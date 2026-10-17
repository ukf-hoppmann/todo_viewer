import { Alert, Box, Button } from "@mui/material";
import { useState, type FormEvent, type ReactNode } from "react";
import { sharedTestIds } from "./testIds";

export interface EditFormLabels {
	save: string;
	cancel: string;
	/** Shown when somebody else changed the element meanwhile (`version_conflict`). */
	conflict: string;
	/** The button that loads the current state. */
	reload: string;
}

const defaultLabels: EditFormLabels = {
	save: "Save",
	cancel: "Cancel",
	conflict: "The element was changed in the meantime.",
	reload: "Load current state",
};

interface EditFormProps {
	children: ReactNode;
	/** Saves; reject with an error whose `code` is `version_conflict` to offer the current state. */
	onSave: () => Promise<void>;
	onCancel: () => void;
	/** Loads the current state of the element into the form; the form keeps the edit until then. */
	onReload: () => void | Promise<void>;
	labels?: Partial<EditFormLabels>;
}

function codeOf(error: unknown): string | undefined {
	return typeof error === "object" && error !== null && "code" in error ? String((error as { code: unknown }).code) : undefined;
}

/** A form with save and cancel; a version conflict is shown with a button that loads the current state. */
export function EditForm({ children, onSave, onCancel, onReload, labels }: EditFormProps) {
	const text = { ...defaultLabels, ...labels };
	const [saving, setSaving] = useState(false);
	const [conflict, setConflict] = useState(false);
	const [error, setError] = useState<string | undefined>();

	const submit = async (event: FormEvent) => {
		event.preventDefault();
		setSaving(true);
		setError(undefined);
		try {
			await onSave();
			setConflict(false);
		} catch (failure) {
			if (codeOf(failure) === "version_conflict") setConflict(true);
			else setError(failure instanceof Error ? failure.message : String(failure));
		} finally {
			setSaving(false);
		}
	};

	return (
		<Box component="form" onSubmit={submit} data-testid={sharedTestIds.editForm} sx={{ display: "flex", flexDirection: "column", gap: 1.5 }}>
			{children}
			{conflict && (
				<Alert
					severity="warning"
					data-testid={sharedTestIds.editFormConflict}
					action={
						<Button
							color="inherit"
							size="small"
							data-testid={sharedTestIds.editFormReload}
							onClick={async () => {
								await onReload();
								setConflict(false);
							}}
						>
							{text.reload}
						</Button>
					}
				>
					{text.conflict}
				</Alert>
			)}
			{error && (
				<Alert severity="error" data-testid={sharedTestIds.editFormError}>
					{error}
				</Alert>
			)}
			<Box sx={{ display: "flex", gap: 1, justifyContent: "flex-end" }}>
				<Button type="button" onClick={onCancel} data-testid={sharedTestIds.editFormCancel}>
					{text.cancel}
				</Button>
				<Button type="submit" variant="contained" disabled={saving || conflict} data-testid={sharedTestIds.editFormSave}>
					{text.save}
				</Button>
			</Box>
		</Box>
	);
}
