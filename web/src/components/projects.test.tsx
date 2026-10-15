import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Schemas, SourceStatus } from "../api/client";
import { renderWithProviders, sourceStatus } from "../test/render";
import type { SyncState } from "../domain/sync";
import { Sidebar } from "./Sidebar";
import { ProjectsSection } from "./settings/ProjectsSection";
import { SETTINGS_SECTIONS } from "./settings/sections";
import { SettingsDialog } from "./settings/SettingsDialog";

type Status = Schemas["SyncStatusOut"];

const central = sourceStatus();  // database primary with the markdown mirror /repos/central
const bare = sourceStatus({ id: "s3", project: "Bare", sync_path: null, markdown_path: null, mirror: "none" });
const files = sourceStatus({
  id: "s2", project: "Files", backend: "markdown", path: "/repos/a/docs", sync_path: null, primary: "markdown", markdown_path: "/repos/a/docs", mirror: "none",
});
const switchedOff = sourceStatus({ id: "s5", project: "Off", sync_path: "/repos/off", markdown_path: "/repos/off", mirror: "none" });
const mirrored = sourceStatus({
  id: "s4", project: "Mirrored", backend: "markdown", path: "/repos/m/docs", sync_path: null, primary: "markdown", markdown_path: "/repos/m/docs", mirror: "database",
});

const status = (source: SourceStatus, state: Status["state"], last: string | null = null): Status => ({
  source_id: source.id, state, last_sync_at: last, conflicts: 0, auto_sync: false, auto_last_run_at: null, auto_paused: null,
});

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
    ["conflicts", "Konflikte warten auf eine Entscheidung"],
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

