import { supportedLanguages } from "../i18n/initI18n";
import { checkContributions } from "./checkContributions";
import type { PluginDefinition } from "./types";

export type DefinitionResult = { ok: true; definition: PluginDefinition } | { ok: false; message: string };

function isObject(value: unknown): value is Record<string, unknown> {
	return typeof value === "object" && value !== null && !Array.isArray(value);
}

/**
 * The API of a plugin must be a real one with the key `<plugin id>.api`: a
 * plugin that skips `createPluginApi` or sets the key by hand could take the
 * place of another owner in the state.
 */
function checkApi(api: unknown, pluginId: string): string[] {
	if (!isObject(api)) return ["`api` is no object"];
	const problems: string[] = [];
	if (typeof api.reducerPath !== "string") problems.push("`api.reducerPath` is no string");
	else if (api.reducerPath !== `${pluginId}.api`) problems.push(`\`api.reducerPath\` is '${api.reducerPath}', expected '${pluginId}.api'`);
	if (typeof api.reducer !== "function") problems.push("`api.reducer` is no function");
	if (typeof api.middleware !== "function") problems.push("`api.middleware` is no function");
	return problems;
}

/**
 * Checks a loaded `index.ts` module at runtime: the types of `definePlugin`
 * do not reach a plugin that was built wrong. The message is English and goes
 * to the log only.
 */
export function checkDefinition(module: unknown, pluginId: string): DefinitionResult {
	if (!isObject(module)) return { ok: false, message: "the module is no object" };
	if (!("plugin" in module)) return { ok: false, message: "the export `plugin` is missing" };
	const { plugin } = module;
	if (!isObject(plugin)) return { ok: false, message: "the export `plugin` is no object" };
	if (!isObject(plugin.i18n)) return { ok: false, message: "`i18n` is missing" };

	const problems: string[] = [];
	for (const language of supportedLanguages) {
		const texts = plugin.i18n[language];
		if (texts === undefined) problems.push(`\`i18n.${language}\` is missing`);
		else if (!isObject(texts)) problems.push(`\`i18n.${language}\` is no object`);
	}
	if (plugin.reducer !== undefined && typeof plugin.reducer !== "function") problems.push("`reducer` is no function");
	if (plugin.api !== undefined) problems.push(...checkApi(plugin.api, pluginId));
	problems.push(...checkContributions(plugin.contributions));
	if (problems.length > 0) return { ok: false, message: problems.join("; ") };

	return { ok: true, definition: plugin as unknown as PluginDefinition };
}
