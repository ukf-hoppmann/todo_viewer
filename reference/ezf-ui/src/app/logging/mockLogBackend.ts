import Ajv, { type ErrorObject } from "ajv";
import schema from "./backendLogEntry.schema.json";

// Unknown additional fields are allowed, as the backend is asked to keep them.
const ajv = new Ajv({ allErrors: true });
const validate = ajv.compile(schema);

function describe({ instancePath, message }: ErrorObject): string {
	return `${instancePath === "" ? "/" : instancePath}: ${message ?? "is invalid"}`;
}

/**
 * Stands in for `persistLogFromUi` until the backend takes the new format
 * (STORY-009). Used as `fetch` of the
 * `BackendSink`: it checks each entry against the agreed format and answers
 * 204 if it fits, otherwise 400 with the problems. Accepted entries are
 * dropped; they are in the console anyway.
 */
export async function mockLogBackend(_url: string, init: RequestInit): Promise<Response> {
	let body: unknown;
	try {
		body = JSON.parse(String(init.body));
	} catch {
		return new Response("body is no JSON", { status: 400 });
	}
	if (validate(body)) return new Response(null, { status: 204 });
	return new Response((validate.errors ?? []).map(describe).join("; "), { status: 400 });
}
