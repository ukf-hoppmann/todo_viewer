import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Schemas, SourceStatus } from "../api/client";
import { renderWithProviders, sourceStatus } from "../test/render";
import { ProjectsSection } from "./settings/ProjectsSection";
import { SETTINGS_SECTIONS } from "./settings/sections";
import { SettingsDialog } from "./settings/SettingsDialog";

type Status = Schemas["SyncStatusOut"];

const central = sourceStatus();  // database primary with the markdown mirror /repos/central
const bare = sourceStatus({ id: "s3", project: "Bare", sync_path: null, markdown_path: null, mirror: "none" });
const files = sourceStatus({
  id: "s2", project: "Files", backend: "markdown", path: "/repos/a/docs", sync_path: null, primary: "markdown", markdown_path: "/repos/a/docs", mirror: "none",
});
const mirrored = sourceStatus({
  id: "s4", project: "Mirrored", backend: "markdown", path: "/repos/m/docs", sync_path: null, primary: "markdown", markdown_path: "/repos/m/docs", mirror: "database",
});

const status = (source: SourceStatus, state: Status["state"], last: string | null = null): Status => ({ source_id: source.id, state, last_sync_at: last });

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

/** Serves the projects and their states; everything else goes to `other`. Records every request. */
function stub(sources: SourceStatus[], states: Status[], other: (request: Request, body: Record<string, unknown>) => Response = () => jsonResponse({}, 404)) {
  const calls: { method: string; path: string; body: Record<string, unknown> }[] = [];
  vi.stubGlobal("fetch", async (request: Request) => {
    const path = new URL(request.url).pathname;
    const raw = await request.clone().text();
    const body = raw ? (JSON.parse(raw) as Record<string, unknown>) : {};
    calls.push({ method: request.method, path, body });
    if (path === "/api/v2/backlog") return jsonResponse({ sources, items: [] });
    if (path === "/api/v2/sync-status") return jsonResponse(states);
    if (path === "/api/v2/folders") return jsonResponse({ path: "/repos", parent: "/", has_todo: false, dirs: [], error: null });
    return other(request, body);
  });
  return calls;
}

const card = (name: string) => screen.getByRole("group", { name });

describe("ProjectsSection: one card per project", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("shows primary source, folder, mirror, state and last sync of every project", async () => {
    stub([central, files], [status(central, "in_sync", "2026-09-30T10:00:00+02:00"), status(files, "none")]);
    renderWithProviders(<ProjectsSection />);

    const db = await screen.findByRole("group", { name: "Central" });
    expect(within(db).getByText("Datenbank", { selector: ".project-primary" })).toBeInTheDocument();
    expect(within(db).getByText("/repos/central")).toBeInTheDocument();
    expect(await within(db).findByText("In Sync")).toBeInTheDocument();
    expect(within(db).getByText(/Letzter Sync: .*2026/)).toBeInTheDocument();

    const md = card("Files");
    expect(within(md).getByText("Markdown-Ordner", { selector: ".project-primary" })).toBeInTheDocument();
    expect(within(md).getByText("/repos/a/docs")).toBeInTheDocument();
    expect(await within(md).findByText("Kein Spiegel")).toBeInTheDocument();
  });

  it.each([
    ["mirror_changed", "Spiegel geändert seit dem letzten Sync"],
    ["primary_changed", "Primärquelle geändert seit dem letzten Sync"],
    ["both_changed", "Beide Seiten geändert"],
    ["unknown", "Noch nie synchronisiert, die Seiten unterscheiden sich"],
    ["unreadable", "Eine Seite ist nicht lesbar"],
  ] as const)("says what %s means", async (state, text) => {
    stub([central], [status(central, state)]);
    renderWithProviders(<ProjectsSection />);

    expect(await within(await screen.findByRole("group", { name: "Central" })).findByText(text)).toBeInTheDocument();
  });

  it("has never synced when there is no last sync", async () => {
    stub([central], [status(central, "unknown")]);
    renderWithProviders(<ProjectsSection />);

    expect(await screen.findByText("Letzter Sync: noch nie")).toBeInTheDocument();
  });

  it("asks for the state again by hand, and only then", async () => {
    const calls = stub([central], [status(central, "in_sync")]);
    renderWithProviders(<ProjectsSection />);
    await screen.findByText("In Sync");
    const asked = () => calls.filter((c) => c.path === "/api/v2/sync-status").length;
    const before = asked();

    await userEvent.click(screen.getByRole("button", { name: "Status prüfen" }));

    await waitFor(() => expect(asked()).toBe(before + 1));
  });

  it("marks the project the menu was opened for", async () => {
    stub([central, files], [status(central, "in_sync"), status(files, "none")]);
    renderWithProviders(<ProjectsSection focusId="s2" />);

    await screen.findByRole("group", { name: "Files" });
    expect(card("Files")).toHaveAttribute("aria-current", "true");
    expect(card("Central")).not.toHaveAttribute("aria-current");
  });
});

