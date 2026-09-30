import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Schemas } from "../api/client";
import { renderWithProviders, sourceStatus } from "../test/render";
import { SyncDialog } from "./SyncDialog";

type Out = Schemas["SyncOut"];
type Section = Schemas["SyncSectionOut"];

const entry = (label: string, name: string | null = null) => ({ label, title: `Title ${label}`, name });
const section = (over: Partial<Section> = {}): Section => ({ created: [], changed: [], unchanged: 0, missing: [], ...over });
const answer = (over: Partial<Out> = {}): Out => ({
  executed: false,
  token: "tok-1",
  items: section(),
  documents: section(),
  skipped: [],
  deleted: [],
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
  items: section({ created: [entry("TASK-1")], changed: [entry("TASK-2")], unchanged: 4, missing: [entry("TASK-9")] }),
  documents: section({ created: [entry("TASK-1", "TASK-1_notes.md")], unchanged: 2 }),
  skipped: [entry("TASK-3", "items/TASK-3/x.md")],
});

/** Preview first; a confirmed request answers like the server does, with the outcome. */
const server = (preview: Out, executed: Partial<Out> = {}) => (_: Request, body: Record<string, unknown>) =>
  jsonResponse(body.confirm ? { ...preview, executed: true, ...executed } : preview);

describe("SyncDialog: syncing a database project", () => {
  afterEach(() => vi.unstubAllGlobals());
  const source = sourceStatus();
  const open = (onClose = vi.fn()) => renderWithProviders(<SyncDialog source={source} mode="sync" onClose={onClose} onSwitched={vi.fn()} />);

  it("asks for a preview first and shows what would happen, with the entries only the target has as a warning", async () => {
    const calls = stubApi(server(previewWith));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    expect(await screen.findByText("1 neu · 1 geändert · 4 unverändert")).toBeInTheDocument();
    expect(screen.getByText("1 neu · 0 geändert · 2 unverändert")).toBeInTheDocument();
    expect(calls).toEqual([{ method: "POST", path: "/api/v2/sources/s1/sync", body: { direction: "to_md", confirm: false, delete_missing: false, language: "de" } }]);
    const warning = screen.getByRole("group", { name: "Nur auf dem Ziel vorhanden" });
    expect(within(warning).getByText("TASK-9 — Title TASK-9")).toBeInTheDocument();
    expect(screen.getByText("≠ TASK-2 — Title TASK-2")).toBeInTheDocument();  // marked as overwritten
    expect(screen.getByText(/items\/TASK-3\/x\.md/)).toBeInTheDocument();
    expect(screen.getByRole("checkbox", { name: "Diese Einträge auf dem Ziel löschen" })).not.toBeChecked();
  });

  it("carries the sync out with the token of the preview and keeps missing entries unless told to delete them", async () => {
    const calls = stubApi(server(previewWith, { kept: [entry("TASK-9")] }));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await userEvent.click(await screen.findByRole("button", { name: "Ausführen" }));

    expect(await screen.findByText("Sync abgeschlossen.")).toBeInTheDocument();
    expect(calls[1]!.body).toEqual({ direction: "to_md", confirm: true, token: "tok-1", delete_missing: false, language: "de" });
    expect(screen.getByText("Fehlende Einträge, die stehen geblieben sind: 1")).toBeInTheDocument();
  });

  it("deletes the missing entries only when the box is ticked", async () => {
    const calls = stubApi(server(previewWith, { deleted: [entry("TASK-9")] }));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await userEvent.click(await screen.findByRole("checkbox", { name: "Diese Einträge auf dem Ziel löschen" }));
    await userEvent.click(screen.getByRole("button", { name: "Ausführen" }));

    expect(await screen.findByText("Gelöscht: 1")).toBeInTheDocument();
    expect(calls[1]!.body).toMatchObject({ confirm: true, delete_missing: true });
  });

  it("changing the direction drops the preview and sends the other direction", async () => {
    const calls = stubApi(server(previewWith));
    open();

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await screen.findByText("1 neu · 1 geändert · 4 unverändert");
    await userEvent.click(screen.getByRole("radio", { name: "Ordner → Datenbank" }));

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
    expect(calls[1]!.body).toMatchObject({ confirm: true, token: "tok-1", delete_missing: false });
    expect(calls[2]!.body).toEqual({ path: "", backend: "database" });
  });

  it("does not switch while entries only the target has would remain, unless they are deleted", async () => {
    const calls = stubApi(switching(answer({ items: section({ missing: [entry("TASK-9")] }) })));
    const onSwitched = vi.fn();
    renderWithProviders(<SyncDialog source={markdown} mode="switch" onClose={vi.fn()} onSwitched={onSwitched} />);

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    const button = await screen.findByRole("button", { name: "Übernehmen und umstellen" });
    expect(button).toBeDisabled();
    expect(screen.getByText("Zum Umstellen müssen beide Seiten gleich sein: die fehlenden Einträge müssen gelöscht werden.")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("checkbox", { name: "Diese Einträge auf dem Ziel löschen" }));
    expect(button).toBeEnabled();
    await userEvent.click(button);

    await waitFor(() => expect(onSwitched).toHaveBeenCalled());
    expect(calls[1]!.body).toMatchObject({ confirm: true, delete_missing: true });
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

  it("starts from the primary source to the mirror and says so", () => {
    stubApi(server(answer()));
    const { unmount } = renderWithProviders(<SyncDialog source={sourceStatus()} mode="sync" onClose={vi.fn()} onSwitched={vi.fn()} />);

    expect(screen.getByRole("radio", { name: /Datenbank → Ordner/ })).toBeChecked();
    expect(screen.getByRole("radio", { name: "Datenbank → Ordner (Standard)" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Ordner → Datenbank" })).not.toBeChecked();
    unmount();

    renderWithProviders(<SyncDialog source={markdownWithMirror} mode="sync" onClose={vi.fn()} onSwitched={vi.fn()} />);
    expect(screen.getByRole("radio", { name: "Ordner → Datenbank (Standard)" })).toBeChecked();
    expect(screen.getByText("Sync-Ordner: /repos/a/docs")).toBeInTheDocument();
  });

  it("previews a markdown project with a database mirror from the folder, and the other way when asked", async () => {
    const calls = stubApi(server(answer()));
    renderWithProviders(<SyncDialog source={markdownWithMirror} mode="sync" onClose={vi.fn()} onSwitched={vi.fn()} />);

    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));
    await waitFor(() => expect(calls).toHaveLength(1));
    await userEvent.click(screen.getByRole("radio", { name: "Datenbank → Ordner" }));
    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls.map((c) => c.body.direction)).toEqual(["from_md", "to_md"]);
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

