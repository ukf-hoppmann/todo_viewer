import type { ReactNode } from "react";
import type { Text } from "./text";

export type ModalSeverity = "error" | "warning" | "info" | "success";

export type ModalWidth = "xs" | "sm" | "md" | "lg" | "xl";

/** One line of the technical details of an alert, e.g. time or error id. */
export interface DetailRow {
	label: Text;
	value: string;
}

/** Fields shared by all dialogs. */
interface ModalRequest {
	/** Without it: the default title of the severity, or "Confirmation required". */
	title?: Text;
	/** Message for the user; line breaks are kept. */
	message?: Text;
	/** Default `sm`. */
	maxWidth?: ModalWidth;
}

export interface AlertRequest extends ModalRequest {
	/** Default `info`. */
	severity?: ModalSeverity;
	/** Technical details, collapsed. */
	details?: DetailRow[];
}

export interface ConfirmRequest extends ModalRequest {
	confirmText?: Text;
	cancelText?: Text;
}

export interface ConfirmBodyProps<T> {
	data: T;
	/** Replaces the data. */
	setData(data: T): void;
	/** Merges a partial object into the data. */
	updateData(patch: Partial<T>): void;
}

export interface ConfirmWithBodyRequest<T> extends ConfirmRequest {
	initialData: T;
	body: (props: ConfirmBodyProps<T>) => ReactNode;
}

export interface ConfirmWithBodyResult<T> {
	confirmed: boolean;
	/** Last state of the content, also when cancelled. */
	data: T;
}

/** The dialog that is shown now, and how to answer it. */
export type PendingModal =
	| { id: number; kind: "alert"; request: AlertRequest; close(): void }
	| { id: number; kind: "confirm"; request: ConfirmRequest; answer(confirmed: boolean): void }
	| {
			id: number;
			kind: "confirmWithBody";
			request: ConfirmWithBodyRequest<unknown>;
			answer(confirmed: boolean, data: unknown): void;
	  };

export interface Modals {
	/** Resolves when the user closes the alert. */
	alert(request: AlertRequest): Promise<void>;
	/** Resolves `true` only when the user confirms. */
	confirm(request: ConfirmRequest): Promise<boolean>;
	confirmWithBody<T>(request: ConfirmWithBodyRequest<T>): Promise<ConfirmWithBodyResult<T>>;
	/** For the display (`useSyncExternalStore`). */
	subscribe(listener: () => void): () => void;
	/** The front dialog of the queue; the same object until the queue changes. */
	getSnapshot(): PendingModal | undefined;
}
