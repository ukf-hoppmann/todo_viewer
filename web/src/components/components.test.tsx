import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toItems } from "../domain/model";
import { apiItem, renderWithProviders } from "../test/render";
import { TreeView } from "../views/TreeView";
import { DetailPanel } from "./DetailPanel";
import { DocumentDialog } from "./DocumentDialog";
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

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

function renderPanel(item: (typeof items)[number]) {
  renderWithProviders(
    <DetailPanel item={item} items={items} byUid={new Map(items.map((i) => [i.uid, i]))} sourcePath="/x" onSelect={vi.fn()} onClose={vi.fn()} />,
  );
}

describe("DetailPanel edit mode", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("changes nothing outside the edit mode", () => {
    renderPanel(items[2]!);

    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "✎ Bearbeiten" })).toBeInTheDocument();
  });

  it("shows an unset priority as empty instead of the first option", async () => {
    renderPanel(items[2]!);

    await userEvent.click(screen.getByRole("button", { name: "✎ Bearbeiten" }));

    expect((screen.getByRole("combobox", { name: "Priorität" }) as HTMLSelectElement).value).toBe("");
  });

  it("saves all changed fields in one request and leaves the edit mode", async () => {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async () => jsonResponse(apiItem("TASK-2")));
    vi.stubGlobal("fetch", fetchMock);
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
    vi.stubGlobal("fetch", fetchMock);
    renderPanel(items[2]!);

    await userEvent.click(screen.getByRole("button", { name: "✎ Bearbeiten" }));
    await userEvent.type(screen.getByRole("textbox", { name: "Titel" }), " changed");
    await userEvent.click(screen.getByRole("button", { name: "Abbrechen" }));

    expect(fetchMock).not.toHaveBeenCalled();
    expect(screen.queryByRole("textbox", { name: "Titel" })).not.toBeInTheDocument();
  });

  it("asks for a resolution when completing", async () => {
    const fetchMock = vi.fn<(request: Request) => Promise<Response>>(async () => jsonResponse(apiItem("TASK-2")));
    vi.stubGlobal("fetch", fetchMock);
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
    vi.stubGlobal("fetch", fetchMock);
    const standalone = toItems([apiItem("TASK-9")])[0]!;
    renderWithProviders(
      <DetailPanel item={standalone} items={[...items, standalone]} byUid={new Map()} sourcePath="/x" onSelect={vi.fn()} onClose={vi.fn()} />,
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
    vi.stubGlobal("fetch", fetchMock);
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
    vi.stubGlobal("fetch", vi.fn(async () =>
      jsonResponse({ code: "children_still_active", message: "x", details: { id: "EPIC-1", items: "STORY-1, TASK-1" } }, 409)));
    renderPanel(items[0]!);

    await userEvent.click(screen.getByRole("button", { name: "✎ Bearbeiten" }));
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Priorität" }), "Urgent");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    expect(await screen.findByText(/EPIC-1 kann nicht geschlossen werden, solange Kinder aktiv sind: STORY-1, TASK-1\./)).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Titel" })).toBeInTheDocument();
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