describe("ProjectsSection: switching the primary source and syncing", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("switches a markdown project to the database through the sync dialog", async () => {
    stub([files], [status(files, "none")]);
    renderWithProviders(<ProjectsSection />);

    await userEvent.click(within(await screen.findByRole("group", { name: "Files" })).getByRole("button", { name: "Primärquelle wechseln…" }));

    expect(screen.getByRole("dialog", { name: "„Files“ in die Datenbank übernehmen" })).toBeInTheDocument();
    expect(screen.getByText(/legt der Dienst ein Backup/)).toBeInTheDocument();
  });

  it("switches a database project with a mirror folder back to markdown", async () => {
    stub([central], [status(central, "in_sync")]);
    renderWithProviders(<ProjectsSection />);

    await userEvent.click(within(await screen.findByRole("group", { name: "Central" })).getByRole("button", { name: "Primärquelle wechseln…" }));

    expect(screen.getByRole("dialog", { name: "„Central“ als Markdown-Ordner ablegen" })).toBeInTheDocument();
  });

  it("cannot switch a database project that has no markdown folder to switch to", async () => {
    stub([bare], [status(bare, "none")]);
    renderWithProviders(<ProjectsSection />);

    const group = await screen.findByRole("group", { name: "Bare" });
    expect(within(group).getByRole("button", { name: "Primärquelle wechseln…" })).toBeDisabled();
    expect(within(group).getByRole("button", { name: "Sync…" })).toBeDisabled();
  });

  it("syncs from the primary source to the mirror unless the other direction is chosen", async () => {
    const calls = stub([mirrored], [status(mirrored, "mirror_changed")], () => jsonResponse({ executed: false, token: "t", items: { created: [], changed: [], unchanged: 0, missing: [] }, documents: { created: [], changed: [], unchanged: 0, missing: [] }, skipped: [], deleted: [], kept: [] }));
    renderWithProviders(<ProjectsSection />);

    await userEvent.click(within(await screen.findByRole("group", { name: "Mirrored" })).getByRole("button", { name: "Sync…" }));
    expect(screen.getByRole("radio", { name: "Ordner → Datenbank (Standard)" })).toBeChecked();
    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    await waitFor(() => expect(calls.some((c) => c.path === "/api/v2/sources/s4/sync")).toBe(true));
    expect(calls.find((c) => c.path === "/api/v2/sources/s4/sync")!.body.direction).toBe("from_md");
  });

  it("closes only the dialog on top when Escape is pressed", async () => {
    stub([files], [status(files, "none")]);
    renderWithProviders(<SettingsDialog initialSection="projects" onClose={vi.fn()} />);

    await userEvent.click(within(await screen.findByRole("group", { name: "Files" })).getByRole("button", { name: "Primärquelle wechseln…" }));
    await userEvent.keyboard("{Escape}");

    expect(screen.queryByRole("dialog", { name: "„Files“ in die Datenbank übernehmen" })).not.toBeInTheDocument();
    expect(screen.getByRole("dialog", { name: "Einstellungen" })).toBeInTheDocument();
  });
});

