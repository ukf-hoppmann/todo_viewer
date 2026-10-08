import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toItems } from "../domain/model";
import { apiItem, renderWithProviders } from "../test/render";
import { TreeView } from "../views/TreeView";
import { DetailPanel } from "./DetailPanel";
import { TrashView } from "../views/TrashView";
import { CreateItemDialog } from "./CreateItemDialog";
import { DeleteDialog } from "./DeleteDialog";
import { DocumentDialog } from "./DocumentDialog";
import { RetypeDialog } from "./RetypeDialog";
import { RetypeNotice } from "./RetypeNotice";
import { Sidebar } from "./Sidebar";

const items = toItems([
  apiItem("EPIC-1", { type: "Epic" }),
  apiItem("TASK-1", { parent: "EPIC-1", status: "Completed" }),
  apiItem("TASK-2", { parent: "EPIC-1", required_for_parent: false }),
]);

describe("TreeView", () => {
  it("shows progress and collapses children", async () => {
    const onSelect = vi.fn();
    renderWithProviders(<TreeView visible={items} items={items} onSelect={onSelect} />);

    expect(screen.getByText("P (1/2)")).toBeInTheDocument();
    expect(screen.getByText("EPIC-1 — Title EPIC-1").closest(".node-row")?.querySelector(".node-progress")).toHaveTextContent("1/1");
    expect(screen.getByText("TASK-2 — Title TASK-2").closest(".tree-node")).toHaveClass("optional");

    await userEvent.click(screen.getByRole("button", { name: "collapse" }));
    expect(screen.queryByText("TASK-1 — Title TASK-1")).not.toBeInTheDocument();

    await userEvent.click(screen.getByText("EPIC-1 — Title EPIC-1"));
    expect(onSelect).toHaveBeenCalledWith("P::EPIC-1");
  });
});

describe("TreeView collapse buttons", () => {
  const nested = toItems([
    apiItem("EPIC-1", { type: "Epic" }),
    apiItem("STORY-1", { type: "Story", parent: "EPIC-1" }),
    apiItem("TASK-1", { parent: "STORY-1" }),
    apiItem("EPIC-1", { type: "Epic", project: "Q", key: "t/EPIC-1", source_id: "t" }),
    apiItem("TASK-9", { project: "Q", key: "t/TASK-9", source_id: "t", parent: "EPIC-1" }),
  ]);

  it("collapses and expands all epics and stories", async () => {
    renderWithProviders(<TreeView visible={nested} items={nested} onSelect={vi.fn()} />);

    await userEvent.click(screen.getByRole("button", { name: "Stories zuklappen" }));
    expect(screen.queryByText("TASK-1 — Title TASK-1")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Stories aufklappen" })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Epics zuklappen" }));
    expect(screen.queryByText("STORY-1 — Title STORY-1")).not.toBeInTheDocument();
    expect(screen.queryByText("TASK-9 — Title TASK-9")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Epics aufklappen" }));
    expect(screen.getByText("STORY-1 — Title STORY-1")).toBeInTheDocument();
    expect(screen.queryByText("TASK-1 — Title TASK-1")).not.toBeInTheDocument();
  });

  it("acts only on marked projects", async () => {
    renderWithProviders(<TreeView visible={nested} items={nested} onSelect={vi.fn()} />, { markedProjects: new Set(["Q"]) });

    await userEvent.click(screen.getByRole("button", { name: "Epics zuklappen" }));
    expect(screen.queryByText("TASK-9 — Title TASK-9")).not.toBeInTheDocument();
    expect(screen.getByText("STORY-1 — Title STORY-1")).toBeInTheDocument();
  });
});

describe("Sidebar project marking", () => {
  it("marks a project by clicking its name without hiding it", async () => {
    renderWithProviders(
      <Sidebar
        options={{ projects: ["P"], statuses: [], priorities: [] }}
        sources={[]}
        onAddSource={vi.fn()}
        onEditSource={vi.fn()}
        onRemoveSource={vi.fn()}
        onSyncSource={vi.fn()}
        onOpenSettings={vi.fn()} syncStates={new Map()} onOpenProject={vi.fn()}
      />,
    );
    const name = screen.getByRole("button", { name: "P" });
    await userEvent.click(name);
    expect(name).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("checkbox", { name: "P" })).toBeChecked();
    await userEvent.click(name);
    expect(name).toHaveAttribute("aria-pressed", "false");
  });
});

