import { useSyncExternalStore } from "react";
import { AlertModal } from "./AlertModal";
import { ConfirmModal } from "./ConfirmModal";
import { modals as defaultModals } from "./modals";
import type { Modals } from "./types";

interface ModalHostProps {
	/** Dialog queue to show; the standard `modals` object by default. */
	modals?: Modals;
}

/**
 * Shows the front dialog of the queue. Mounted at the top of the app so that
 * dialogs work before login and before plugins are loaded.
 */
export function ModalHost({ modals = defaultModals }: ModalHostProps) {
	const pending = useSyncExternalStore(modals.subscribe, modals.getSnapshot);

	switch (pending?.kind) {
		case "alert":
			return <AlertModal key={pending.id} request={pending.request} onClose={pending.close} />;
		case "confirm":
			return (
				<ConfirmModal key={pending.id} request={pending.request} onAnswer={(confirmed) => pending.answer(confirmed)} />
			);
		case "confirmWithBody":
			return (
				<ConfirmModal
					key={pending.id}
					request={pending.request}
					onAnswer={(confirmed, data) => pending.answer(confirmed, data)}
				/>
			);
		default:
			return null;
	}
}
