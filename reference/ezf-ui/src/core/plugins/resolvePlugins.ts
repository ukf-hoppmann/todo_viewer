import { ConfigError } from "../config/ConfigError";
import type { PluginSelection } from "../config/types";
import type { PluginCatalogue, PluginStatus } from "./types";
import { validatePluginManifest } from "./validatePluginManifest";

const kebabCase = /^[a-z0-9]+(-[a-z0-9]+)*$/;

/** Ids no plugin may have: `core` is the owner of the core, `dev` the prefix of development routes. */
const reservedIds = ["core", "dev"];

/** A plugin that may be loaded: all it requires is a candidate as well. */
export interface PluginCandidate {
	id: string;
	requires: string[];
	load: () => Promise<unknown>;
}

export interface Resolution {
	/** Every plugin that is not a candidate. */
	statuses: Map<string, PluginStatus>;
	/** In topological order of `requires`: each one after the plugins it requires. */
	candidates: PluginCandidate[];
}

type Blocked = { code: "requires-failed" | "requires-disabled"; cause: string[] };

/**
 * Decides from config and manifests alone which plugins are loaded
 * (architecture rule 3.5); no plugin code runs here. Throws `ConfigError`
 * (`config-unknown-plugin`) if the config names a plugin that does not exist.
 */
export function resolvePlugins(config: PluginSelection, catalogue: PluginCatalogue): Resolution {
	const unknown = Object.keys(config.plugins).filter((id) => !Object.hasOwn(catalogue, id));
	if (unknown.length > 0) {
		throw new ConfigError(
			"config-unknown-plugin",
			"the plugin selection names plugins that do not exist",
			unknown.map((id) => ({ path: `/plugins/${id}`, message: "no plugin with this id exists" })),
		);
	}

	const ids = Object.keys(catalogue).sort();
	const statuses = new Map<string, PluginStatus>();
	const requires = new Map<string, string[]>();
	const fail = (id: string, code: PluginStatus["code"], message: string) =>
		statuses.set(id, { id, status: "failed", code, message });

	// The plugin itself: id, manifest, definition file.
	for (const id of ids) {
		const { manifest, load } = catalogue[id]!;
		const checked = validatePluginManifest(manifest);
		if (!kebabCase.test(id)) fail(id, "id-invalid", `the folder name '${id}' is not kebab-case`);
		else if (reservedIds.includes(id)) fail(id, "id-invalid", `the folder name '${id}' is reserved`);
		else if (!checked.ok) fail(id, "manifest-invalid", `plugin.json is missing or invalid: ${checked.message}`);
		else if (!load) fail(id, "definition-missing", "index.ts is missing");
		if (checked.ok) requires.set(id, checked.manifest.requires);
	}

	for (const [id, required] of requires) {
		const missing = required.filter((other) => !Object.hasOwn(catalogue, other));
		if (missing.length > 0 && !statuses.has(id)) {
			fail(id, "requires-unknown", `requires plugins that do not exist: ${missing.join(", ")}`);
		}
	}

	for (const cycle of findCycles(requires)) {
		for (const id of cycle) {
			if (!statuses.has(id)) fail(id, "requires-cycle", `requires forms a cycle: ${cycle.join(" -> ")}`);
		}
	}

	for (const id of ids) {
		if (!statuses.has(id) && !config.plugins[id]?.enabled) statuses.set(id, { id, status: "disabled" });
	}

	// Remaining plugins: blocked by what they require, or candidates. Failed
	// and disabled plugins end every walk, so no cycle is entered here.
	const blocked = new Map<string, Blocked | undefined>();
	const candidates: PluginCandidate[] = [];

	function visit(id: string): Blocked | undefined {
		if (blocked.has(id)) return blocked.get(id);
		const status = statuses.get(id);
		if (status?.status === "failed") return { code: "requires-failed", cause: [] };
		if (status?.status === "disabled") return { code: "requires-disabled", cause: [] };

		let result: Blocked | undefined;
		for (const other of requires.get(id) ?? []) {
			const found = visit(other);
			if (!found) continue;
			const chained: Blocked = { code: found.code, cause: [other, ...found.cause] };
			if (chained.code === "requires-failed") {
				result = chained;
				break;
			}
			result ??= chained;
		}
		blocked.set(id, result);

		if (result) {
			const reason = result.code === "requires-failed" ? "failed" : "is switched off";
			const message = `required plugin '${result.cause.at(-1)}' ${reason} (via ${result.cause.join(" -> ")})`;
			statuses.set(id, { id, status: "blocked", code: result.code, message, cause: result.cause });
		} else {
			// Post-order: the plugins it requires were added before.
			candidates.push({ id, requires: requires.get(id)!, load: catalogue[id]!.load! });
		}
		return result;
	}

	for (const id of ids) visit(id);

	return { statuses, candidates };
}

/** Strongly connected components (Tarjan) that form a cycle, a plugin requiring itself included. */
function findCycles(requires: Map<string, string[]>): string[][] {
	const index = new Map<string, number>();
	const low = new Map<string, number>();
	const stack: string[] = [];
	const onStack = new Set<string>();
	const cycles: string[][] = [];
	let counter = 0;

	function connect(id: string) {
		index.set(id, counter);
		low.set(id, counter);
		counter += 1;
		stack.push(id);
		onStack.add(id);

		for (const other of requires.get(id) ?? []) {
			if (!requires.has(other)) continue;
			if (!index.has(other)) {
				connect(other);
				low.set(id, Math.min(low.get(id)!, low.get(other)!));
			} else if (onStack.has(other)) {
				low.set(id, Math.min(low.get(id)!, index.get(other)!));
			}
		}

		if (low.get(id) === index.get(id)) {
			const component: string[] = [];
			let member: string;
			do {
				member = stack.pop()!;
				onStack.delete(member);
				component.push(member);
			} while (member !== id);
			if (component.length > 1 || requires.get(id)!.includes(id)) cycles.push(component.reverse());
		}
	}

	for (const id of requires.keys()) if (!index.has(id)) connect(id);
	return cycles;
}
