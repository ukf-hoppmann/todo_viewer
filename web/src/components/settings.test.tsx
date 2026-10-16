import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../test/render";
import { Sidebar } from "./Sidebar";
import { SETTINGS_SECTIONS, type SettingsSection } from "./settings/sections";
import { SettingsDialog } from "./settings/SettingsDialog";

const storage = { kind: "sqlite", location: "/data/configs/todo.db", schema_version: 4 };

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function stubStorage(answer: () => Response = () => jsonResponse(storage)) {
  vi.stubGlobal("fetch", async (request: Request) => {
    if (new URL(request.url).pathname === "/api/v2/storage") return answer();
    return jsonResponse({}, 404);
  });
}

const extra: SettingsSection = { id: "extra", titleKey: "tab.kanban", Component: () => <p>Extra content</p> };

describe("SettingsDialog: sections from a list", () => {
  beforeEach(() => stubStorage());
  afterEach(() => vi.unstubAllGlobals());

  it("lists the registered sections as navigation and opens the first one", async () => {
    renderWithProviders(<SettingsDialog onClose={vi.fn()} />);

    expect(screen.getByRole("dialog", { name: "Einstellungen" })).toBeInTheDocument();
    const navigation = screen.getByRole("navigation", { name: "Abschnitte" });
    expect(navigation.querySelectorAll("button")).toHaveLength(SETTINGS_SECTIONS.length);
    expect(screen.getByRole("button", { name: "Allgemein" })).toHaveAttribute("aria-current", "page");
    expect(await screen.findByText("sqlite")).toBeInTheDocument();
  });

  it("shows an entry added to the list without any other change, and switches to it", async () => {
    renderWithProviders(<SettingsDialog sections={[...SETTINGS_SECTIONS, extra]} onClose={vi.fn()} />);

    expect(screen.getByRole("navigation", { name: "Abschnitte" }).querySelectorAll("button")).toHaveLength(
      SETTINGS_SECTIONS.length + 1,
    );
    expect(screen.queryByText("Extra content")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Kanban" }));

    expect(screen.getByText("Extra content")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Kanban" })).toHaveAttribute("aria-current", "page");
    expect(screen.queryByText("sqlite")).not.toBeInTheDocument();
  });

  it("opens at the requested section", () => {
    renderWithProviders(<SettingsDialog sections={[...SETTINGS_SECTIONS, extra]} initialSection="extra" onClose={vi.fn()} />);

    expect(screen.getByText("Extra content")).toBeInTheDocument();
  });

  it("closes with Escape", async () => {
    const onClose = vi.fn();
    renderWithProviders(<SettingsDialog onClose={onClose} />);

    await userEvent.keyboard("{Escape}");

    expect(onClose).toHaveBeenCalled();
  });
});

describe("Settings: Allgemein", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("shows type, location and schema version of the database, read-only, with the hint where to change it", async () => {
    stubStorage();
    renderWithProviders(<SettingsDialog onClose={vi.fn()} />);

    expect(await screen.findByText("sqlite")).toBeInTheDocument();
    expect(screen.getByText("/data/configs/todo.db")).toBeInTheDocument();
    expect(screen.getByText("4")).toBeInTheDocument();
    expect(screen.getByText(/configs\/config\.json/)).toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();  // nothing to edit here
  });

  it("says so when the database cannot be described", async () => {
    stubStorage(() => jsonResponse({ code: "write_failed", message: "no access", details: {} }, 500));
    renderWithProviders(<SettingsDialog onClose={vi.fn()} />);

    expect(await screen.findByText(/Die Datenbank konnte nicht gelesen werden/)).toBeInTheDocument();
  });

  it("sets the backend new projects start with, markdown until it is changed", async () => {
    stubStorage();
    renderWithProviders(<SettingsDialog onClose={vi.fn()} />);

    expect(screen.getByRole("radio", { name: "Markdown-Ordner" })).toBeChecked();
    await userEvent.click(screen.getByRole("radio", { name: "Datenbank" }));

    expect(screen.getByRole("radio", { name: "Datenbank" })).toBeChecked();
    expect(screen.getByRole("radio", { name: "Markdown-Ordner" })).not.toBeChecked();
  });

  it("starts with the stored choice", () => {
    stubStorage();
    renderWithProviders(<SettingsDialog onClose={vi.fn()} />, { defaultBackend: "database" });

    expect(screen.getByRole("radio", { name: "Datenbank" })).toBeChecked();
  });

  it("is in English when the language is", async () => {
    stubStorage();
    renderWithProviders(<SettingsDialog onClose={vi.fn()} />, { lang: "en" });

    expect(screen.getByRole("dialog", { name: "Settings" })).toBeInTheDocument();
    expect(await screen.findByText("sqlite")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByRole("button", { name: "General" })).toBeInTheDocument());
  });
});

describe("Sidebar: the gear", () => {
  it("opens the settings", async () => {
    const onOpenSettings = vi.fn();
    renderWithProviders(
      <Sidebar
        options={{ projects: [], statuses: [], priorities: [] }}
        sources={[]}
        onAddSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onSyncSource={vi.fn()}
        onOpenSettings={onOpenSettings} syncStates={new Map()} onOpenProject={vi.fn()}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: "Einstellungen" }));

    expect(onOpenSettings).toHaveBeenCalledTimes(1);
  });
});