const SOURCES = [
  { id: "s", project: "P", path: "/p", backend: "markdown" as const, sync_path: null, primary: "markdown" as const, markdown_path: "/p", mirror: "none" as const, item_count: 3, problem: null },
  { id: "t", project: "Q", path: "/q", backend: "markdown" as const, sync_path: null, primary: "markdown" as const, markdown_path: "/q", mirror: "none" as const, item_count: 0, problem: null },
];

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

/** Answers the requests of the detail panel itself (the trash, the notes pointing at the item); every other request
 *  goes to `handler`. */
function stubApi(handler: (request: Request) => Promise<Response>, trash: unknown[] = []) {
  vi.stubGlobal("fetch", async (request: Request) => {
    const path = new URL(request.url).pathname;
    if (path === "/api/v2/trash") return jsonResponse(trash);
    if (/^\/api\/v2\/projects\/[^/]+\/items\/[^/]+\/notes$/.test(path)) return jsonResponse([]);
    return handler(request);
  });
}

function renderPanel(item: (typeof items)[number]) {
  renderWithProviders(
    <DetailPanel item={item} items={items} byUid={new Map(items.map((i) => [i.uid, i]))} sourcePath="/x" sources={SOURCES} onSelect={vi.fn()} onRetyped={vi.fn()} onClose={vi.fn()} />,
  );
}

describe("DetailPanel edit mode", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("keeps title and texts to the edit mode", () => {
    renderPanel(items[2]!);

    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "Parent" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "✎ Bearbeiten" })).toBeInTheDocument();
  });

  it("shows an unset priority as empty instead of the first option", async () => {
    renderPanel(items[2]!);

    await userEvent.click(screen.getByRole("button", { name: "✎ Bearbeiten" }));

    expect((screen.getByRole("combobox", { name: "Priorität" }) as HTMLSelectElement).value).toBe("");
  });

  it("saves all changed fields in one request and leaves the edit mode", async () => {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async () => jsonResponse(apiItem("TASK-2")));
    stubApi(fetchMock);
    const item = items[2]!;
    renderPanel(item);

    await userEvent.click(screen.getByRole("button", { name: "✎ Bearbeiten" }));
    const save = screen.getByRole("button", { name: "Speichern" });
    expect(save).toBeDisabled();
    await userEvent.clear(screen.getByRole("textbox", { name: "Titel" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Titel" }), "Renamed");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Priorität" }), "Urgent");
    await userEvent.type(screen.getByRole("textbox", { name: "Ziel" }), "A goal");
    await userEvent.click(save);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const request = fetchMock.mock.calls[0]![0] as Request;
    expect(request.method).toBe("PATCH");
    expect(new URL(request.url).pathname).toBe(`/api/v2/items/s/${item.id}`);
    expect(await request.clone().json()).toEqual({
      version: item.version,
      fields: { title: "Renamed", priority: "Urgent", goal: "A goal" },
      resolution: null,
    });
    await waitFor(() => expect(screen.queryByRole("form")).not.toBeInTheDocument());
  });

  it("discards the changes on cancel", async () => {
    const fetchMock = vi.fn();
    stubApi(fetchMock);
    renderPanel(items[2]!);

    await userEvent.click(screen.getByRole("button", { name: "✎ Bearbeiten" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Titel" }), " changed");
    await userEvent.click(screen.getByRole("button", { name: "Abbrechen" }));

    expect(fetchMock).not.toHaveBeenCalled();
    expect(screen.queryByRole("textbox", { name: "Titel" })).not.toBeInTheDocument();
  });

  it("asks for a resolution when completing", async () => {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async () => jsonResponse(apiItem("TASK-2")));
    stubApi(fetchMock);
    const item = items[2]!;
    renderPanel(item);

    await userEvent.click(screen.getByRole("button", { name: "✎ Bearbeiten" }));
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Status" }), "Completed");
    const text = screen.getByRole("textbox", { name: "Entscheidung (Resolution)" });
    expect((text as HTMLTextAreaElement).value).toMatch(/^Confirmed by the project owner on \d{4}-\d{2}-\d{2}\.$/);
    await userEvent.clear(text);
    await userEvent.type(text, "Done");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(await (fetchMock.mock.calls[0]![0] as Request).clone().json()).toEqual({
      version: item.version,
      fields: { status: "Completed" },
      resolution: "Done",
    });
  });

  it("sends required-for-parent together with a new parent", async () => {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async () => jsonResponse(apiItem("TASK-2")));
    stubApi(fetchMock);
    const standalone = toItems([apiItem("TASK-9")])[0]!;
    renderWithProviders(
      <DetailPanel item={standalone} items={[...items, standalone]} byUid={new Map()} sourcePath="/x" sources={SOURCES} onSelect={vi.fn()} onRetyped={vi.fn()} onClose={vi.fn()} />,
    );

    await userEvent.click(screen.getByRole("button", { name: "✎ Bearbeiten" }));
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Parent" }), "EPIC-1");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Pflicht für Parent" }), "No");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect((await (fetchMock.mock.calls[0]![0] as Request).clone().json()).fields).toEqual({
      parent: "EPIC-1",
      required_for_parent: "No",
    });
  });

  it("keeps the inputs on a version conflict and saves again on the current state", async () => {
    const item = items[2]!;
    const current = { ...apiItem("TASK-2", { parent: "EPIC-1", required_for_parent: false }), version: "v-new", goal: "Their goal" };
    const fetchMock = vi.fn(async (request: Request) => {
      if (request.method === "GET") return jsonResponse(current);
      const body = await request.clone().json();
      return body.version === "v-new"
        ? jsonResponse(current)
        : jsonResponse({ code: "version_conflict", message: "x", details: { id: "TASK-2" } }, 409);
    });
    stubApi(fetchMock);
    renderPanel(item);

    await userEvent.click(screen.getByRole("button", { name: "✎ Bearbeiten" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Titel" }), " mine");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));
    await userEvent.click(await screen.findByRole("button", { name: "Aktuellen Stand laden" }));

    expect((screen.getByRole("textbox", { name: "Titel" }) as HTMLInputElement).value).toBe("Title TASK-2 mine");
    expect((screen.getByRole("textbox", { name: "Ziel" }) as HTMLTextAreaElement).value).toBe("Their goal");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(await (fetchMock.mock.calls[2]![0] as Request).clone().json()).toEqual({
      version: "v-new",
      fields: { title: "Title TASK-2 mine" },
      resolution: null,
    });
  });

  it("shows rule violations with the blocking items", async () => {
    stubApi(vi.fn(async () =>
      jsonResponse({ code: "children_still_active", message: "x", details: { id: "EPIC-1", items: "STORY-1, TASK-1" } }, 409)));
    renderPanel(items[0]!);

    await userEvent.click(screen.getByRole("button", { name: "✎ Bearbeiten" }));
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Priorität" }), "Urgent");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    expect(await screen.findByText(/EPIC-1 kann nicht geschlossen werden, solange Kinder aktiv sind: STORY-1, TASK-1\./)).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Titel" })).toBeInTheDocument();
  });
});

