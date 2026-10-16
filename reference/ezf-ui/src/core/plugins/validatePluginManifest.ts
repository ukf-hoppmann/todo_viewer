import Ajv, { type ErrorObject } from "ajv";
import pluginManifestSchema from "./pluginManifest.schema.json";
import type { PluginManifest } from "./types";

// Collects every violation instead of stopping at the first.
const ajv = new Ajv({ allErrors: true });
const validate = ajv.compile<PluginManifest>(pluginManifestSchema);

export type ManifestResult = { ok: true; manifest: PluginManifest } | { ok: false; message: string };

function describe({ instancePath, message, params }: ErrorObject): string {
	// Name the unknown field, otherwise the message says only "additional properties".
	const extra = "additionalProperty" in params ? `: ${String(params.additionalProperty)}` : "";
	return `${instancePath === "" ? "/" : instancePath}: ${message ?? "is invalid"}${extra}`;
}

/**
 * Checks the raw content of a `plugin.json` (`undefined` if the file is
 * missing). A broken manifest disables only its plugin, so the result is
 * returned instead of thrown.
 */
export function validatePluginManifest(raw: unknown): ManifestResult {
	if (validate(raw)) return { ok: true, manifest: raw };
	return { ok: false, message: (validate.errors ?? []).map(describe).join("; ") };
}
