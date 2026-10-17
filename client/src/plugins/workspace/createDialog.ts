import { createContext, useContext } from "react";

/** What the form of a create type gets from the dialog. */
export interface CreateDialogContext {
	/** Closes the dialog (after saving or on cancel). */
	close: () => void;
	/** The marked project, or the built-in one: where a new element goes by default. */
	projectUid: string | undefined;
}

export const CreateDialogState = createContext<CreateDialogContext | undefined>(undefined);

/** For the form a plugin hangs into `workspace.create-types`: the dialog's `close` and the default project. */
export function useCreateDialog(): CreateDialogContext {
	const value = useContext(CreateDialogState);
	if (!value) throw new Error("useCreateDialog is only available inside the create dialog");
	return value;
}
