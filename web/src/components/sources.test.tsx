import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { SourceStatus } from "../api/client";
import { renderWithProviders, sourceStatus } from "../test/render";
import { Sidebar } from "./Sidebar";
import { SourceDialog } from "./SourceDialog";

const listing = { path: "/repos", parent: "/", has_todo: false, dirs: [{ name: "docs", has_todo: true }], error: null };

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

/** Answers the folder browser; every other request goes to `handler`. */
function stubApi(handler: (request: Request) => Promise<Response>) {
  const calls: Request[] = [];
  vi.stubGlobal("fetch", async (request: Request) => {
    if (new URL(request.url).pathname === "/api/v2/folders") return jsonResponse(listing);
    calls.push(request.clone());
    return handler(request);
  });
  return calls;
}

const saved = (over: Partial<SourceStatus> = {}) => jsonResponse(sourceStatus(over));

describe("SourceDialog: choosing where a project is stored", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("adds a database project by name, with a sync folder only if one is chosen", async () => {
    const calls = stubApi(async () => saved());
    const onSaved = vi.fn();
    renderWithProviders(<SourceDialog source={null} onSaved={onSaved} onClose={vi.fn()} />);

    await userEvent.click(screen.getByRole("radio", { name: "Datenbank" }));
    expect(screen.queryByPlaceholderText("/pfad/zu/docs/todo")).toHaveValue("");  // the browser's start folder is not taken over
    await userEvent.type(screen.getByLabelText("Projektname"), "Central");
    await userEvent.click(screen.getByRole("button", { name: "OK" }));

    await waitFor(() => expect(onSaved).toHaveBeenCalledWith("Central"));
    expect([calls[0]!.method, new URL(calls[0]!.url).pathname]).toEqual(["POST", "/api/v2/sources"]);
    expect(await calls[0]!.json()).toEqual({ path: "", project: "Central", backend: "database" });
  });

  it("sends the chosen sync folder of a new database project", async () => {
    const calls = stubApi(async () => saved());
    renderWithProviders(<SourceDialog source={null} onSaved={vi.fn()} onClose={vi.fn()} />);

    await userEvent.click(screen.getByRole("radio", { name: "Datenbank" }));
    await userEvent.type(screen.getByLabelText("Projektname"), "Central");
    await userEvent.type(screen.getByLabelText("Sync-Ordner (optional, enthält TODO.md)"), "/repos/central");
    await userEvent.click(screen.getByRole("button", { name: "OK" }));

    await waitFor(() => expect(calls).toHaveLength(1));
    expect(await calls[0]!.json()).toEqual({ path: "", project: "Central", backend: "database", sync_path: "/repos/central" });
  });

  it("wants a name for a database project and sends nothing without it", async () => {
    const calls = stubApi(async () => saved());
    renderWithProviders(<SourceDialog source={null} onSaved={vi.fn()} onClose={vi.fn()} />);

    await userEvent.click(screen.getByRole("radio", { name: "Datenbank" }));
    await userEvent.click(screen.getByRole("button", { name: "OK" }));

    expect(await screen.findByText("Dieses Feld darf nicht leer sein.")).toBeInTheDocument();
    expect(calls).toHaveLength(0);
  });

  it("preselects the backend chosen in the settings, and the user can still pick the other", async () => {
    stubApi(async () => saved());
    renderWithProviders(<SourceDialog source={null} onSaved={vi.fn()} onClose={vi.fn()} />, {
      defaultBackend: "database",
    });

    expect(screen.getByRole("radio", { name: "Datenbank" })).toBeChecked();
    expect(screen.getByLabelText("Projektname")).toHaveAttribute("placeholder", "Name des Projekts");
    await userEvent.click(screen.getByRole("radio", { name: "Markdown-Ordner" }));
    expect(screen.getByRole("radio", { name: "Markdown-Ordner" })).toBeChecked();
  });

  it("does not change the backend of a project that exists", () => {
    stubApi(async () => saved());
    renderWithProviders(
      <SourceDialog source={sourceStatus({ backend: "markdown", path: "/repos/a/docs", sync_path: null })} part="folder" onSaved={vi.fn()} onClose={vi.fn()} />,
      { defaultBackend: "database" },
    );

    expect(screen.getByText("Gespeichert in: Markdown-Ordner")).toBeInTheDocument();
  });

  it("still adds a markdown project by its folder", async () => {
    const calls = stubApi(async () => saved({ backend: "markdown", path: "/repos/a/docs", sync_path: null }));
    renderWithProviders(<SourceDialog source={null} onSaved={vi.fn()} onClose={vi.fn()} />);

    expect(screen.getByRole("radio", { name: "Markdown-Ordner" })).toBeChecked();
    await waitFor(() => expect(screen.getByPlaceholderText("/pfad/zu/docs/todo")).toHaveValue("/repos"));  // follows the browser
    await userEvent.clear(screen.getByPlaceholderText("/pfad/zu/docs/todo"));
    await userEvent.type(screen.getByPlaceholderText("/pfad/zu/docs/todo"), "/repos/a/docs");
    await userEvent.click(screen.getByRole("button", { name: "OK" }));

    await waitFor(() => expect(calls).toHaveLength(1));
    expect(await calls[0]!.json()).toEqual({ path: "/repos/a/docs", project: "", backend: "markdown" });
  });

  it("shows a translated error of the server and stays open", async () => {
    stubApi(async () => jsonResponse({ code: "duplicate", message: "x", details: {} }, 409));
    const onSaved = vi.fn();
    renderWithProviders(<SourceDialog source={null} onSaved={onSaved} onClose={vi.fn()} />);

    await userEvent.type(screen.getByPlaceholderText("/pfad/zu/docs/todo"), "/repos/a/docs");
    await userEvent.click(screen.getByRole("button", { name: "OK" }));

    expect(await screen.findByText("Dieser Ordner ist bereits eingetragen.")).toBeInTheDocument();
    expect(onSaved).not.toHaveBeenCalled();
  });
});