describe("ProjectsSection: folders and mirrors", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("changes the markdown folder in a dialog of its own, which asks for nothing else", async () => {
    stub([files], [status(files, "none")]);
    renderWithProviders(<ProjectsSection />);

    await userEvent.click(within(await screen.findByRole("group", { name: "Files" })).getByRole("button", { name: "Ordner ändern…" }));

    expect(screen.getByRole("dialog", { name: "Projektordner ändern" })).toBeInTheDocument();
    expect(screen.queryByLabelText("Projektname")).not.toBeInTheDocument();
  });

  it("sets up the mirror folder of a database project that has none", async () => {
    stub([bare], [status(bare, "none")]);
    renderWithProviders(<ProjectsSection />);

    await userEvent.click(within(await screen.findByRole("group", { name: "Bare" })).getByRole("button", { name: "Spiegel-Ordner festlegen…" }));

    expect(screen.getByRole("dialog", { name: "Spiegel-Ordner ändern" })).toBeInTheDocument();
  });

  it("keeps a database mirror of a markdown project when asked, and sends the mirror only", async () => {
    const calls = stub([files], [status(files, "none")], () => jsonResponse({ ...files, mirror: "database" }));
    renderWithProviders(<ProjectsSection />);

    await userEvent.click(within(await screen.findByRole("group", { name: "Files" })).getByRole("checkbox", { name: "Datenbank-Spiegel führen" }));

    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true));
    const put = calls.find((c) => c.method === "PUT")!;
    expect(put.path).toBe("/api/v2/sources/s2");
    expect(put.body).toEqual({ path: "/repos/a/docs", project: "Files", mirror: "database" });
  });

  it("asks before dropping the database mirror, because that deletes the copy in the database", async () => {
    const calls = stub([mirrored], [status(mirrored, "in_sync")], () => jsonResponse({ ...mirrored, mirror: "none" }));
    const confirm = vi.spyOn(window, "confirm").mockReturnValueOnce(false).mockReturnValueOnce(true);
    renderWithProviders(<ProjectsSection />);
    const box = within(await screen.findByRole("group", { name: "Mirrored" })).getByRole("checkbox", { name: "Datenbank-Spiegel führen" });
    expect(box).toBeChecked();

    await userEvent.click(box);
    expect(calls.some((c) => c.method === "PUT")).toBe(false);  // declined
    await userEvent.click(box);

    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true));
    expect(calls.find((c) => c.method === "PUT")!.body).toEqual({ path: "/repos/m/docs", project: "Mirrored", mirror: "none" });
    expect(confirm.mock.calls[0]![0]).toMatch(/Kopie in der Datenbank/);
    confirm.mockRestore();
  });

  it("removes the markdown mirror of a database project", async () => {
    const calls = stub([central], [status(central, "in_sync")], () => jsonResponse({ ...central, sync_path: null, markdown_path: null, mirror: "none" }));
    renderWithProviders(<ProjectsSection />);

    await userEvent.click(within(await screen.findByRole("group", { name: "Central" })).getByRole("button", { name: "Spiegel entfernen" }));

    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true));
    expect(calls.find((c) => c.method === "PUT")!.body).toEqual({ path: "", project: "Central", sync_path: "", mirror: "none" });
  });

  it("shows a translated error of the server and changes nothing on screen", async () => {
    stub([files], [status(files, "none")], () => jsonResponse({ code: "duplicate", message: "x", details: {} }, 409));
    renderWithProviders(<ProjectsSection />);

    await userEvent.click(within(await screen.findByRole("group", { name: "Files" })).getByRole("checkbox", { name: "Datenbank-Spiegel führen" }));

    expect(await screen.findByText("Dieser Ordner ist bereits eingetragen.")).toBeInTheDocument();
    expect(within(card("Files")).getByRole("checkbox", { name: "Datenbank-Spiegel führen" })).not.toBeChecked();
  });
});

describe("Settings: the section list", () => {
  it("offers the projects next to the general settings", () => {
    stub([], []);
    renderWithProviders(<SettingsDialog onClose={vi.fn()} />);

    expect(SETTINGS_SECTIONS.map((s) => s.id)).toEqual(["general", "projects"]);
    expect(screen.getByRole("button", { name: "Projekte" })).toBeInTheDocument();
  });

  it("opens at the projects when the menu is opened for one project", async () => {
    stub([files], [status(files, "none")]);
    renderWithProviders(<SettingsDialog initialSection="projects" focusId="s2" onClose={vi.fn()} />);

    expect(await screen.findByRole("group", { name: "Files" })).toHaveAttribute("aria-current", "true");
  });
});