describe("ProjectsSection: the automatic sync", () => {
  afterEach(() => vi.unstubAllGlobals());
  const auto = sourceStatus({ auto_sync: true });
  const autoStatus = (over: Partial<Status> = {}): Status => ({ ...status(auto, "in_sync"), auto_sync: true, ...over });

  it("is off by default and switched on by the owner, who is not asked anything else", async () => {
    const calls = stub([central], [status(central, "in_sync")], (request) => (request.method === "PUT" ? jsonResponse({ ...central, auto_sync: true }) : jsonResponse({}, 404)));
    renderWithProviders(<ProjectsSection />);

    const box = await within(await screen.findByRole("group", { name: "Central" })).findByRole("checkbox", { name: /Automatisch abgleichen/ });
    expect(box).not.toBeChecked();
    await userEvent.click(box);

    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true));
    expect(calls.find((c) => c.method === "PUT")!.body).toMatchObject({ project: "Central", auto_sync: true });
  });

  it("cannot be switched on without a mirror", async () => {
    stub([bare], [status(bare, "none")]);
    renderWithProviders(<ProjectsSection />);

    expect(await within(await screen.findByRole("group", { name: "Bare" })).findByRole("checkbox", { name: /Automatisch abgleichen/ })).toBeDisabled();
  });

  it("shows the last run when it is on, and the reason when it is paused", async () => {
    stub([auto], [autoStatus({ auto_last_run_at: "2026-10-14T09:30:00+02:00" })]);
    const { unmount } = renderWithProviders(<ProjectsSection />);
    expect(await screen.findByText(/Auto-Sync: letzter Lauf .*2026/)).toBeInTheDocument();
    unmount();

    stub([auto], [autoStatus({ auto_paused: "merge_markers" })]);
    renderWithProviders(<ProjectsSection />);
    expect(await screen.findByText(/Auto-Sync pausiert: Git-Merge-Marker/)).toBeInTheDocument();
  });

  it("names the open conflicts, which wait for a decision in the sync dialog", async () => {
    stub([auto], [autoStatus({ conflicts: 2 })]);
    renderWithProviders(<ProjectsSection />);

    expect(await screen.findByText("2 offene Konflikte: im Sync-Dialog entscheiden")).toBeInTheDocument();
  });

  it("shows nothing about it for a project that has it off", async () => {
    stub([central], [status(central, "in_sync")]);
    renderWithProviders(<ProjectsSection />);

    await screen.findByText("In Sync");
    expect(screen.queryByText(/Auto-Sync:/)).not.toBeInTheDocument();
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

  it("syncs in both directions unless the run is restricted to one", async () => {
    const section = { created: [], changed: [], unchanged: 0 };
    const calls = stub([mirrored], [status(mirrored, "mirror_changed")], () => jsonResponse({ executed: false, token: "t", items: section, documents: section, topics: section, notes: section, note_documents: section, conflicts: [], skipped: [], resolved: [], deleted: [], deferred: [], kept: [] }));
    renderWithProviders(<ProjectsSection />);

    await userEvent.click(within(await screen.findByRole("group", { name: "Mirrored" })).getByRole("button", { name: "Sync…" }));
    expect(screen.getByRole("radio", { name: /In beide Richtungen/ })).toBeChecked();
    await userEvent.click(screen.getByRole("button", { name: "Vorschau" }));

    await waitFor(() => expect(calls.some((c) => c.path === "/api/v2/sources/s4/sync")).toBe(true));
    expect(calls.find((c) => c.path === "/api/v2/sources/s4/sync")!.body.direction).toBeNull();
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

  it("switches the markdown mirror of a database project off and keeps its folder", async () => {
    const calls = stub([central], [status(central, "in_sync")], () => jsonResponse({ ...central, mirror: "none" }));
    renderWithProviders(<ProjectsSection />);

    await userEvent.click(within(await screen.findByRole("group", { name: "Central" })).getByRole("button", { name: "Spiegel ausschalten" }));

    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true));
    expect(calls.find((c) => c.method === "PUT")!.body).toEqual({ path: "", project: "Central", sync_path: "/repos/central", mirror: "none" });
  });

  it("switches it on again without asking for a folder", async () => {
    const calls = stub([switchedOff], [status(switchedOff, "none")], () => jsonResponse({ ...switchedOff, mirror: "markdown" }));
    renderWithProviders(<ProjectsSection />);

    const group = await screen.findByRole("group", { name: "Off" });
    expect(within(group).getByText("/repos/off")).toBeInTheDocument();  // the folder is still there
    expect(within(group).getByText("Markdown-Spiegel aus")).toBeInTheDocument();
    expect(within(group).getByRole("button", { name: "Sync…" })).toBeDisabled();
    await userEvent.click(within(group).getByRole("button", { name: "Spiegel einschalten" }));

    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(calls.find((c) => c.method === "PUT")!.body).toEqual({ path: "", project: "Off", sync_path: "/repos/off", mirror: "markdown" });
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

describe("Sidebar: the badge for a changed mirror", () => {
  const options = { projects: ["Central", "Files"], statuses: [], priorities: [] };
  const show = (states: [string, SyncState][], onOpenProject = vi.fn()) =>
    renderWithProviders(
      <Sidebar
        options={options}
        sources={[central, files]}
        syncStates={new Map(states)}
        onAddSource={vi.fn()}
        onEditSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onSyncSource={vi.fn()}
        onOpenSettings={vi.fn()}
        onOpenProject={onOpenProject}
      />,
    );

  it.each(["mirror_changed", "both_changed", "unreadable", "conflicts"] as const)("marks a project whose state is %s", (state) => {
    show([["s1", state]]);

    expect(screen.getAllByRole("button", { name: /Central: .* Einstellungen/ })).toHaveLength(1);
    expect(screen.queryByRole("button", { name: /Files: .* Einstellungen/ })).not.toBeInTheDocument();
  });

  it("marks a project with open conflicts although its state says in sync, and names them", () => {
    renderWithProviders(
      <Sidebar
        options={options} sources={[central, files]} syncStates={new Map([["s1", "in_sync" as SyncState]])} syncConflicts={new Map([["s1", 3]])}
        onAddSource={vi.fn()} onEditSource={vi.fn()} onRemoveSource={vi.fn()} onSyncSource={vi.fn()} onOpenSettings={vi.fn()} onOpenProject={vi.fn()}
      />,
    );

    expect(screen.getByRole("button", { name: /Central: .* Einstellungen/ })).toHaveAttribute("title", "3 offene Konflikte");
  });

  it.each(["none", "in_sync", "primary_changed", "unknown"] as const)("does not mark a project whose state is %s", (state) => {
    show([["s1", state], ["s2", state]]);

    expect(screen.queryByRole("button", { name: /: .* Einstellungen/ })).not.toBeInTheDocument();
  });

  it("names the state and opens the settings at that project", async () => {
    const onOpenProject = vi.fn();
    show([["s1", "mirror_changed"]], onOpenProject);

    const badge = screen.getByRole("button", { name: /Central: .* Einstellungen/ });
    expect(badge).toHaveAttribute("title", "Spiegel geändert seit dem letzten Sync");
    await userEvent.click(badge);

    expect(onOpenProject).toHaveBeenCalledWith(central);
  });
});

