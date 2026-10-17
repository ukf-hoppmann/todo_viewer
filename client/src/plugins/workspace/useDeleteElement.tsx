import { useCallback, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { ConfirmDialog } from "../../shared";
import { errorMessage, useDeleteElementMutation } from "./api";

/**
 * Deleting an element for the plugins that own one: `requestDelete(uid, version)` puts it into the trash. If it
 * has children the user is asked first (the question names how many), and then the element and its
 * descendants go to the trash together. The plugin renders `dialog` once anywhere in its page. `failed` holds
 * the server's message of a failed attempt (for example a version conflict).
 */
export function useDeleteElement(): {
	requestDelete: (uid: string, version: number) => Promise<void>;
	dialog: ReactNode;
	failed: string | undefined;
} {
	const { t } = useTranslation("workspace");
	const [deleteElement] = useDeleteElementMutation();
	const [asking, setAsking] = useState<{ uid: string; version: number; children: number }>();
	const [failed, setFailed] = useState<string>();

	const run = useCallback(
		async (uid: string, version: number, cascade: boolean) => {
			setFailed(undefined);
			const result = await deleteElement({ uid, version, cascade });
			if ("error" in result) setFailed(errorMessage(result.error, t("trash.failed")));
			else if (result.data.has_children) setAsking({ uid, version, children: result.data.children });
		},
		[deleteElement, t],
	);

	const dialog = (
		<ConfirmDialog
			open={asking !== undefined}
			title={t("delete.title")}
			message={t("delete.message", { count: asking?.children ?? 0 })}
			confirmLabel={t("delete.confirm")}
			cancelLabel={t("card.cancel")}
			onCancel={() => setAsking(undefined)}
			onConfirm={() => {
				const current = asking;
				setAsking(undefined);
				if (current) void run(current.uid, current.version, true);
			}}
		/>
	);

	return { requestDelete: (uid, version) => run(uid, version, false), dialog, failed };
}