describe("SourceDialog: an existing project", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("only renames: no storage, no folder, no sync or switch buttons", () => {
    stubApi(async () => saved());
    renderWithProviders(<SourceDialog source={sourceStatus()} onSaved={vi.fn()} onClose={vi.fn()} />);

    expect(screen.getByRole("dialog", { name: "Projekt umbenennen" })).toBeInTheDocument();
    expect(screen.getByLabelText("Projektname")).toHaveValue("Central");
    expect(screen.queryByRole("radio")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Sync-Ordner (optional, enthält TODO.md)")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Sync|ablegen|übernehmen/ })).not.toBeInTheDocument();
  });

  it("renames a database project and keeps its mirror folder", async () => {
    const calls = stubApi(async () => saved({ project: "Renamed" }));
    const onSaved = vi.fn();
    renderWithProviders(<SourceDialog source={sourceStatus()} onSaved={onSaved} onClose={vi.fn()} />);

    await userEvent.clear(screen.getByLabelText("Projektname"));
    await userEvent.type(screen.getByLabelText("Projektname"), "Renamed");
    await userEvent.click(screen.getByRole("button", { name: "OK" }));

    await waitFor(() => expect(onSaved).toHaveBeenCalledWith("Renamed"));
    expect([calls[0]!.method, new URL(calls[0]!.url).pathname]).toEqual(["PUT", "/api/v2/sources/s1"]);
    expect(await calls[0]!.json()).toEqual({ path: "", project: "Renamed", sync_path: "/repos/central" });
  });

  it("renames a markdown project and keeps its folder", async () => {
    const calls = stubApi(async () => saved({ backend: "markdown", project: "Docs" }));
    const source = sourceStatus({ backend: "markdown", path: "/repos/a/docs", sync_path: null, primary: "markdown", markdown_path: "/repos/a/docs", mirror: "none" });
    renderWithProviders(<SourceDialog source={source} onSaved={vi.fn()} onClose={vi.fn()} />);

    await userEvent.clear(screen.getByLabelText("Projektname"));
    await userEvent.type(screen.getByLabelText("Projektname"), "Docs");
    await userEvent.click(screen.getByRole("button", { name: "OK" }));

    await waitFor(() => expect(calls).toHaveLength(1));
    expect(await calls[0]!.json()).toEqual({ path: "/repos/a/docs", project: "Docs" });
  });

  it("changes only the folder when opened for the folder, and clears the mirror folder of a database project when emptied", async () => {
    const calls = stubApi(async () => saved({ sync_path: null }));
    renderWithProviders(<SourceDialog source={sourceStatus()} part="folder" onSaved={vi.fn()} onClose={vi.fn()} />);

    expect(screen.queryByLabelText("Projektname")).not.toBeInTheDocument();
    await userEvent.clear(screen.getByLabelText("Sync-Ordner (optional, enthält TODO.md)"));
    await userEvent.click(screen.getByRole("button", { name: "OK" }));

    await waitFor(() => expect(calls).toHaveLength(1));
    expect([calls[0]!.method, new URL(calls[0]!.url).pathname]).toEqual(["PUT", "/api/v2/sources/s1"]);
    expect(await calls[0]!.json()).toEqual({ path: "", project: "Central", sync_path: "" });
  });
});

describe("Sidebar: projects in the database", () => {
  const options = { projects: ["Central", "Files", "Manual"], statuses: [], priorities: [] };
  const files = sourceStatus({ id: "s2", project: "Files", backend: "markdown", path: "/repos/a/docs", sync_path: null, primary: "markdown", markdown_path: "/repos/a/docs", mirror: "none" });
  const show = (sources = [sourceStatus(), files], onSyncSource = vi.fn()) =>
    renderWithProviders(
      <Sidebar options={options} sources={sources} onAddSource={vi.fn()} onEditSource={vi.fn()} onRemoveSource={vi.fn()} onSyncSource={onSyncSource} onOpenSettings={vi.fn()} syncStates={new Map()} onOpenProject={vi.fn()} />,
    );

  it("marks database projects and syncs only those that have a sync folder", async () => {
    const onSyncSource = vi.fn();
    show([sourceStatus(), files], onSyncSource);

    expect(screen.getAllByTitle("Gespeichert in der Datenbank")).toHaveLength(1);
    expect(screen.getAllByRole("button", { name: "Sync mit dem Markdown-Ordner" })).toHaveLength(1);
    await userEvent.click(screen.getByRole("button", { name: "Sync mit dem Markdown-Ordner" }));

    expect(onSyncSource).toHaveBeenCalledWith(sourceStatus());
  });

  it("shows a symbol for a project that syncs automatically, and for no other", () => {
    show([sourceStatus({ auto_sync: true }), sourceStatus({ id: "s3", project: "Manual" }), files]);

    expect(screen.getAllByRole("img", { name: "Sync automatisch" })).toHaveLength(1);
  });

  it("offers no sync for a database project without a sync folder", () => {
    show([sourceStatus({ sync_path: null, markdown_path: null, mirror: "none" })]);

    expect(screen.queryByRole("button", { name: "Sync mit dem Markdown-Ordner" })).not.toBeInTheDocument();
  });
});
