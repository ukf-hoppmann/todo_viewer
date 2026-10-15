import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Schemas } from "../api/client";
import { renderWithProviders, sourceStatus } from "../test/render";
import { SyncDialog } from "./SyncDialog";

type Out = Schemas["SyncOut"];
type Section = Schemas["SyncSectionOut"];

const entry = (label: string, name: string | null = null, origin: "database" | "markdown" | null = null) => ({ label, title: `Title ${label}`, name, origin });
const conflict = (label: string, reason: Schemas["SyncConflictOut"]["reason"] = "both_changed") => ({
  kind: "item" as const, label, title: `Title ${label}`, name: null, reason, database: null, markdown: null,
});
const section = (over: Partial<Section> = {}): Section => ({ created: [], changed: [], unchanged: 0, ...over });
const answer = (over: Partial<Out> = {}): Out => ({
  executed: false,
  token: "tok-1",
  items: section(),
  documents: section(),
  conflicts: [],
  skipped: [],
  resolved: [],
  deleted: [],
  deferred: [],
  kept: [],
  ...over,
});

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

/** Records every request; `handler` answers them. */
function stubApi(handler: (request: Request, body: Record<string, unknown>) => Response) {
  const calls: { method: string; path: string; body: Record<string, unknown> }[] = [];
  vi.stubGlobal("fetch", async (request: Request) => {
    const raw = await request.clone().text();
    const body = raw ? (JSON.parse(raw) as Record<string, unknown>) : {};
    calls.push({ method: request.method, path: new URL(request.url).pathname, body });
    return handler(request, body);
  });
  return calls;
}

const previewWith = answer({
  items: section({ created: [entry("TASK-1", null, "database")], changed: [entry("TASK-2", null, "markdown")], unchanged: 4 }),
  documents: section({ created: [entry("TASK-1", "TASK-1_notes.md", "database")], unchanged: 2 }),
  conflicts: [conflict("TASK-9", "database_deleted")],
  skipped: [entry("TASK-3", "items/TASK-3/x.md")],
});

/** Preview first; a confirmed request answers like the server does, with the outcome. */
const server = (preview: Out, executed: Partial<Out> = {}) => (_: Request, body: Record<string, unknown>) =>
  jsonResponse(body.confirm ? { ...preview, executed: true, ...executed } : preview);

describe("SyncDialog: syncing a database project", () => {
  afterEach(() => vi.unstubAllGlobals());
  const source = sourceStatus();
  const open = (onClose = vi.fn()) => renderWithProviders(<SyncDialog source={source} mode="sync" onClose={onClose} onSwitched={vi.fn()} />);

  it("asks for a preview first and shows what would happen, with the conflicts as a warning", async () => {
    const calls = stubApi(server(previewWith));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    expect(await screen.findByText("1 neu · 1 geändert · 4 unverändert")).toBeInTheDocument();
    expect(screen.getByText("1 neu · 0 geändert · 2 unverändert")).toBeInTheDocument();
    expect(calls).toEqual([{ method: "POST", path: "/api/v2/sources/s1/sync", body: { direction: null, confirm: false, resolutions: [], language: "de" } }]);
    const warning = screen.getByRole("group", { name: "Konflikte" });
    expect(within(warning).getByText("TASK-9 — Title TASK-9")).toBeInTheDocument();
    expect(within(warning).getByText("(in der Datenbank gelöscht)")).toBeInTheDocument();
    expect(screen.getByText("＋ TASK-1 — Title TASK-1 →")).toBeInTheDocument();  // comes from the database
    expect(screen.getByText("≠ TASK-2 — Title TASK-2 ←")).toBeInTheDocument();  // comes from the folder
    expect(screen.getByText(/items\/TASK-3\/x\.md/)).toBeInTheDocument();
  });

  it("carries the sync out with the token of the preview and reports the conflicts that stayed", async () => {
    const calls = stubApi(server(previewWith, { deferred: [entry("TASK-9")] }));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await userEvent.click(await screen.findByRole("button", { name: "Ausführen" }));

    expect(await screen.findByText("Sync abgeschlossen.")).toBeInTheDocument();
    expect(calls[1]!.body).toEqual({ direction: null, confirm: true, token: "tok-1", resolutions: [], language: "de" });
    expect(screen.getByText("Aufgeschobene Konflikte: 1")).toBeInTheDocument();
  });

  it("changing the direction drops the preview and sends the other direction", async () => {
    const calls = stubApi(server(previewWith));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await screen.findByText("1 neu · 1 geändert · 4 unverändert");
    await userEvent.click(screen.getByRole("radio", { name: "Nur Ordner → Datenbank" }));

    expect(screen.queryByText("1 neu · 1 geändert · 4 unverändert")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Ausführen" })).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls[1]!.body.direction).toBe("from_md");
  });

  it("says when both sides are equal", async () => {
    stubApi(server(answer({ items: section({ unchanged: 3 }) })));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    expect(await screen.findByText("Beide Seiten sind gleich.")).toBeInTheDocument();
  });

  it("translates the error of a stale preview and lets the user ask again", async () => {
    stubApi((_, body) => (body.confirm ? jsonResponse({ code: "sync_stale", message: "x", details: {} }, 409) : jsonResponse(previewWith)));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await userEvent.click(await screen.findByRole("button", { name: "Ausführen" }));

    expect(await screen.findByText("Seit der Vorschau hat sich eine Seite geändert. Bitte die Vorschau neu holen.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Vorschau" })).toBeEnabled();
  });

  it("names the reason when the folder cannot be read", async () => {
    stubApi(() => jsonResponse({ code: "sync_source_invalid", message: "x", details: { reason: "not_found" } }, 400));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    expect(await screen.findByText("Der Ordner lässt sich nicht abgleichen; es wurde nichts geändert: Ordner nicht gefunden.")).toBeInTheDocument();
  });
});

