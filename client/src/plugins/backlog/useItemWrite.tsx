import { useCallback, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { ConfirmDialog } from "../../shared";
import {
	toWriteError,
	useCreateItemMutation,
	useMoveItemMutation,
	useReopenAncestorsMutation,
	useRetypeItemMutation,
	useUpdateItemMutation,
	type ItemOut,
	type RetypeOut,
} from "./api";

type Ancestor = { uid: string; label: string };

/**
 * The writes of the backlog (create, change, move, change type) as promises that reject with a `WriteError`.
 * If a write fails because the new place is below a closed parent (`parent_closed`), the user is asked once
 * whether to reopen the closed ancestors; after a yes they are reopened and the write is tried again. The
 * component that uses this renders `dialog` once.
 */
export function useItemWrite() {
	const { t } = useTranslation("backlog");
	const [create] = useCreateItemMutation();
	const [update] = useUpdateItemMutation();
	const [move] = useMoveItemMutation();
	const [retype] = useRetypeItemMutation();
	const [reopen] = useReopenAncestorsMutation();
	const [asking, setAsking] = useState<{ ancestors: Ancestor[]; answer: (reopen: boolean) => void }>();

	/** Runs `action`; on `parent_closed` asks to reopen, then runs it once more. */
	const withReopen = useCallback(
		async <T,>(action: () => Promise<T>): Promise<T> => {
			try {
				return await action();
			} catch (failure) {
				const error = toWriteError(failure);
				const ancestors = (error.details.ancestors as Ancestor[] | undefined) ?? [];
				if (error.code !== "parent_closed" || ancestors.length === 0) throw error;
				const yes = await new Promise<boolean>((resolve) => setAsking({ ancestors, answer: resolve }));
				setAsking(undefined);
				if (!yes) throw error;
				try {
					await reopen(ancestors[ancestors.length - 1]!.uid).unwrap();
				} catch (reopenFailure) {
					throw toWriteError(reopenFailure);
				}
				return action();
			}
		},
		[reopen],
	);

	const run = useCallback(
		async <T,>(action: () => Promise<T>): Promise<T> => {
			try {
				return await withReopen(action);
			} catch (failure) {
				throw toWriteError(failure);
			}
		},
		[withReopen],
	);

	const dialog: ReactNode = (
		<ConfirmDialog
			open={asking !== undefined}
			title={t("reopen.title")}
			message={t("reopen.message", { items: asking?.ancestors.map((a) => a.label).join(", ") })}
			confirmLabel={t("reopen.confirm")}
			cancelLabel={t("form.cancel")}
			onCancel={() => asking?.answer(false)}
			onConfirm={() => asking?.answer(true)}
		/>
	);

	return {
		dialog,
		createItem: (project: string, type: string, fields: Record<string, unknown>): Promise<ItemOut> =>
			run(() => create({ project, type, fields }).unwrap()),
		updateItem: (item: Pick<ItemOut, "uid" | "version">, fields: Record<string, unknown>, resolution?: string): Promise<ItemOut> =>
			run(() => update({ uid: item.uid, version: item.version, fields, resolution }).unwrap()),
		moveItem: (item: { uid: string; version: number }, parent: string | null, position: number): Promise<ItemOut> =>
			run(() => move({ uid: item.uid, version: item.version, parent, position }).unwrap()),
		retypeItem: (item: Pick<ItemOut, "uid" | "version">, type: string): Promise<RetypeOut> =>
			run(() => retype({ uid: item.uid, version: item.version, type }).unwrap()),
	};
}