describe("DetailPanel children", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("marks children by status and lists deleted ones from the trash", async () => {
    stubApi(vi.fn(), [apiItem("TASK-9", { parent: "EPIC-1", deleted: "2026-09-20" })]);
    renderPanel(items[0]!);

    const done = screen.getByRole("button", { name: "TASK-1" });
    expect(done).toHaveAttribute("title", "Title TASK-1 — Abgeschlossen");
    expect(done.style.borderColor).toBe("var(--status-done)");
    expect(screen.getByRole("button", { name: "TASK-2 (optional)" })).toHaveAttribute("title", "Title TASK-2 — Offen");
    const deleted = await screen.findByText("TASK-9");
    expect(deleted).toHaveClass("deleted");
    expect(deleted).toHaveAttribute("title", "Title TASK-9 — gelöscht am 2026-09-20");
  });
});

describe("DetailPanel direct changes", () => {
  afterEach(() => vi.unstubAllGlobals());

  const quickItems = toItems([
    apiItem("EPIC-1", { type: "Epic", area: "Web" }),
    apiItem("TASK-1", { parent: "EPIC-1", required_for_parent: true, area: "Backend", dependencies: ["TASK-2"] }),
    apiItem("TASK-2", { parent: "EPIC-1", required_for_parent: false, area: "Web" }),
  ]);
  const task = quickItems[1]!;

  function renderQuick() {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async () => jsonResponse(apiItem("TASK-1")));
    stubApi(fetchMock);
    renderWithProviders(
      <DetailPanel item={task} items={quickItems} byUid={new Map(quickItems.map((i) => [i.uid, i]))} sourcePath="/x" sources={SOURCES} onSelect={vi.fn()} onRetyped={vi.fn()} onClose={vi.fn()} />,
    );
    const sent = async () => {
      await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
      const request = fetchMock.mock.calls[0]![0] as Request;
      expect(request.method).toBe("PATCH");
      return request.clone().json();
    };
    return { fetchMock, sent };
  }

  it("saves a status change at once, with only that field", async () => {
    const { sent } = renderQuick();

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Status" }), "In progress");

    expect(await sent()).toEqual({ version: task.version, fields: { status: "In progress" }, resolution: null });
  });

  it("asks for a resolution before completing and sends nothing on cancel", async () => {
    const { fetchMock, sent } = renderQuick();

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Status" }), "Completed");
    await userEvent.click(screen.getByRole("button", { name: "Abbrechen" }));
    expect(fetchMock).not.toHaveBeenCalled();
    expect((screen.getByRole("combobox", { name: "Status" }) as HTMLSelectElement).value).toBe("Open");

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Status" }), "Completed");
    const text = screen.getByRole("textbox", { name: "Entscheidung (Resolution)" });
    expect((text as HTMLTextAreaElement).value).toMatch(/^Confirmed by the project owner on \d{4}-\d{2}-\d{2}\.$/);
    await userEvent.clear(text);
    await userEvent.type(text, "Done");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    expect(await sent()).toEqual({ version: task.version, fields: { status: "Completed" }, resolution: "Done" });
  });

  it("saves priority and required-for-parent at once", async () => {
    const { fetchMock } = renderQuick();

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Priorität" }), "Urgent");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByRole("combobox", { name: "Pflicht für Parent" })).toBeEnabled());
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Pflicht für Parent" }), "No");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));

    expect((await (fetchMock.mock.calls[0]![0] as Request).clone().json()).fields).toEqual({ priority: "Urgent" });
    expect((await (fetchMock.mock.calls[1]![0] as Request).clone().json()).fields).toEqual({ required_for_parent: "No" });
  });

  it("shows a conflict next to the field", async () => {
    stubApi(vi.fn(async () => jsonResponse({ code: "version_conflict", message: "x", details: { id: "TASK-1" } }, 409)));
    renderWithProviders(
      <DetailPanel item={task} items={quickItems} byUid={new Map()} sourcePath="/x" sources={SOURCES} onSelect={vi.fn()} onRetyped={vi.fn()} onClose={vi.fn()} />,
    );

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Priorität" }), "Urgent");

    expect(await screen.findByRole("alert")).toHaveTextContent(/inzwischen geändert/);
  });

  it("removes and adds dependencies at once", async () => {
    const { fetchMock } = renderQuick();

    await userEvent.click(screen.getByRole("button", { name: "Abhängigkeit TASK-2 entfernen" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(screen.getByRole("combobox", { name: "＋ Abhängigkeit hinzufügen" })).toBeEnabled());
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "＋ Abhängigkeit hinzufügen" }), "EPIC-1");
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));

    expect((await (fetchMock.mock.calls[0]![0] as Request).clone().json()).fields).toEqual({ dependencies: [] });
    expect((await (fetchMock.mock.calls[1]![0] as Request).clone().json()).fields).toEqual({ dependencies: ["TASK-2", "EPIC-1"] });
  });

  it("offers the backlog's areas and saves a chosen one", async () => {
    const { sent } = renderQuick();
    const area = screen.getByRole("combobox", { name: "Bereich" });

    expect(within(area).getAllByRole("option").map((o) => o.textContent)).toEqual(["Backend", "Web", "＋ Neuer Bereich…"]);
    await userEvent.selectOptions(area, "Web");

    expect((await sent()).fields).toEqual({ area: "Web" });
  });

  it("saves a new area on Enter and cancels it on Escape", async () => {
    const { fetchMock, sent } = renderQuick();
    const newArea = () => screen.getByRole("textbox", { name: /Neuer Bereich/ });

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Bereich" }), "＋ Neuer Bereich…");
    await userEvent.type(newArea(), "Docs{Escape}");
    expect(fetchMock).not.toHaveBeenCalled();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Bereich" }), "＋ Neuer Bereich…");
    await userEvent.type(newArea(), " Docs {Enter}");

    expect((await sent()).fields).toEqual({ area: "Docs" });
  });
});