describe("SyncDialog: deciding conflicts", () => {
  afterEach(() => vi.unstubAllGlobals());
  const itemConflict = {
    ...conflict("TASK-5"),
    database: { fields: [{ name: "title", value: "In the database" }, { name: "goal", value: "same" }], text: null },
    markdown: { fields: [{ name: "title", value: "In the file" }, { name: "goal", value: "same" }], text: null },
  };
  const docConflict = {
    kind: "document" as const, label: "TASK-5", title: "Title TASK-5", name: "TASK-5_notes.md", reason: "both_changed" as const,
    database: { fields: null, text: "one\ntwo\nthree" }, markdown: { fields: null, text: "one\nTWO\nthree" },
  };
  const withConflicts = answer({ conflicts: [itemConflict, docConflict, conflict("TASK-6", "markdown_deleted")] });
  const open = () => renderWithProviders(<SyncDialog source={sourceStatus()} mode="sync" onClose={vi.fn()} onSwitched={vi.fn()} />);

  it("preselects deferring for every conflict", async () => {
    stubApi(server(withConflicts));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    for (const group of await screen.findAllByRole("radiogroup", { name: /Entscheidung für/ })) {
      expect(within(group).getByRole("radio", { name: "Aufschieben" })).toBeChecked();
    }
  });

  it("sends exactly the decisions made, each for its own conflict, and leaves the rest deferred", async () => {
    const calls = stubApi(server(withConflicts, { deferred: [entry("TASK-6")] }));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    const item = await screen.findByRole("radiogroup", { name: "Entscheidung für TASK-5 — Title TASK-5" });
    await userEvent.click(within(item).getByRole("radio", { name: "Datenbank gilt" }));
    const doc = screen.getByRole("radiogroup", { name: "Entscheidung für TASK-5 / TASK-5_notes.md" });
    await userEvent.click(within(doc).getByRole("radio", { name: "Datei gilt" }));
    await userEvent.click(screen.getByRole("button", { name: "Ausführen" }));

    await screen.findByText("Sync abgeschlossen.");
    expect(calls[1]!.body.resolutions).toEqual([
      { kind: "item", label: "TASK-5", name: null, choice: "database" },
      { kind: "document", label: "TASK-5", name: "TASK-5_notes.md", choice: "markdown" },
    ]);
    expect(screen.getByText("Aufgeschobene Konflikte: 1")).toBeInTheDocument();
  });

  it("shows the differing fields side by side for an item", async () => {
    stubApi(server(withConflicts));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await userEvent.click((await screen.findAllByRole("button", { name: "Vergleich anzeigen" }))[0]!);

    const table = screen.getByRole("table");
    expect(within(table).getByText("In the database")).toBeInTheDocument();
    expect(within(table).getByText("In the file")).toBeInTheDocument();
    expect(within(table).queryByText("goal")).not.toBeInTheDocument();  // equal fields are left out
  });

  it("shows a text comparison for a document and says a side is missing for a deletion", async () => {
    stubApi(server(withConflicts));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    const buttons = await screen.findAllByRole("button", { name: "Vergleich anzeigen" });
    await userEvent.click(buttons[1]!);
    expect(screen.getByText(/^− two/)).toHaveClass("diff-removed");
    expect(screen.getByText(/^\+ TWO/)).toHaveClass("diff-added");
    await userEvent.click(screen.getAllByRole("button", { name: "Vergleich anzeigen" })[1]!);  // TASK-6 (the others are open)
    expect(screen.getByText("Auf dieser Seite fehlt der Eintrag: Datenbank")).toBeInTheDocument();
  });

  it("a switch sends no decisions and waits for the conflicts to be decided in a normal sync", async () => {
    const calls = stubApi(server(withConflicts));
    renderWithProviders(<SyncDialog source={sourceStatus()} mode="switch" onClose={vi.fn()} onSwitched={vi.fn()} />);

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    expect(await screen.findByRole("button", { name: "Übernehmen und umstellen" })).toBeDisabled();
    expect(calls).toHaveLength(1);
  });
});

