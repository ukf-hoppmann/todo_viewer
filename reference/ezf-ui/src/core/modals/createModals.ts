import type { ConfirmWithBodyRequest, Modals, PendingModal } from "./types";

/**
 * Creates an independent dialog queue. The core uses one instance (`modals`);
 * tests create their own. It is not bound to React: anything can enqueue
 * dialogs, the display (`ModalHost`) shows the front one.
 */
export function createModals(): Modals {
	const queue: PendingModal[] = [];
	const listeners = new Set<() => void>();
	let nextId = 1;

	const notify = () => listeners.forEach((listener) => listener());

	/** Adds a request; `settle` runs at most once, then the next one moves up. */
	function enqueue<R>(
		build: (settle: (result: R) => void, id: number) => PendingModal,
	): Promise<R> {
		return new Promise<R>((resolve) => {
			let settled = false;
			const settle = (result: R) => {
				if (settled) return;
				settled = true;
				queue.splice(queue.indexOf(pending), 1);
				resolve(result);
				notify();
			};
			const pending = build(settle, nextId++);
			queue.push(pending);
			notify();
		});
	}

	return {
		alert: (request) =>
			enqueue<void>((settle, id) => ({ id, kind: "alert", request, close: () => settle() })),

		confirm: (request) =>
			enqueue<boolean>((settle, id) => ({ id, kind: "confirm", request, answer: settle })),

		confirmWithBody: <T>(request: ConfirmWithBodyRequest<T>) =>
			enqueue<{ confirmed: boolean; data: T }>((settle, id) => ({
				id,
				kind: "confirmWithBody",
				request: request as ConfirmWithBodyRequest<unknown>,
				answer: (confirmed, data) => settle({ confirmed, data: data as T }),
			})),

		subscribe(listener) {
			listeners.add(listener);
			return () => {
				listeners.delete(listener);
			};
		},

		getSnapshot: () => queue[0],
	};
}