describe("DocumentDialog", () => {
  it("loads documents by item and name and switches between them", async () => {
    const fetchMock = vi.fn(async (request: Request) => {
      const name = decodeURIComponent(new URL(request.url).pathname.split("/").pop()!);
      return new Response(JSON.stringify({ name, kind: "spec", content: `# Content of ${name}`, version: "v" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    const [item] = toItems([
      apiItem("TASK-7", { documents: [{ name: "TASK-7_notes.md", kind: "notes" }, { name: "TASK-7_spec.md", kind: "spec" }] }),
    ]);
    renderWithProviders(<DocumentDialog item={item!} initialName="TASK-7_notes.md" onClose={vi.fn()} />);

    expect(await screen.findByText("Content of TASK-7_notes.md")).toBeInTheDocument();
    expect(new URL(fetchMock.mock.calls[0]![0].url).pathname).toBe("/api/v2/items/s/TASK-7/documents/TASK-7_notes.md");

    await userEvent.click(screen.getByRole("tab", { name: "Spec" }));
    expect(await screen.findByText("Content of TASK-7_spec.md")).toBeInTheDocument();
  });
});

describe("CreateItemDialog", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("creates a new item without parent and selects it", async () => {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async () =>
      jsonResponse(apiItem("STORY-7", { project: "Q", source_id: "t" }), 201));
    vi.stubGlobal("fetch", fetchMock);
    const onCreated = vi.fn();
    renderWithProviders(<CreateItemDialog sources={SOURCES} sourceId="s" parent={null} onClose={vi.fn()} onCreated={onCreated} />);

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Projekt" }), "t");
    await userEvent.type(screen.getByRole("textbox", { name: "Titel" }), "New story");
    await userEvent.type(screen.getByRole("textbox", { name: "Bereich" }), "Core");
    await userEvent.type(screen.getByRole("textbox", { name: "Ziel" }), "Goal");
    await userEvent.type(screen.getByRole("textbox", { name: "Fertigstellungskriterien" }), "Done");
    await userEvent.click(screen.getByRole("button", { name: "Anlegen" }));

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith("Q::STORY-7"));
    const request = fetchMock.mock.calls[0]![0];
    expect([request.method, new URL(request.url).pathname]).toEqual(["POST", "/api/v2/items"]);
    expect(await request.clone().json()).toEqual({
      source_id: "t", type: "Story", title: "New story", area: "Core", goal: "Goal", completion_criteria: "Done", priority: "Normal",
    });
  });

  it("prefills a child and offers only fitting types", async () => {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async () =>
      jsonResponse({ code: "value_required", message: "x", details: { field: "title" } }, 400));
    vi.stubGlobal("fetch", fetchMock);
    const epic = items[0]!;
    renderWithProviders(<CreateItemDialog sources={SOURCES} sourceId="s" parent={epic} onClose={vi.fn()} onCreated={vi.fn()} />);

    expect(screen.queryByRole("combobox", { name: "Projekt" })).not.toBeInTheDocument();
    expect([...(screen.getByRole("combobox", { name: "Typ" }) as HTMLSelectElement).options].map((o) => o.value)).toEqual(["Story", "Task"]);
    await userEvent.click(screen.getByRole("button", { name: "Anlegen" }));

    expect(await screen.findByText(/Dieses Feld darf nicht leer sein/)).toBeInTheDocument();
    expect(await fetchMock.mock.calls[0]![0].clone().json()).toMatchObject({ parent: "EPIC-1", required_for_parent: "Yes" });
  });

  it("offers to reopen a closed parent and creates the item afterwards", async () => {
    let posts = 0;
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async (request) => {
      if (request.method === "POST" && posts++ === 0)
        return jsonResponse({ code: "parent_closed", message: "x", details: { id: "STORY-7", items: "EPIC-1" } }, 409);
      if (request.method === "POST") return jsonResponse(apiItem("STORY-7", { parent: "EPIC-1" }), 201);
      return jsonResponse(apiItem("EPIC-1", { type: "Epic", version: "v1" }));
    });
    vi.stubGlobal("fetch", fetchMock);
    const onCreated = vi.fn();
    renderWithProviders(<CreateItemDialog sources={SOURCES} sourceId="s" parent={items[0]!} onClose={vi.fn()} onCreated={onCreated} />);

    await userEvent.click(screen.getByRole("button", { name: "Anlegen" }));
    expect(await screen.findByText(/EPIC-1 ist abgeschlossen. Wieder öffnen/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Wieder öffnen und anlegen" }));

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith("P::STORY-7"));
    const calls = fetchMock.mock.calls.map(([r]) => `${r.method} ${new URL(r.url).pathname}`);
    expect(calls).toEqual(["POST /api/v2/items", "GET /api/v2/items/s/EPIC-1", "PATCH /api/v2/items/s/EPIC-1", "POST /api/v2/items"]);
    expect(await fetchMock.mock.calls[2]![0].clone().json()).toEqual({ version: "v1", fields: { status: "In progress" }, resolution: null });
  });
});

describe("DeleteDialog", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("warns about children and deletes them only after confirmation", async () => {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async (request) =>
      new URL(request.url).searchParams.get("cascade") === "true"
        ? jsonResponse([apiItem("EPIC-1"), apiItem("TASK-1")])
        : jsonResponse({ code: "has_children", message: "x", details: { id: "EPIC-1", items: "TASK-1, TASK-2" } }, 409));
    vi.stubGlobal("fetch", fetchMock);
    const onDeleted = vi.fn();
    renderWithProviders(<DeleteDialog item={items[0]!} onClose={vi.fn()} onDeleted={onDeleted} />);

    await userEvent.click(screen.getByRole("button", { name: "In den Papierkorb" }));
    expect(await screen.findByText(/Kinder, die mitgelöscht würden: TASK-1, TASK-2/)).toBeInTheDocument();
    expect(onDeleted).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "Samt Kindern in den Papierkorb" }));

    await waitFor(() => expect(onDeleted).toHaveBeenCalled());
    const urls = fetchMock.mock.calls.map(([r]) => new URL(r.url));
    expect(urls.map((u) => [u.pathname, u.searchParams.get("cascade"), u.searchParams.get("version")])).toEqual([
      ["/api/v2/items/s/EPIC-1", "false", "v-EPIC-1"],
      ["/api/v2/items/s/EPIC-1", "true", "v-EPIC-1"],
    ]);
  });
});

