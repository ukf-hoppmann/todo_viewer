import { Button, Dialog, DialogActions, DialogContent, DialogContentText, DialogTitle } from "@mui/material";
import type { ReactNode } from "react";
import { sharedTestIds } from "../testIds";

interface ConfirmDialogProps {
	open: boolean;
	title: string;
	message: ReactNode;
	confirmLabel: string;
	cancelLabel: string;
	onConfirm: () => void;
	onCancel: () => void;
}

/** Asks for a confirmation; the texts come from the caller (it translates). */
export function ConfirmDialog({ open, title, message, confirmLabel, cancelLabel, onConfirm, onCancel }: ConfirmDialogProps) {
	return (
		<Dialog open={open} onClose={onCancel} slotProps={{ paper: { "data-testid": sharedTestIds.confirmDialog } as never }}>
			<DialogTitle>{title}</DialogTitle>
			<DialogContent>
				<DialogContentText component="div">{message}</DialogContentText>
			</DialogContent>
			<DialogActions>
				<Button onClick={onCancel} data-testid={sharedTestIds.confirmDialogCancel}>
					{cancelLabel}
				</Button>
				<Button variant="contained" onClick={onConfirm} data-testid={sharedTestIds.confirmDialogConfirm}>
					{confirmLabel}
				</Button>
			</DialogActions>
		</Dialog>
	);
}

export interface Choice<T extends string = string> {
	value: T;
	label: string;
	/** An explanation under the button. */
	description?: string;
}

interface ChoiceDialogProps<T extends string> {
	open: boolean;
	title: string;
	message?: ReactNode;
	choices: readonly Choice<T>[];
	cancelLabel: string;
	onChoose: (value: T) => void;
	onCancel: () => void;
}

/** Offers several ways to go on, e.g. "database", "file", "later" for a sync conflict. */
export function ChoiceDialog<T extends string>({ open, title, message, choices, cancelLabel, onChoose, onCancel }: ChoiceDialogProps<T>) {
	return (
		<Dialog open={open} onClose={onCancel} slotProps={{ paper: { "data-testid": sharedTestIds.choiceDialog } as never }}>
			<DialogTitle>{title}</DialogTitle>
			<DialogContent sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
				{message && <DialogContentText component="div">{message}</DialogContentText>}
				{choices.map((choice) => (
					<Button
						key={choice.value}
						variant="outlined"
						onClick={() => onChoose(choice.value)}
						data-testid={sharedTestIds.choiceDialogOption(choice.value)}
						sx={{ justifyContent: "flex-start", textAlign: "left", flexDirection: "column", alignItems: "flex-start" }}
					>
						{choice.label}
						{choice.description && (
							<DialogContentText variant="caption" component="span">
								{choice.description}
							</DialogContentText>
						)}
					</Button>
				))}
			</DialogContent>
			<DialogActions>
				<Button onClick={onCancel} data-testid={sharedTestIds.choiceDialogCancel}>
					{cancelLabel}
				</Button>
			</DialogActions>
		</Dialog>
	);
}
