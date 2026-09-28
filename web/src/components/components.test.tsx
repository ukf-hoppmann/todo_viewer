import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toItems } from "../domain/model";
import { apiItem, renderWithProviders } from "../test/render";
import { TreeView } from "../views/TreeView";
import { DetailPanel } from "./DetailPanel";
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

describe("DetailPanel editing", () => {
  afterEach(() => vi.unstubAllGlobals());

  it("asks for a resolution before completing and sends it with the item ref", async () => {
    const fetchMock = vi.fn(async (request: Request) => {
      const body = await request.clone().json();
      return new Response(JSON.stringify({ ...apiItem("TASK-2"), status: body.value }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    const item = items[2]!;
    renderWithProviders(
      <DetailPanel item={item} items={items} byUid={new Map(items.map((i) => [i.uid, i]))} sourcePath="/x" onSelect={vi.fn()} onClose={vi.fn()} />,
    );

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Status" }), "Completed");
    const text = screen.getByRole("textbox", { name: "Entscheidung (Resolution)" });
    expect((text as HTMLTextAreaElement).value).toMatch(/^Confirmed by the project owner on \d{4}-\d{2}-\d{2}\.$/);

    await userEvent.clear(text);
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));
    expect(screen.getByText("Bitte eine Resolution angeben.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();

    await userEvent.type(text, "Done");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    const request = fetchMock.mock.calls[0]![0];
    expect(request.method).toBe("PATCH");
    expect(new URL(request.url).pathname).toBe(`/api/v2/items/s/${item.id}`);
    expect(await request.clone().json()).toEqual({ version: item.version, field: "status", value: "Completed", resolution: "Done" });
  });

  it("edits required-for-parent as Yes/No", async () => {
    const fetchMock = vi.fn(async (request: Request) => {
      const body = await request.clone().json();
      return new Response(JSON.stringify({ ...apiItem("TASK-2"), required_for_parent: body.value === "Yes" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    });
    vi.stubGlobal("fetch", fetchMock);
    const item = items[2]!;
    renderWithProviders(
      <DetailPanel item={item} items={items} byUid={new Map(items.map((i) => [i.uid, i]))} sourcePath="/x" onSelect={vi.fn()} onClose={vi.fn()} />,
    );

    const select = screen.getByRole("combobox", { name: "Pflicht für Parent" });
    expect((select as HTMLSelectElement).value).toBe("No");
    await userEvent.selectOptions(select, "Ja");

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
    expect(await fetchMock.mock.calls[0]![0].clone().json()).toEqual({
      version: item.version,
      field: "required_for_parent",
      value: "Yes",
      resolution: null,
    });
  });

  it("offers required-for-parent only for items with a parent", () => {
    const item = items[0]!;
    renderWithProviders(
      <DetailPanel item={item} items={items} byUid={new Map(items.map((i) => [i.uid, i]))} sourcePath="/x" onSelect={vi.fn()} onClose={vi.fn()} />,
    );
    expect(screen.queryByRole("combobox", { name: "Pflicht für Parent" })).not.toBeInTheDocument();
  });

  it("shows translated API errors", async () => {
    vi.stubGlobal("fetch", vi.fn(async () =>
      new Response(JSON.stringify({ code: "version_conflict", message: "x", details: {} }), {
        status: 409,
        headers: { "Content-Type": "application/json" },
      })));
    const item = items[0]!;
    renderWithProviders(
      <DetailPanel item={item} items={items} byUid={new Map(items.map((i) => [i.uid, i]))} sourcePath="/x" onSelect={vi.fn()} onClose={vi.fn()} />,
    );

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Priorität" }), "Urgent");

    expect(await screen.findByText(/Der Eintrag wurde inzwischen geändert/)).toBeInTheDocument();
  });
});
