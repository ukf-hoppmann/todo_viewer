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
  topics: section(),
  notes: section(),
  note_documents: section(),
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

  it("loads the preview by itself and puts the conflicts first, the rest of the changes as one line", async () => {
    const calls = stubApi(server(previewWith));
    open();

    const warning = await screen.findByRole("group", { name: "Konflikte" });
    expect(calls).toEqual([{ method: "POST", path: "/api/v2/sources/s1/sync", body: { direction: null, confirm: false, resolutions: [], language: "de" } }]);
    expect(within(warning).getByText("TASK-9 — Title TASK-9")).toBeInTheDocument();
    expect(within(warning).getByText("(in der Datenbank gelöscht)")).toBeInTheDocument();
    const line = screen.getByText("Konfliktfreie Änderungen, die beim Übernehmen mitgehen: 3 (2 neu, 1 geändert).");
    expect(warning.compareDocumentPosition(line) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();  // the conflicts stand above the changes
    expect(screen.getByText(/items\/TASK-3\/x\.md/)).toBeInTheDocument();
  });

  it("keeps the lists of changes behind details", async () => {
    stubApi(server(previewWith));
    open();

    await screen.findByRole("group", { name: "Konflikte" });
    expect(screen.queryByText("＋ TASK-1 — Title TASK-1 →")).not.toBeInTheDocument();
    expect(screen.queryByText("1 neu · 1 geändert · 4 unverändert")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Details anzeigen" }));

    expect(screen.getByText("1 neu · 1 geändert · 4 unverändert")).toBeInTheDocument();
    expect(screen.getByText("1 neu · 0 geändert · 2 unverändert")).toBeInTheDocument();
    expect(screen.getByText("＋ TASK-1 — Title TASK-1 →")).toBeInTheDocument();  // comes from the database
    expect(screen.getByText("≠ TASK-2 — Title TASK-2 ←")).toBeInTheDocument();  // comes from the folder
    await userEvent.click(screen.getByRole("button", { name: "Details ausblenden" }));
    expect(screen.queryByText("＋ TASK-1 — Title TASK-1 →")).not.toBeInTheDocument();
  });

  it("has no direction to choose and no preview to ask for: the direction is a setting of the project", async () => {
    stubApi(server(previewWith));
    open();

    await screen.findByRole("group", { name: "Konflikte" });
    expect(screen.queryByRole("radiogroup", { name: "Richtung" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Vorschau" })).not.toBeInTheDocument();
  });

  it("carries the sync out with the token of the preview and reports the conflicts that stayed", async () => {
    const calls = stubApi(server(previewWith, { deferred: [entry("TASK-9")] }));
    open();

    await userEvent.click(await screen.findByRole("button", { name: "Entscheidungen übernehmen" }));

    expect(await screen.findByText("Sync abgeschlossen.")).toBeInTheDocument();
    expect(calls[1]!.body).toEqual({ direction: null, confirm: true, token: "tok-1", resolutions: [], language: "de" });
    expect(screen.getByText("Aufgeschobene Konflikte: 1")).toBeInTheDocument();
  });

  it("offers to run the sync when there is nothing to decide", async () => {
    stubApi(server(answer({ items: section({ created: [entry("TASK-1", null, "database")] }) })));
    open();

    expect(await screen.findByRole("button", { name: "Ausführen" })).toBeEnabled();
    expect(screen.queryByRole("button", { name: "Entscheidungen übernehmen" })).not.toBeInTheDocument();
    expect(screen.queryByRole("group", { name: "Konflikte" })).not.toBeInTheDocument();
    expect(screen.getByText("Änderungen, die übertragen werden: 1 (1 neu, 0 geändert).")).toBeInTheDocument();
  });

  it("says when both sides are equal", async () => {
    stubApi(server(answer({ items: section({ unchanged: 3 }) })));
    open();

    expect(await screen.findByText("Beide Seiten sind gleich.")).toBeInTheDocument();
  });

  it("says when only conflicts are left", async () => {
    stubApi(server(answer({ conflicts: [conflict("TASK-9")] })));
    open();

    expect(await screen.findByText("Außer den Konflikten gibt es nichts zu übertragen.")).toBeInTheDocument();
  });

  it("translates the error of a stale preview and lets the user ask again", async () => {
    stubApi((_, body) => (body.confirm ? jsonResponse({ code: "sync_stale", message: "x", details: {} }, 409) : jsonResponse(previewWith)));
    open();

    await userEvent.click(await screen.findByRole("button", { name: "Entscheidungen übernehmen" }));

    expect(await screen.findByText("Seit der Vorschau hat sich eine Seite geändert. Bitte die Vorschau neu holen.")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Vorschau neu laden" })).toBeEnabled();
  });

  it("loads the preview again on request", async () => {
    const calls = stubApi(server(previewWith));
    open();

    await screen.findByRole("group", { name: "Konflikte" });
    await userEvent.click(screen.getByRole("button", { name: "Vorschau neu laden" }));

    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls[1]!.body.confirm).toBe(false);
  });

  it("names the reason when the folder cannot be read", async () => {
    stubApi(() => jsonResponse({ code: "sync_source_invalid", message: "x", details: { reason: "not_found" } }, 400));
    open();

    expect(await screen.findByText("Der Ordner lässt sich nicht abgleichen; es wurde nichts geändert: Ordner nicht gefunden.")).toBeInTheDocument();
  });

  it("is titled after what it was opened for", async () => {
    stubApi(server(answer()));
    const { unmount } = open();
    expect(screen.getByRole("dialog", { name: "Sync: Central" })).toBeInTheDocument();
    await screen.findByText("Beide Seiten sind gleich.");
    unmount();

    renderWithProviders(<SyncDialog source={source} mode="sync" intent="resolve" onClose={vi.fn()} onSwitched={vi.fn()} />);
    expect(screen.getByRole("dialog", { name: "Konflikte klären: Central" })).toBeInTheDocument();
  });
});

describe("SyncDialog: notes in the same sync", () => {
  afterEach(() => vi.unstubAllGlobals());
  const open = () => renderWithProviders(<SyncDialog source={sourceStatus()} mode="sync" onClose={vi.fn()} onSwitched={vi.fn()} />);
  const withNotes = answer({
    topics: section({ created: [entry("TOPIC-1", null, "database")], unchanged: 2 }),
    notes: section({ created: [entry("new-idea", null, "markdown")], changed: [entry("NOTE-3", null, "database")], unchanged: 5 }),
    note_documents: section({ created: [entry("NOTE-3", "NOTE-3_notes.md", "database")] }),
  });

  it("shows topics, notes, and documents of notes next to items and documents, each with its counts", async () => {
    stubApi(server(withNotes));
    open();

    await userEvent.click(await screen.findByRole("button", { name: "Details anzeigen" }));

    expect(screen.getByRole("heading", { name: "Topics" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Notes" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Dokumente der Notes" })).toBeInTheDocument();
    expect(screen.getByText("1 neu · 0 geändert · 2 unverändert")).toBeInTheDocument();
    expect(screen.getByText("1 neu · 1 geändert · 5 unverändert")).toBeInTheDocument();
    expect(screen.getByText("＋ new-idea — Title new-idea ←")).toBeInTheDocument();  // written in the files
    expect(screen.getByText("＋ NOTE-3 / NOTE-3_notes.md →")).toBeInTheDocument();
    expect(screen.queryByText("Beide Seiten sind gleich.")).not.toBeInTheDocument();
  });

  it("counts notes, topics and their documents as changes, even folded away", async () => {
    stubApi(server(withNotes));
    open();

    expect(await screen.findByText("Änderungen, die übertragen werden: 4 (3 neu, 1 geändert).")).toBeInTheDocument();
  });

  it("leaves out the sections of notes when a project has none, and counts notes as a change", async () => {
    stubApi(server(answer({ items: section({ unchanged: 3 }) })));
    open();

    expect(await screen.findByText("Beide Seiten sind gleich.")).toBeInTheDocument();
    expect(screen.queryByRole("heading", { name: "Notes" })).not.toBeInTheDocument();
  });

  it("decides a note conflict and a topic conflict like any other, with the body as a text comparison", async () => {
    const note = {
      kind: "note" as const, label: "NOTE-7", title: "Prüfen", name: null, reason: "both_changed" as const,
      database: { fields: [{ name: "summary", value: "Prüfen" }, { name: "body", value: "eins\nzwei" }], text: null },
      markdown: { fields: [{ name: "summary", value: "Prüfen" }, { name: "body", value: "eins\nZWEI" }], text: null },
    };
    const topic = { ...conflict("TOPIC-2"), kind: "topic" as const, database: { fields: [{ name: "name", value: "A" }], text: null },
      markdown: { fields: [{ name: "name", value: "B" }], text: null } };
    const calls = stubApi(server(answer({ conflicts: [note, topic] })));
    open();

    await userEvent.click((await screen.findAllByRole("button", { name: "Vergleich anzeigen" }))[0]!);
    expect(screen.getByText(/^− zwei/)).toHaveClass("diff-removed");
    expect(screen.getByText(/^\+ ZWEI/)).toHaveClass("diff-added");
    expect(within(screen.getByRole("table")).queryByText("summary")).not.toBeInTheDocument();  // equal fields are left out
    await userEvent.click(within(screen.getByRole("radiogroup", { name: "Entscheidung für NOTE-7 — Prüfen" })).getByRole("radio", { name: "Datei gilt" }));
    await userEvent.click(within(screen.getByRole("radiogroup", { name: "Entscheidung für TOPIC-2 — Title TOPIC-2" })).getByRole("radio", { name: "Datenbank gilt" }));
    await userEvent.click(screen.getByRole("button", { name: "Entscheidungen übernehmen" }));

    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls[1]!.body.resolutions).toEqual([
      { kind: "note", label: "NOTE-7", name: null, choice: "markdown" },
      { kind: "topic", label: "TOPIC-2", name: null, choice: "database" },
    ]);
  });

  it("compares the text of a note document", async () => {
    const doc = {
      kind: "note_document" as const, label: "NOTE-7", title: "Prüfen", name: "NOTE-7_notes.md", reason: "both_changed" as const,
      database: { fields: null, text: "a\nb" }, markdown: { fields: null, text: "a\nc" },
    };
    stubApi(server(answer({ conflicts: [doc] })));
    open();

    await userEvent.click(await screen.findByRole("button", { name: "Vergleich anzeigen" }));

    expect(screen.getByText(/^− b/)).toHaveClass("diff-removed");
    expect(screen.getByText(/^\+ c/)).toHaveClass("diff-added");
  });

  it("translates the errors of the notes folder: a broken file with its line, a file changed meanwhile", async () => {
    stubApi((_, body) => body.confirm
      ? jsonResponse({ code: "mirror_conflict", message: "x", details: { file: "NOTE-1.md" } }, 409)
      : jsonResponse(withNotes));
    open();

    await userEvent.click(await screen.findByRole("button", { name: "Ausführen" }));
    expect(await screen.findByText(/Eine Datei im Notes-Ordner hat sich während des Syncs geändert/)).toBeInTheDocument();

    vi.unstubAllGlobals();
    stubApi(() => jsonResponse({ code: "sync_source_invalid", message: "Nothing was changed: NOTE-1.md, line 3: invalid Status: 'x'", details: { reason: "note_format" } }, 400));
    await userEvent.click(screen.getByRole("button", { name: "Vorschau neu laden" }));
    expect(await screen.findByText(/Eine Notes-Datei hält das Format nicht ein.*NOTE-1\.md, line 3/)).toBeInTheDocument();
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
  // Deleted in the folder: the database still has it, the file is gone.
  const deleted = { ...conflict("TASK-6", "markdown_deleted"), database: { fields: [{ name: "id", value: "TASK-6" }], text: null } };
  const withConflicts = answer({ conflicts: [itemConflict, docConflict, deleted] });
  const open = () => renderWithProviders(<SyncDialog source={sourceStatus()} mode="sync" onClose={vi.fn()} onSwitched={vi.fn()} />);
  const decision = (name: string) => within(screen.getByRole("radiogroup", { name: `Entscheidung für ${name}` }));

  it("preselects deferring for every conflict", async () => {
    stubApi(server(withConflicts));
    open();

    for (const group of await screen.findAllByRole("radiogroup", { name: /Entscheidung für/ })) {
      expect(within(group).getByRole("radio", { name: "Aufschieben" })).toBeChecked();
    }
  });

  it("sends exactly the decisions made, each for its own conflict, and leaves the rest deferred", async () => {
    const calls = stubApi(server(withConflicts, { deferred: [entry("TASK-6")] }));
    open();

    await screen.findByRole("radiogroup", { name: "Entscheidung für TASK-5 — Title TASK-5" });
    await userEvent.click(decision("TASK-5 — Title TASK-5").getByRole("radio", { name: "Datenbank gilt" }));
    await userEvent.click(decision("TASK-5 / TASK-5_notes.md").getByRole("radio", { name: "Datei gilt" }));
    await userEvent.click(screen.getByRole("button", { name: "Entscheidungen übernehmen" }));

    await screen.findByText("Sync abgeschlossen.");
    expect(calls[1]!.body.resolutions).toEqual([
      { kind: "item", label: "TASK-5", name: null, choice: "database" },
      { kind: "document", label: "TASK-5", name: "TASK-5_notes.md", choice: "markdown" },
    ]);
    expect(screen.getByText("Aufgeschobene Konflikte: 1")).toBeInTheDocument();
  });

  it("counts the decisions made out of all conflicts", async () => {
    stubApi(server(withConflicts));
    open();

    expect(await screen.findByText("0 von 3 entschieden")).toBeInTheDocument();
    await userEvent.click(decision("TASK-5 — Title TASK-5").getByRole("radio", { name: "Datenbank gilt" }));
    expect(screen.getByText("1 von 3 entschieden")).toBeInTheDocument();
    await userEvent.click(decision("TASK-5 — Title TASK-5").getByRole("radio", { name: "Aufschieben" }));
    expect(screen.getByText("0 von 3 entschieden")).toBeInTheDocument();
  });

  it("says in one line what differs, before any comparison is opened", async () => {
    stubApi(server(withConflicts));
    open();

    const rows = await screen.findAllByRole("listitem");
    const item = rows[0]!;
    expect(within(item).getByText("title")).toBeInTheDocument();
    expect(within(item).getByText("In the database")).toHaveClass("diff-removed");
    expect(within(item).getByText("In the file")).toHaveClass("diff-added");
    expect(within(item).queryByText("goal")).not.toBeInTheDocument();  // equal fields are left out
    expect(within(rows[1]!).getByText("Der Text unterscheidet sich.")).toBeInTheDocument();
    expect(within(rows[2]!).getByText("Auf dieser Seite fehlt der Eintrag: Datei")).toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
  });

  it("shows the differing fields side by side for an item", async () => {
    stubApi(server(withConflicts));
    open();

    await userEvent.click((await screen.findAllByRole("button", { name: "Vergleich anzeigen" }))[0]!);

    const table = screen.getByRole("table");
    expect(within(table).getByText("In the database")).toBeInTheDocument();
    expect(within(table).getByText("In the file")).toBeInTheDocument();
    expect(within(table).queryByText("goal")).not.toBeInTheDocument();  // equal fields are left out
  });

  it("shows a text comparison for a document and says a side is missing for a deletion", async () => {
    stubApi(server(withConflicts));
    open();

    const buttons = await screen.findAllByRole("button", { name: "Vergleich anzeigen" });
    await userEvent.click(buttons[1]!);
    expect(screen.getByText(/^− two/)).toHaveClass("diff-removed");
    expect(screen.getByText(/^\+ TWO/)).toHaveClass("diff-added");
    await userEvent.click(screen.getAllByRole("button", { name: "Vergleich anzeigen" })[1]!);  // TASK-6 (the others are open)
    expect(screen.getAllByText("Auf dieser Seite fehlt der Eintrag: Datei")).toHaveLength(2);  // the line and the comparison
  });

  it("a switch sends no decisions and waits for the conflicts to be decided in a normal sync", async () => {
    const calls = stubApi(server(withConflicts));
    renderWithProviders(<SyncDialog source={sourceStatus()} mode="switch" onClose={vi.fn()} onSwitched={vi.fn()} />);

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    expect(await screen.findByRole("button", { name: "Übernehmen und umstellen" })).toBeDisabled();
    expect(calls).toHaveLength(1);
  });
});

describe("SyncDialog: deciding all conflicts at once, and one by one", () => {
  afterEach(() => vi.unstubAllGlobals());
  const changed = (label: string) => ({ ...conflict(label), database: { fields: [{ name: "status", value: "Open" }], text: null }, markdown: { fields: [{ name: "status", value: "Completed" }], text: null } });
  const deleted = conflict("TASK-9", "database_deleted");
  const open = () => renderWithProviders(<SyncDialog source={sourceStatus()} mode="sync" onClose={vi.fn()} onSwitched={vi.fn()} />);
  const decision = (name: string) => within(screen.getByRole("radiogroup", { name: `Entscheidung für ${name}` }));
  const chosen = (name: string, choice: string) => expect(decision(name).getByRole("radio", { name: choice })).toBeChecked();

  it("gives one decision to every change on both sides and leaves the deletions to their own decision", async () => {
    stubApi(server(answer({ conflicts: [changed("A"), changed("B"), deleted] })));
    open();

    expect(await screen.findByText("Für alle 2 Änderungen auf beiden Seiten:")).toBeInTheDocument();
    expect(screen.getByText("Löschungen entscheidest du einzeln.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Datenbank gilt für alle" }));

    chosen("A — Title A", "Datenbank gilt");
    chosen("B — Title B", "Datenbank gilt");
    chosen("TASK-9 — Title TASK-9", "Aufschieben");
    expect(screen.getByText("2 von 3 entschieden")).toBeInTheDocument();
  });

  it("lets every row be changed after the bulk decision, and sends the result", async () => {
    const calls = stubApi(server(answer({ conflicts: [changed("A"), changed("B"), deleted] })));
    open();

    await userEvent.click(await screen.findByRole("button", { name: "Datei gilt für alle" }));
    await userEvent.click(decision("B — Title B").getByRole("radio", { name: "Datenbank gilt" }));
    await userEvent.click(decision("TASK-9 — Title TASK-9").getByRole("radio", { name: "Datenbank gilt" }));
    await userEvent.click(screen.getByRole("button", { name: "Entscheidungen übernehmen" }));

    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls[1]!.body.resolutions).toEqual([
      { kind: "item", label: "A", name: null, choice: "markdown" },
      { kind: "item", label: "B", name: null, choice: "database" },
      { kind: "item", label: "TASK-9", name: null, choice: "database" },
    ]);
  });

  it("decides one by one as before when nothing is decided for all", async () => {
    const calls = stubApi(server(answer({ conflicts: [changed("A"), changed("B")] })));
    open();

    await screen.findByRole("radiogroup", { name: "Entscheidung für A — Title A" });
    await userEvent.click(decision("A — Title A").getByRole("radio", { name: "Datei gilt" }));
    await userEvent.click(screen.getByRole("button", { name: "Entscheidungen übernehmen" }));

    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls[1]!.body.resolutions).toEqual([{ kind: "item", label: "A", name: null, choice: "markdown" }]);
  });

  it("defers all again, but keeps what was decided for a deletion", async () => {
    stubApi(server(answer({ conflicts: [changed("A"), changed("B"), deleted] })));
    open();

    await userEvent.click(await screen.findByRole("button", { name: "Datenbank gilt für alle" }));
    await userEvent.click(decision("TASK-9 — Title TASK-9").getByRole("radio", { name: "Datei gilt" }));
    await userEvent.click(screen.getByRole("button", { name: "Alle aufschieben" }));

    chosen("A — Title A", "Aufschieben");
    chosen("B — Title B", "Aufschieben");
    chosen("TASK-9 — Title TASK-9", "Datei gilt");
  });

  it("offers no decision for all when there is only one change on both sides", async () => {
    stubApi(server(answer({ conflicts: [changed("A"), deleted] })));
    open();

    await screen.findByRole("group", { name: "Konflikte" });
    expect(screen.queryByRole("button", { name: "Datenbank gilt für alle" })).not.toBeInTheDocument();
  });

  it("does not mention deletions when there are none", async () => {
    stubApi(server(answer({ conflicts: [changed("A"), changed("B")] })));
    open();

    await screen.findByText("Für alle 2 Änderungen auf beiden Seiten:");
    expect(screen.queryByText("Löschungen entscheidest du einzeln.")).not.toBeInTheDocument();
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

  it("syncs both ways unless the project says otherwise, and does not ask", async () => {
    const calls = stubApi(server(answer()));
    renderWithProviders(<SyncDialog source={sourceStatus()} mode="sync" onClose={vi.fn()} onSwitched={vi.fn()} />);

    await screen.findByText("Beide Seiten sind gleich.");
    expect(calls.map((c) => c.body.direction)).toEqual([null]);
    expect(screen.queryByRole("radio")).not.toBeInTheDocument();
    expect(screen.queryByText(/Richtung eingeschränkt/)).not.toBeInTheDocument();
  });

  it("runs the direction set for the project, says so, and keeps it on a reload", async () => {
    const calls = stubApi(server(answer()));
    renderWithProviders(<SyncDialog source={markdownWithMirror} mode="sync" onClose={vi.fn()} onSwitched={vi.fn()} />, { syncScopes: { s1: "to_md" } });

    expect(screen.getByText("Sync-Ordner: /repos/a/docs")).toBeInTheDocument();
    expect(screen.getByText("Richtung eingeschränkt (Einstellung des Projekts): Nur Datenbank → Ordner")).toBeInTheDocument();
    await screen.findByText("Beide Seiten sind gleich.");
    await userEvent.click(screen.getByRole("button", { name: "Vorschau neu laden" }));

    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls.map((c) => c.body.direction)).toEqual(["to_md", "to_md"]);
  });

  it("takes the setting of its own project only", async () => {
    const calls = stubApi(server(answer()));
    renderWithProviders(<SyncDialog source={sourceStatus()} mode="sync" onClose={vi.fn()} onSwitched={vi.fn()} />, { syncScopes: { other: "from_md" } });

    await screen.findByText("Beide Seiten sind gleich.");
    expect(calls[0]!.body.direction).toBeNull();
  });

  it("does not use the setting for a switch, which has a direction of its own", async () => {
    const calls = stubApi(server(answer()));
    renderWithProviders(<SyncDialog source={sourceStatus()} mode="switch" onClose={vi.fn()} onSwitched={vi.fn()} />, { syncScopes: { s1: "from_md" } });

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    await waitFor(() => expect(calls).toHaveLength(1));
    expect(calls[0]!.body.direction).toBe("to_md");
    expect(screen.queryByText(/Richtung eingeschränkt/)).not.toBeInTheDocument();
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

