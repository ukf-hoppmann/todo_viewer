import type { i18n as I18n } from "i18next";
import type { Logger } from "../logging/types";
import { checkDefinition } from "./checkDefinition";
import { checkSlots } from "./checkSlots";
import { resolvePlugins } from "./resolvePlugins";
import type { ActivePlugin, PluginCatalogue, PluginRegistry, PluginSelection, PluginStatus } from "./types";

interface PluginRegistryOptions {
	config: PluginSelection;
	catalogue: PluginCatalogue;
	i18n: I18n;
	logger: Logger;
}

/**
 * Decides, loads and registers the plugins of this start; called once by
 * `src/app`. Only plugins that may be active are loaded, in parallel, and
 * registered in topological order. A failing plugin disables only itself and
 * the plugins that require it. Throws `PluginSelectionError`
 * before loading anything if the config names a plugin that does not exist.
 */
export async function createPluginRegistry({
	config,
	catalogue,
	i18n,
	logger,
}: PluginRegistryOptions): Promise<PluginRegistry> {
	const { statuses, candidates } = resolvePlugins(config, catalogue);
	const loaded = await Promise.allSettled(candidates.map((candidate) => candidate.load()));
	const active: ActivePlugin[] = [];

	candidates.forEach(({ id, requires }, position) => {
		// Required plugins come earlier, so their status is final here.
		const failed = requires.map((other) => statuses.get(other)).find((status) => status && status.status !== "active");
		if (failed) {
			const cause = [failed.id, ...(failed.cause ?? [])];
			const message = `required plugin '${cause.at(-1)}' failed (via ${cause.join(" -> ")})`;
			statuses.set(id, { id, status: "blocked", code: "requires-failed", message, cause });
			return;
		}

		const result = loaded[position]!;
		if (result.status === "rejected") {
			statuses.set(id, { id, status: "failed", code: "import-failed", message: "importing index.ts failed", error: result.reason });
			return;
		}
		const checked = checkDefinition(result.value, id);
		if (!checked.ok) {
			statuses.set(id, { id, status: "failed", code: "definition-invalid", message: `the definition is invalid: ${checked.message}` });
			return;
		}

		const contributions = checked.definition.contributions ?? [];
		const slotProblems = checkSlots({
			id,
			requires,
			contributions,
			slots: Object.keys(checked.definition.slots ?? {}),
			registered: new Map(
				active.map((plugin) => [
					plugin.id,
					{ contributions: plugin.definition.contributions ?? [], slots: Object.keys(plugin.definition.slots ?? {}) },
				]),
			),
		});
		if (slotProblems.length > 0) {
			statuses.set(id, { id, status: "failed", code: "contribution-invalid", message: `the contributions are invalid: ${slotProblems.join("; ")}` });
			return;
		}

		const otherFrame = checked.definition.frame && active.find((plugin) => plugin.definition.frame);
		if (otherFrame) {
			statuses.set(id, {
				id,
				status: "failed",
				code: "definition-invalid",
				message: `the definition is invalid: \`frame\` is already provided by '${otherFrame.id}'`,
			});
			return;
		}

		for (const [language, texts] of Object.entries(checked.definition.i18n)) {
			i18n.addResourceBundle(language, id, texts);
		}
		active.push({ id, definition: checked.definition });
		statuses.set(id, { id, status: "active" });
	});

	const all = Object.freeze(
		[...statuses.values()]
			.sort((left, right) => left.id.localeCompare(right.id))
			.map((status) => Object.freeze(log(logger, status))),
	);
	const frozenActive = Object.freeze(active);

	return {
		active: () => frozenActive,
		statuses: () => all,
	};
}

/**
 * Failures are reported (error), plugins blocked by a failure are noted
 * (warn), the rest is debug. A reported status keeps its log entry.
 */
function log(logger: Logger, plugin: PluginStatus): PluginStatus {
	const { id, status, code, message, cause, error } = plugin;
	const reported = status === "failed" || code === "requires-failed";
	const write = status === "failed" ? logger.error : reported ? logger.warn : logger.debug;
	const entry = write({
		action: "activate-plugin",
		message: `plugin '${id}' is ${status}${message ? `: ${message}` : ""}`,
		data: { plugin: id, status, code, cause },
		error,
	});
	return reported ? { ...plugin, logEntry: entry } : plugin;
}
