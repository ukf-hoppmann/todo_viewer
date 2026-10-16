import Ajv, { type ErrorObject } from "ajv";
import { ConfigError, type ConfigErrorDetail } from "./ConfigError";
import pluginSelectionSchema from "./pluginSelection.schema.json";
import type { PluginSelection } from "./types";

// Collects every violation instead of stopping at the first.
const ajv = new Ajv({ allErrors: true });
const validate = ajv.compile<PluginSelection>(pluginSelectionSchema);

function toDetail({ instancePath, message, params }: ErrorObject): ConfigErrorDetail {
	// Name the unknown field, otherwise the message says only "additional properties".
	const extra = "additionalProperty" in params ? `: ${String(params.additionalProperty)}` : "";
	return { path: instancePath, message: `${message ?? "is invalid"}${extra}` };
}

/** Checks the raw data against the schema of the plugin selection; throws `ConfigError` (`config-invalid`) if it does not match. */
export function validatePluginSelection(raw: unknown): PluginSelection {
	if (validate(raw)) return raw;
	throw new ConfigError("config-invalid", "the plugin selection does not match its schema", (validate.errors ?? []).map(toDetail));
}
