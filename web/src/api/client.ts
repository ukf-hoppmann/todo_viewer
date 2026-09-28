// Typed HTTP client for API v2. Types come from schema.d.ts (npm run gen:api).
import createClient from "openapi-fetch";
import type { components, paths } from "./schema";

export type Schemas = components["schemas"];
export type ApiItem = Schemas["ItemOut"];
export type SourceStatus = Schemas["SourceStatusOut"];
export type Source = Schemas["SourceOut"];
export type FolderListing = Schemas["FolderListingOut"];
export type ItemFields = Schemas["ItemFieldsIn"];

// Absolute base URL (Request needs one outside browsers); fetch is looked up per call
// instead of being captured at import, so tests can stub it.
export const api = createClient<paths>({
  baseUrl: globalThis.location?.origin ?? "",
  fetch: (request) => globalThis.fetch(request),
});

/** An error answer of the API, carrying the stable code the UI translates. */
export class ApiError extends Error {
  readonly code: string;
  readonly details: Record<string, string>;

  constructor(code: string, message: string, details: Record<string, string> = {}) {
    super(message);
    this.code = code;
    this.details = details;
  }
}

type Result<T> = { data?: T; error?: unknown; response: Response };

/** Returns the data of an openapi-fetch result or throws an ApiError. */
export async function unwrap<T>(call: Promise<Result<T>>): Promise<T> {
  const { data, error, response } = await call;
  if (error !== undefined || data === undefined) {
    const body = (error ?? {}) as Partial<Schemas["ErrorOut"]>;
    throw new ApiError(body.code ?? `http_${response.status}`, body.message ?? response.statusText, body.details);
  }
  return data;
}