describe("type change", () => {
  afterEach(() => vi.unstubAllGlobals());

  const notice = {
    code: "external_references_may_remain",
    message: "References outside the backlog are not updated.",
    details: { old_id: "TASK-2", new_id: "STORY-2" },
  };
  const retyped = { item: apiItem("STORY-2", { type: "Story", parent: "EPIC-1" }), old_id: "TASK-2", notices: [notice] };

  it("sends version and the chosen type and reports the result", async () => {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async () => jsonResponse(retyped));
    vi.stubGlobal("fetch", fetchMock);
    const onRetyped = vi.fn();
    renderWithProviders(<RetypeDialog item={items[2]!} onClose={vi.fn()} onRetyped={onRetyped} />);

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Neuer Typ" }), "Story");
    await userEvent.click(screen.getByRole("button", { name: "Typ ändern" }));

    await waitFor(() => expect(onRetyped).toHaveBeenCalledWith(retyped));
    const request = fetchMock.mock.calls[0]![0];
    expect([request.method, new URL(request.url).pathname]).toEqual(["POST", "/api/v2/items/s/TASK-2/retype"]);
    expect(await request.clone().json()).toEqual({ version: "v-TASK-2", type: "Story" });
  });

  it("offers no epic below a parent", () => {
    renderWithProviders(<RetypeDialog item={items[2]!} onClose={vi.fn()} onRetyped={vi.fn()} />);

    const options = within(screen.getByRole("combobox", { name: "Neuer Typ" })).getAllByRole("option");
    expect(options.map((o) => o.textContent)).toEqual(["Story"]);
  });

  it("shows a translated error and changes nothing", async () => {
    vi.stubGlobal("fetch", async () =>
      jsonResponse({ code: "item_folder_exists", message: "x", details: { id: "STORY-2" } }, 409));
    const onRetyped = vi.fn();
    renderWithProviders(<RetypeDialog item={items[2]!} onClose={vi.fn()} onRetyped={onRetyped} />);

    await userEvent.click(screen.getByRole("button", { name: "Typ ändern" }));

    expect(await screen.findByText(/Für STORY-2 gibt es schon einen Dokumentenordner/)).toBeInTheDocument();
    expect(onRetyped).not.toHaveBeenCalled();
  });

  it("tells old and new id and warns about references outside the backlog until closed", async () => {
    const onClose = vi.fn();
    renderWithProviders(<RetypeNotice result={retyped} onClose={onClose} />);

    expect(screen.getByRole("dialog", { name: "TASK-2 heißt jetzt STORY-2" })).toBeInTheDocument();
    expect(screen.getByText(/Verweise auf TASK-2 außerhalb des Backlogs/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Schließen" }));

    expect(onClose).toHaveBeenCalled();
  });

  it("falls back to the server message for an unknown notice", () => {
    const unknown = { ...retyped, notices: [{ code: "something_new", message: "Server says so.", details: {} }] };
    renderWithProviders(<RetypeNotice result={unknown} onClose={vi.fn()} />);

    expect(screen.getByText("Server says so.")).toBeInTheDocument();
  });

  it("opens from the detail panel", async () => {
    stubApi(vi.fn());
    renderPanel(items[2]!);

    await userEvent.click(screen.getByRole("button", { name: "🔁 Typ ändern" }));

    expect(screen.getByRole("dialog", { name: "Typ von TASK-2 ändern" })).toBeInTheDocument();
  });
});

describe("TrashView", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("lists deleted items, restores them and purges only after confirmation", async () => {
    const trashed = apiItem("TASK-5", { deleted: "2026-09-28", archived: true, title: "Old idea" });
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async (request) => {
      const url = new URL(request.url);
      if (url.pathname === "/api/v2/trash") return jsonResponse(url.searchParams.get("source_id") === "s" ? [trashed] : []);
      return jsonResponse([trashed]);
    });
    vi.stubGlobal("fetch", fetchMock);
    renderWithProviders(<TrashView sources={SOURCES} />);

    expect(await screen.findByText("TASK-5 — Old idea")).toBeInTheDocument();
    expect(screen.getByText("gelöscht am 2026-09-28")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Wiederherstellen" }));
    await userEvent.click(screen.getByRole("button", { name: "Endgültig löschen" }));
    expect(screen.getByText(/lässt sich nicht rückgängig machen/)).toBeInTheDocument();
    await userEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Endgültig löschen" }));

    await waitFor(() => expect(fetchMock.mock.calls.some(([r]) => r.method === "DELETE")).toBe(true));
    const writes = fetchMock.mock.calls.map(([r]) => r).filter((r) => r.method !== "GET");
    expect(writes.map((r) => [r.method, new URL(r.url).pathname])).toEqual([
      ["POST", "/api/v2/trash/s/TASK-5/restore"],
      ["DELETE", "/api/v2/trash/s/TASK-5"],
    ]);
    expect(await writes[0]!.clone().json()).toEqual({ version: "v-TASK-5" });
  });

  it("shows a hint when the trash is empty", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse([])));
    renderWithProviders(<TrashView sources={SOURCES} />);

    expect(await screen.findByText("Der Papierkorb ist leer.")).toBeInTheDocument();
  });
});

