import type { i18n as I18n } from "i18next";
import type { RootOptions } from "react-dom/client";
import type { LogEntry } from "../logging/types";
import { coreTestIds } from "../testIds";
import type { UnhandledErrors } from "./createUnhandledErrors";
import { ErrorBoundary } from "./ErrorBoundary";
import { unhandledErrors } from "./unhandledErrors";

type RootErrorHandlers = Required<Pick<RootOptions, "onCaughtError" | "onUncaughtError" | "onRecoverableError">>;

interface RootErrorHandlersOptions {
	/** For the texts of the crash message. */
	i18n: I18n;
	/** The element React renders into; the crash message replaces its content. */
	container: HTMLElement;
	unhandled?: UnhandledErrors;
}

/**
 * Writes the message for a crash of the whole application directly into the
 * DOM: React has removed the interface, so nothing that needs React can be
 * shown. The texts fall back to German if they are not available.
 */
function showCrashMessage({ i18n, container }: RootErrorHandlersOptions, entry: LogEntry) {
	const t = (key: string, defaultValue: string) => i18n.t(key, { ns: "core", defaultValue });

	const box = document.createElement("div");
	box.dataset.testid = coreTestIds.crashMessage;
	box.setAttribute("role", "alert");
	box.style.cssText = "font-family: sans-serif; padding: 24px; max-width: 640px; margin: 0 auto;";

	const message = document.createElement("p");
	message.textContent = t("errors.crash", "Die Anwendung ist abgestürzt. Bitte laden Sie die Seite neu.");
	const errorId = document.createElement("p");
	errorId.textContent = `${t("reportError.details.errorId", "Fehler-ID")}: ${entry.id}`;
	const sessionId = document.createElement("p");
	sessionId.textContent = `${t("reportError.details.sessionId", "Sitzungs-ID")}: ${entry.sessionId}`;

	box.append(message, errorId, sessionId);
	container.replaceChildren(box);
}

/**
 * The error callbacks for `createRoot`: render errors that a boundary caught,
 * that no boundary caught, and ones React recovered from. The browser still
 * prints the default console output.
 */
export function createRootErrorHandlers(options: RootErrorHandlersOptions): RootErrorHandlers {
	const unhandled = options.unhandled ?? unhandledErrors;

	return {
		onCaughtError(error, { componentStack, errorBoundary }) {
			// Boundaries of other kinds (e.g. in the `ModalHost`) belong to the core.
			const origin = errorBoundary instanceof ErrorBoundary ? errorBoundary.props.origin : "core";
			unhandled.report(error, { origin, action: "render", data: { componentStack } });
		},

		onUncaughtError(error, { componentStack }) {
			const entry = unhandled.fatal(error, { action: "render-uncaught", data: { componentStack } });
			showCrashMessage(options, entry);
		},

		onRecoverableError(error, { componentStack }) {
			unhandled.warn(error, { action: "render-recovered", data: { componentStack } });
		},
	};
}
