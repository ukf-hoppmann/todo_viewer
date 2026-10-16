import Ajv, { type ErrorObject } from "ajv";
import loggingSchema from "../logging/logging.schema.json";
import appConfigSchema from "./appConfig.schema.json";
import { ConfigError, type ConfigErrorDetail } from "./ConfigError";
import type { AppConfig } from "./types";

// Collects every violation instead of stopping at the first. The default
// (strict) mode rejects mistakes in the schemas themselves.
const ajv = new Ajv({ allErrors: true });
ajv.addSchema(loggingSchema);
const validate = ajv.compile<AppConfig>(appConfigSchema);

function toDetail({ instancePath, message, params }: ErrorObject): ConfigErrorDetail {
	// Name the unknown field, otherwise the message says only "additional properties".
	const extra = "additionalProperty" in params ? `: ${String(params.additionalProperty)}` : "";
	return { path: instancePath, message: `${message ?? "is invalid"}${extra}` };
}

/** Checks the raw data against the schema of the app config; throws `ConfigError` (`config-invalid`) if it does not match. */
export function validateAppConfig(raw: unknown): AppConfig {
	if (validate(raw)) return raw;
	throw new ConfigError("config-invalid", "the app config does not match its schema", (validate.errors ?? []).map(toDetail));
}
