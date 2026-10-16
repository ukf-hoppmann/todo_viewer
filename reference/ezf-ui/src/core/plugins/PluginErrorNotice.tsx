import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import { modals as defaultModals } from "../modals/modals";
import type { DetailRow, Modals } from "../modals/types";
import type { PluginStatus } from "./types";
import { usePluginRegistry } from "./usePluginRegistry";

interface PluginErrorNoticeProps {
	/** Dialog queue; the standard `modals` object by default. */
	modals?: Modals;
}

/** Plugins blocked because of the failed plugin `id`. */
function affectedBy(id: string, statuses: readonly PluginStatus[]): string[] {
	return statuses
		.filter((status) => status.code === "requires-failed" && status.cause?.at(-1) === id)
		.map((status) => status.id);
}

/**
 * Tells the user once after the start which plugins failed and which plugins
 * are missing because of that: one alert for all failures. Switched-off
 * plugins are no error and are not shown. The registry has logged each
 * failure already; this is only the hint for the user.
 */
export function PluginErrorNotice({ modals = defaultModals }: PluginErrorNoticeProps) {
	const registry = usePluginRegistry();
	const { t } = useTranslation("core");
	// StrictMode runs effects twice; the alert must appear only once.
	const shown = useRef(false);

	useEffect(() => {
		if (shown.current) return;
		const statuses = registry.statuses();
		const failed = statuses.filter((status) => status.status === "failed");
		if (failed.length === 0) return;
		shown.current = true;

		const list = failed
			.map(({ id }) => {
				const affected = affectedBy(id, statuses);
				return affected.length > 0 ? t("plugins.failedWithAffected", { plugin: id, affected: affected.join(", ") }) : id;
			})
			.map((line) => `• ${line}`)
			.join("\n");

		// Per plugin its reason and the id of its log entry; the session id is the same for all.
		const details: DetailRow[] = failed.flatMap(({ id, code, message, logEntry }) => [
			{ label: { key: "plugins.detailsPlugin", params: { plugin: id } }, value: `${code}: ${message}` },
			...(logEntry ? [{ label: { key: "reportError.details.errorId" }, value: logEntry.id }] : []),
		]);
		const sessionId = failed.find((status) => status.logEntry)?.logEntry?.sessionId;
		if (sessionId) details.push({ label: { key: "reportError.details.sessionId" }, value: sessionId });

		void modals.alert({ severity: "error", message: t("plugins.failed", { list }), details });
	}, [registry, modals, t]);

	return null;
}