describe("SyncDialog: switching the storage of a project", () => {
  afterEach(() => vi.unstubAllGlobals());
  const markdown = sourceStatus({ backend: "markdown", path: "/repos/a/docs", sync_path: null });

  /** The server of a switch: sync answers as given, the project comes back moved. */
  const switching = (preview: Out, put: Response | null = null) => (request: Request, body: Record<string, unknown>) =>
    request.method === "PUT" ? (put ?? jsonResponse(sourceStatus({ backend: "database", path: "", sync_path: "/repos/a/docs" })))
      : jsonResponse(body.confirm ? { ...preview, executed: true } : preview);

  it("reads the folder into the database and then switches; the direction is fixed", async () => {
    const calls = stubApi(switching(answer({ items: section({ created: [entry("TASK-1")] }) })));
    const onSwitched = vi.fn();
    renderWithProviders(<SyncDialog source={markdown} mode="switch" onClose={vi.fn()} onSwitched={onSwitched} />);

    expect(screen.getByRole("dialog", { name: "„Central“ in die Datenbank übernehmen" })).toBeInTheDocument();
    expect(screen.getByText(/Der Ordner \/repos\/a\/docs wird in die Datenbank gelesen/)).toBeInTheDocument();
    expect(screen.queryByRole("radio")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await userEvent.click(await screen.findByRole("button", { name: "Übernehmen und umstellen" }));

    await waitFor(() => expect(onSwitched).toHaveBeenCalledWith("Central"));
    expect(calls.map((c) => [c.method, c.path])).toEqual([
      ["POST", "/api/v2/sources/s1/sync"], ["POST", "/api/v2/sources/s1/sync"], ["PUT", "/api/v2/sources/s1"]]);
    expect(calls[0]!.body.direction).toBe("from_md");
    expect(calls[1]!.body).toMatchObject({ confirm: true, token: "tok-1" });
    expect(calls[2]!.body).toEqual({ path: "", backend: "database" });
  });

  it("does not switch while conflicts are undecided", async () => {
    stubApi(switching(answer({ conflicts: [conflict("TASK-9")] })));
    renderWithProviders(<SyncDialog source={markdown} mode="switch" onClose={vi.fn()} onSwitched={vi.fn()} />);

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    expect(await screen.findByRole("button", { name: "Übernehmen und umstellen" })).toBeDisabled();
    expect(screen.getByText("Zum Umstellen müssen die Konflikte entschieden sein.")).toBeInTheDocument();
  });

  it("writes the database out and moves the project back to its folder", async () => {
    const calls = stubApi(switching(answer(), jsonResponse(sourceStatus({ backend: "markdown", path: "/repos/central", sync_path: null }))));
    const onSwitched = vi.fn();
    renderWithProviders(<SyncDialog source={sourceStatus()} mode="switch" onClose={vi.fn()} onSwitched={onSwitched} />);

    expect(screen.getByRole("dialog", { name: "„Central“ als Markdown-Ordner ablegen" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await userEvent.click(await screen.findByRole("button", { name: "Übernehmen und umstellen" }));

    await waitFor(() => expect(onSwitched).toHaveBeenCalledWith("Central"));
    expect(calls[0]!.body.direction).toBe("to_md");
    expect(calls[2]!.body).toEqual({ path: "", backend: "markdown" });
  });

  it("shows a translated error when the server refuses the switch and leaves the dialog open", async () => {
    stubApi(switching(answer(), jsonResponse({ code: "sync_required", message: "x", details: {} }, 409)));
    const onSwitched = vi.fn();
    renderWithProviders(<SyncDialog source={markdown} mode="switch" onClose={vi.fn()} onSwitched={onSwitched} />);

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await userEvent.click(await screen.findByRole("button", { name: "Übernehmen und umstellen" }));

    expect(await screen.findByText("Die Seiten sind nicht gleich. Erst synchronisieren, dann umstellen.")).toBeInTheDocument();
    expect(onSwitched).not.toHaveBeenCalled();
  });
});

describe("SyncDialog: the direction", () => {
  afterEach(() => vi.unstubAllGlobals());
  const markdownWithMirror = sourceStatus({
    backend: "markdown", path: "/repos/a/docs", sync_path: null, primary: "markdown", markdown_path: "/repos/a/docs", mirror: "database",
  });

  it("starts with both directions and says so", () => {
    stubApi(server(answer()));
    renderWithProviders(<SyncDialog source={sourceStatus()} mode="sync" onClose={vi.fn()} onSwitched={vi.fn()} />);

    expect(screen.getByRole("radio", { name: /In beide Richtungen/ })).toBeChecked();
    expect(screen.getByRole("radio", { name: /In beide Richtungen.*\(Standard\)/ })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Nur Datenbank → Ordner" })).not.toBeChecked();
    expect(screen.getByRole("radio", { name: "Nur Ordner → Datenbank" })).not.toBeChecked();
  });

  it("restricts the run to one side when asked", async () => {
    const calls = stubApi(server(answer()));
    renderWithProviders(<SyncDialog source={markdownWithMirror} mode="sync" onClose={vi.fn()} onSwitched={vi.fn()} />);

    expect(screen.getByText("Sync-Ordner: /repos/a/docs")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await waitFor(() => expect(calls).toHaveLength(1));
    await userEvent.click(screen.getByRole("radio", { name: "Nur Datenbank → Ordner" }));
    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls.map((c) => c.body.direction)).toEqual([null, "to_md"]);
  });
});

describe("SyncDialog: switching saves the old primary source first", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("says that a backup is made before the switch", () => {
    stubApi(server(answer()));
    renderWithProviders(<SyncDialog source={sourceStatus()} mode="switch" onClose={vi.fn()} onSwitched={vi.fn()} />);

    expect(screen.getByText(/legt der Dienst ein Backup der bisherigen Primärquelle an/)).toBeInTheDocument();
  });

  it("names why the backup failed, changes nothing, and stays open", async () => {
    stubApi((request, body) =>
      request.method === "PUT"
        ? jsonResponse({ code: "backup_failed", message: "x", details: { reason: "disk full" } }, 409)
        : jsonResponse(body.confirm ? { ...answer(), executed: true } : answer()),
    );
    const onSwitched = vi.fn();
    renderWithProviders(<SyncDialog source={sourceStatus()} mode="switch" onClose={vi.fn()} onSwitched={onSwitched} />);

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await userEvent.click(await screen.findByRole("button", { name: "Übernehmen und umstellen" }));

    expect(await screen.findByText(/Das Backup der bisherigen Primärquelle ist fehlgeschlagen.*disk full/)).toBeInTheDocument();
    expect(onSwitched).not.toHaveBeenCalled();
  });
});