describe("DocumentDialog writing", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("appends a notes entry and asks for a summary when the item has none", async () => {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async () =>
      jsonResponse({ name: "TASK-7_notes.md", kind: "notes", content: "# TASK-7\n\n## 2026-09-28 — Plan\n", version: "n1" }));
    vi.stubGlobal("fetch", fetchMock);
    const [item] = toItems([apiItem("TASK-7")]);
    renderWithProviders(<DocumentDialog item={item!} initialName={null} initialMode="note" onClose={vi.fn()} />);

    await userEvent.type(screen.getByRole("textbox", { name: "Thema" }), "Plan");
    await userEvent.type(screen.getByRole("textbox", { name: /Entschieden/ }), "Use regex{enter}Keep it small");
    await userEvent.type(screen.getByRole("textbox", { name: "Kurzfassung" }), "Parser work");
    await userEvent.click(screen.getByRole("button", { name: "Eintrag anhängen" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const request = fetchMock.mock.calls[0]![0];
    expect([request.method, new URL(request.url).pathname]).toEqual(["POST", "/api/v2/items/s/TASK-7/notes"]);
    expect(await request.clone().json()).toEqual({
      topic: "Plan", discussed: [], decided: ["Use regex", "Keep it small"], open: [], summary: "Parser work",
    });
  });

  it("creates a spec named after its topic", async () => {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async () =>
      jsonResponse({ name: "TASK-7_spec_data-model.md", kind: "spec", content: "# Model", version: "s1" }));
    vi.stubGlobal("fetch", fetchMock);
    const [item] = toItems([apiItem("TASK-7", { summary: "S" })]);
    renderWithProviders(<DocumentDialog item={item!} initialName={null} initialMode="newSpec" onClose={vi.fn()} />);

    await userEvent.type(screen.getByRole("textbox", { name: /Thema/ }), "Data model");
    await userEvent.type(screen.getByRole("textbox", { name: "Markdown" }), "# Model");
    expect(screen.getByRole("heading", { name: "Model" })).toBeInTheDocument(); // preview
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const request = fetchMock.mock.calls[0]![0];
    expect([request.method, new URL(request.url).pathname]).toEqual(["PUT", "/api/v2/items/s/TASK-7/documents/TASK-7_spec_data-model.md"]);
    expect(await request.clone().json()).toEqual({ content: "# Model", version: null });
  });

  it("keeps the text on a spec conflict and overwrites only after showing the current state", async () => {
    let saved = 0;
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async (request) => {
      if (request.method === "GET") {
        return jsonResponse({ name: "TASK-7_spec.md", kind: "spec", content: saved ? "# Theirs" : "# Mine old", version: saved ? "v2" : "v1" });
      }
      saved += 1;
      const body = await request.clone().json();
      return body.version === "v2"
        ? jsonResponse({ name: "TASK-7_spec.md", kind: "spec", content: body.content, version: "v3" })
        : jsonResponse({ code: "version_conflict", message: "x", details: {} }, 409);
    });
    vi.stubGlobal("fetch", fetchMock);
    const [item] = toItems([apiItem("TASK-7", { documents: [{ name: "TASK-7_spec.md", kind: "spec" }] })]);
    renderWithProviders(<DocumentDialog item={item!} initialName="TASK-7_spec.md" onClose={vi.fn()} />);

    await userEvent.click(await screen.findByRole("button", { name: "✎ Bearbeiten" }));
    const editor = screen.getByRole("textbox", { name: "Markdown" });
    await userEvent.clear(editor);
    await userEvent.type(editor, "# Mine new");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));
    await userEvent.click(await screen.findByRole("button", { name: "Aktuellen Stand anzeigen" }));

    expect(await screen.findByRole("heading", { name: "Theirs" })).toBeInTheDocument();
    expect((screen.getByRole("textbox", { name: "Markdown" }) as HTMLTextAreaElement).value).toBe("# Mine new");
    await userEvent.click(screen.getByRole("button", { name: "Trotzdem speichern" }));
    await waitFor(() => expect(screen.queryByRole("textbox", { name: "Markdown" })).not.toBeInTheDocument());
    const puts = fetchMock.mock.calls.map(([r]) => r).filter((r) => r.method === "PUT");
    expect(await puts[1]!.clone().json()).toEqual({ content: "# Mine new", version: "v2" });
  });

  it("edits a notes document as a whole: get the text, put the new one", async () => {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async (request) =>
      request.method === "GET"
        ? jsonResponse({ name: "TASK-7_notes.md", kind: "notes", content: "# Notes\n\n- old", version: "n1" })
        : jsonResponse({ name: "TASK-7_notes.md", kind: "notes", content: (await request.clone().json()).content, version: "n2" }));
    vi.stubGlobal("fetch", fetchMock);
    const [item] = toItems([apiItem("TASK-7", { summary: "S", documents: [{ name: "TASK-7_notes.md", kind: "notes" }] })]);
    renderWithProviders(<DocumentDialog item={item!} initialName="TASK-7_notes.md" onClose={vi.fn()} />);

    await userEvent.click(await screen.findByRole("button", { name: "✎ Bearbeiten" }));
    const editor = screen.getByRole("textbox", { name: "Markdown" });
    expect((editor as HTMLTextAreaElement).value).toBe("# Notes\n\n- old");
    await userEvent.clear(editor);
    await userEvent.type(editor, "# Notes{enter}{enter}- corrected");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    await waitFor(() => expect(fetchMock.mock.calls.some(([r]) => r.method === "PUT")).toBe(true));
    const put = fetchMock.mock.calls.map(([r]) => r).find((r) => r.method === "PUT")!;
    expect(new URL(put.url).pathname).toBe("/api/v2/items/s/TASK-7/documents/TASK-7_notes.md");
    expect(await put.clone().json()).toEqual({ content: "# Notes\n\n- corrected", version: "n1" });
  });
});
