import { Box, Checkbox, FormControl, FormHelperText, InputLabel, ListItemText, MenuItem, Select, TextField } from "@mui/material";
import { useState } from "react";
import { sharedTestIds } from "./testIds";

export interface FieldOption {
	value: string;
	label: string;
}

type Common = {
	/** Names the field in the test ids and in the form. */
	id: string;
	label: string;
	/** Saves the value; a rejection shows its message at the field and keeps the edit. */
	onSave: (value: never) => Promise<void> | void;
	disabled?: boolean;
};

export type InlineFieldProps =
	| (Common & { kind: "text"; value: string; onSave: (value: string) => Promise<void> | void; multiline?: boolean })
	| (Common & { kind: "select"; value: string; options: readonly FieldOption[]; onSave: (value: string) => Promise<void> | void })
	| (Common & { kind: "multiselect"; value: readonly string[]; options: readonly FieldOption[]; onSave: (value: string[]) => Promise<void> | void });

function messageOf(error: unknown): string {
	if (error instanceof Error) return error.message;
	if (typeof error === "object" && error !== null && "message" in error) return String((error as { message: unknown }).message);
	return String(error);
}

/**
 * A field that saves at once: a text on leaving it (or Enter), a choice as soon as it changes. A failed save
 * shows the message under the field and leaves the edit as it is, so nothing the user typed is lost.
 */
export function InlineField(props: InlineFieldProps) {
	const { id, label, disabled } = props;
	// What the user is typing; nothing while the field shows the stored value.
	const [draft, setDraft] = useState<string | undefined>();
	const [error, setError] = useState<string | undefined>();
	const [saving, setSaving] = useState(false);
	const value = props.value;
	/** Runs the save; true if it worked. A failure shows its message and keeps the edit. */
	const run = async (action: () => Promise<void> | void): Promise<boolean> => {
		setSaving(true);
		try {
			await action();
			setError(undefined);
			return true;
		} catch (failure) {
			setError(messageOf(failure));
			return false;
		} finally {
			setSaving(false);
		}
	};

	const errorText = error && (
		<FormHelperText error data-testid={sharedTestIds.inlineFieldError(id)}>
			{error}
		</FormHelperText>
	);

	if (props.kind === "text") {
		const { onSave, multiline } = props;
		const shown = draft ?? props.value;
		const commit = () => {
			if (draft === undefined) return;
			if (draft === props.value) setDraft(undefined);
			else void run(() => onSave(draft)).then((saved) => saved && setDraft((current) => (current === draft ? undefined : current)));
		};
		return (
			<Box data-testid={sharedTestIds.inlineField(id)}>
				<TextField
					size="small"
					fullWidth
					label={label}
					value={shown}
					multiline={multiline}
					disabled={disabled || saving}
					error={Boolean(error)}
					onChange={(event) => setDraft(event.target.value)}
					onBlur={commit}
					onKeyDown={(event) => {
						if (event.key === "Enter" && !multiline) commit();
						if (event.key === "Escape") {
							setDraft(undefined);
							setError(undefined);
						}
					}}
					slotProps={{ htmlInput: { "data-testid": sharedTestIds.inlineFieldInput(id) } }}
				/>
				{errorText}
			</Box>
		);
	}

	const options = props.options;
	const labelId = `inline-field-${id}`;
	const multiple = props.kind === "multiselect";
	return (
		<Box data-testid={sharedTestIds.inlineField(id)}>
			<FormControl size="small" fullWidth disabled={disabled || saving} error={Boolean(error)}>
				<InputLabel id={labelId}>{label}</InputLabel>
				<Select
					labelId={labelId}
					label={label}
					multiple={multiple}
					value={multiple ? [...(value as readonly string[])] : (value as string)}
					renderValue={(selected) =>
						(Array.isArray(selected) ? selected : [selected])
							.map((entry) => options.find((option) => option.value === entry)?.label ?? entry)
							.join(", ")
					}
					onChange={(event) => {
						const next = event.target.value;
						if (props.kind === "multiselect") void run(() => props.onSave(typeof next === "string" ? next.split(",") : next));
						else void run(() => props.onSave(next as string));
					}}
					SelectDisplayProps={{ "data-testid": sharedTestIds.inlineFieldInput(id) } as never}
				>
					{options.map((option) => (
						<MenuItem key={option.value} value={option.value} data-testid={`${sharedTestIds.inlineFieldInput(id)}.${option.value}`}>
							{multiple && <Checkbox checked={(value as readonly string[]).includes(option.value)} size="small" />}
							<ListItemText primary={option.label} />
						</MenuItem>
					))}
				</Select>
				{errorText}
			</FormControl>
		</Box>
	);
}
