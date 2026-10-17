/**
 * ESLint rule `architecture/boundaries`: checks relative imports against
 * docs/development/architecture.md and its scope client (rules 0, 1, scope client 1).
 *
 * Paths are relative to the project root (the repository): the client lives in `client/`, its tests in
 * `tests/`, the old viewer in `src_old/`, the template in `reference/`.
 *
 * Imports of packages are not checked. A plugin may import another plugin
 * only if that one is listed under `requires` in the importing plugin's
 * manifest `plugin.json`, and only through its public API. The manifest is read
 * when a file imports into another plugin; if it is missing or unusable, every
 * such import is reported (`manifestUnreadable`).
 *
 * Runs without a build step: Node strips the types when ESLint loads it, so
 * only erasable TypeScript syntax is allowed here.
 */
import type { Rule } from "eslint";
import { readFileSync } from "node:fs";
import path from "node:path";

type Layer = "app" | "core" | "shared" | "plugin" | "legacy" | "tests" | "other";

type Unit = {
	layer: Layer;
	/** Folder of the unit relative to the project root, e.g. `client/src/core`. */
	root: string;
};

type Options = { root?: string };

const productionLayers: ReadonlySet<Layer> = new Set(["app", "core", "shared", "plugin"]);

/**
 * Layers each production layer may import from (rule 1.2). Imports between
 * plugins are decided separately, by `requires`.
 */
const allowedTargets: Record<string, ReadonlySet<Layer>> = {
	app: new Set(["core", "plugin"]),
	core: new Set(["shared"]),
	plugin: new Set(["core", "shared"]),
	shared: new Set(),
};

/** The ids under `requires` of a manifest, or `undefined` if the file is missing or not usable. */
function readRequires(manifestPath: string): ReadonlySet<string> | undefined {
	let manifest: unknown;
	try {
		manifest = JSON.parse(readFileSync(manifestPath, "utf-8"));
	} catch {
		return undefined;
	}
	const requires = typeof manifest === "object" && manifest !== null && "requires" in manifest ? manifest.requires : undefined;
	if (Array.isArray(requires) && requires.every((id) => typeof id === "string")) return new Set(requires);
	return undefined;
}

function classify(relativePath: string): Unit {
	const parts = relativePath.split("/");

	if (parts[0] === "src_old" || parts[0] === "reference") return { layer: "legacy", root: parts[0] };
	if (parts[0] === "tests") return { layer: "tests", root: "tests" };
	if (parts[0] === "client" && parts[1] === "src") {
		if (parts[2] === "app" || parts[2] === "core" || parts[2] === "shared") {
			return { layer: parts[2], root: `client/src/${parts[2]}` };
		}
		if (parts[2] === "plugins" && parts[3]) {
			return { layer: "plugin", root: `client/src/plugins/${parts[3]}` };
		}
	}
	return { layer: "other", root: "" };
}

function isPublicEntry(target: string, unit: Unit): boolean {
	return target === unit.root || target === `${unit.root}/index` || target === `${unit.root}/index.ts`;
}

function toPosix(p: string): string {
	return p.split(path.sep).join("/");
}

export const boundaries: Rule.RuleModule = {
	meta: {
		type: "problem",
		docs: {
			description: "Enforce the layer and public-API rules of docs/development/architecture.md",
		},
		schema: [
			{
				type: "object",
				properties: { root: { type: "string" } },
				additionalProperties: false,
			},
		],
		messages: {
			legacy: "Nothing may import from src_old or reference; copy and adapt instead (architecture rule 0).",
			testCode: "Production code must not import test code (scope client 1).",
			direction: "'{{from}}' must not import from '{{to}}' (scope client 1).",
			coreToPlugin: "core must not import from a plugin (scope client 1).",
			pluginToPlugin:
				"Plugin '{{from}}' must not import from plugin '{{to}}': it is not listed under `requires` in client/src/plugins/{{from}}/plugin.json (scope client 1).",
			manifestUnreadable:
				"Cannot check the import into another plugin: '{{manifest}}' is missing or invalid; it must be JSON with a list `requires` (scope client 1 and 2).",
			deepImport: "Import '{{to}}' only through its public API '{{entry}}' (scope client 1).",
		},
	},

	create(context) {
		const options = (context.options[0] ?? {}) as Options;
		const projectRoot = options.root ?? context.cwd;
		const importerUnit = classify(toPosix(path.relative(projectRoot, context.filename)));

		// Read when this file first imports into another plugin, then reused for the file.
		let requires: ReadonlySet<string> | undefined | null = null;
		const manifest = `${importerUnit.root}/plugin.json`;
		function requiredPlugins(): ReadonlySet<string> | undefined {
			if (requires === null) requires = readRequires(path.join(projectRoot, manifest));
			return requires;
		}

		function check(node: Rule.Node, source: unknown): void {
			if (typeof source !== "string" || !source.startsWith(".")) return;

			const absolute = path.resolve(path.dirname(context.filename), source);
			const target = toPosix(path.relative(projectRoot, absolute));
			const targetUnit = classify(target);

			if (targetUnit.layer === "legacy") {
				context.report({ node, messageId: "legacy" });
				return;
			}
			if (!productionLayers.has(importerUnit.layer)) return;

			if (targetUnit.layer === "tests") {
				context.report({ node, messageId: "testCode" });
				return;
			}
			if (!productionLayers.has(targetUnit.layer) || targetUnit.root === importerUnit.root) return;

			if (importerUnit.layer === "plugin" && targetUnit.layer === "plugin") {
				const required = requiredPlugins();
				if (!required) {
					context.report({ node, messageId: "manifestUnreadable", data: { manifest } });
					return;
				}
				if (!required.has(path.posix.basename(targetUnit.root))) {
					const [from, to] = [importerUnit.root, targetUnit.root].map((root) => path.posix.basename(root));
					context.report({ node, messageId: "pluginToPlugin", data: { from, to } });
					return;
				}
			} else if (!allowedTargets[importerUnit.layer].has(targetUnit.layer)) {
				const messageId = importerUnit.layer === "core" && targetUnit.layer === "plugin" ? "coreToPlugin" : "direction";
				context.report({ node, messageId, data: { from: importerUnit.root, to: targetUnit.root } });
				return;
			}
			if (!isPublicEntry(target, targetUnit)) {
				context.report({ node, messageId: "deepImport", data: { to: target, entry: targetUnit.root } });
			}
		}

		return {
			ImportDeclaration: (node) => check(node, node.source.value),
			ExportNamedDeclaration: (node) => check(node, node.source?.value),
			ExportAllDeclaration: (node) => check(node, node.source.value),
			ImportExpression: (node) => check(node, node.source.type === "Literal" ? node.source.value : undefined),
		};
	},
};
