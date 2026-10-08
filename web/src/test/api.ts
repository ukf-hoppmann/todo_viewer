import type { Schemas } from "../api/client";
import type { IndexNote, IndexTopic } from "../domain/notes";
import { sourceStatus } from "./render";

export function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

export function errorResponse(status: number, code: string, details: Record<string, string> = {}) {
  return jsonResponse({ code, message: code, details }, status);
}

export interface Route {
  method: string;
  /** Path of the request, or a pattern for it. */
  path: string | RegExp;
  respond: (request: Request) => unknown;
}

export interface RecordedCall {
  method: string;
  path: string;
  search: string;
  body: () => Promise<unknown>;
}

/**
 * Stubs `fetch` with a table of routes. A route answers with a `Response` or any value (sent as JSON, 200).
 * Anything unmatched is a 404 `not_stubbed`, so a test sees at once which request it forgot.
 */
export function stubRoutes(routes: Route[]) {
  const calls: RecordedCall[] = [];
  vi.stubGlobal("fetch", async (request: Request) => {
    const url = new URL(request.url);
    const route = routes.find((r) => r.method === request.method && (typeof r.path === "string" ? r.path === url.pathname : r.path.test(url.pathname)));
    const copy = request.clone();
    calls.push({ method: request.method, path: url.pathname, search: url.search, body: () => copy.json() });
    if (!route) return errorResponse(404, "not_stubbed");
    const answer = route.respond(request);
    return answer instanceof Response ? answer : jsonResponse(answer);
  });
  return calls;
}

export function indexTopic(label: string, over: Partial<IndexTopic> = {}): IndexTopic {
  return { project: "P", label, name: `Topic ${label}`, parent: null, path: [`Topic ${label}`], due_at: null, due: false, note_count: 0, ...over };
}

export function indexNote(label: string, over: Partial<IndexNote> = {}): IndexNote {
  return { project: "P", label, summary: `Summary ${label}`, status: "waiting", reason: null, review_at: null, topic: null, archived: false, ...over };
}

/** The routes every Notes test needs: the project list and the index. */
export function notesBaseRoutes(topics: IndexTopic[], notes: IndexNote[]): Route[] {
  return [
    { method: "GET", path: "/api/v2/backlog", respond: () => ({ items: [], sources: [sourceStatus({ id: "s1", project: "P", backend: "database" })] }) },
    { method: "GET", path: "/api/v2/notes/index", respond: () => ({ topics, notes }) },
  ];
}

export function noteOut(label: string, over: Partial<Schemas["NoteOut"]> = {}): Schemas["NoteOut"] {
  return {
    project: "P",
    label,
    version: `v-${label}`,
    summary: `Summary ${label}`,
    body: null,
    status: "waiting",
    stored_status: "waiting",
    reason: null,
    topic: null,
    review_at: "2027-06-15T12:00:00Z",
    trigger_mode: "any",
    triggers: [],
    open_notices: [],
    archived: false,
    deleted: null,
    created: null,
    updated: null,
    ...over,
  };
}

export function linkOut(id: number, over: Partial<Schemas["LinkOut"]> = {}): Schemas["LinkOut"] {
  return {
    id,
    note: "NOTE-001",
    project: "P",
    kind: "item",
    target_project: "P",
    target: "STORY-001",
    target_display: "P · STORY-001",
    role: "reference",
    reachable: true,
    unreachable_reason: null,
    ...over,
  };
}
