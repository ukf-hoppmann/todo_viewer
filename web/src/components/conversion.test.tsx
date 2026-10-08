import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toItems } from "../domain/model";
import { errorResponse, indexTopic, linkOut, noteOut, stubRoutes, type Route } from "../test/api";
import { apiItem, renderWithProviders } from "../test/render";
import { DemoteItemDialog } from "./DemoteItemDialog";
import { DetailPanel } from "./DetailPanel";
import { ItemOrigin, NoteOrigin } from "./OriginLink";
import { PromoteNoteDialog } from "./PromoteNoteDialog";

const NOTE = { project: "P", label: "NOTE-001", version: "v-note", summary: "Check the sync", body: "Look at both directions." };
const ITEMS = toItems([apiItem("EPIC-001", { type: "Epic", title: "The epic" }), apiItem("STORY-001", { type: "Story", parent: "EPIC-001" })]);
const PROMOTE = "/api/v2/notes/P/NOTE-001/promote";
const created = apiItem("STORY-009", { type: "Story", title: "Check the sync" });

afterEach(() => vi.unstubAllGlobals());

describe("PromoteNoteDialog", () => {
  it("starts from the note, sends the fields, and offers the new item", async () => {
    const calls = stubRoutes([{ method: "POST", path: PROMOTE, respond: () => ({ note: noteOut("NOTE-001", { status: "promoted" }), item: created }) }]);
    renderWithProviders(<PromoteNoteDialog note={NOTE} items={ITEMS} onClose={vi.fn()} />);

    expect(screen.getByRole("textbox", { name: "Titel" })).toHaveValue("Check the sync");
    expect(screen.getByRole("textbox", { name: "Ziel" })).toHaveValue("Look at both directions.");
    await userEvent.type(screen.getByRole("textbox", { name: "Bereich" }), "Core");
    await userEvent.type(screen.getByRole("textbox", { name: "Fertigstellungskriterien" }), "It works.");
    await userEvent.click(screen.getByRole("button", { name: "Befördern" }));

    expect(await screen.findByText("Befördert zu STORY-009.")).toBeInTheDocument();
    expect(await calls[0]!.body()).toEqual({
      version: "v-note",
      item_type: "Story",
      area: "Core",
      goal: "Look at both directions.",
      completion_criteria: "It works.",
      priority: "Normal",
      title: "Check the sync",
      summary: "Check the sync",
    });
    expect(screen.getByRole("button", { name: "Item öffnen" })).toBeInTheDocument();
  });

  it("sends the chosen parent together with whether it is required", async () => {
    const calls = stubRoutes([{ method: "POST", path: PROMOTE, respond: () => ({ note: noteOut("NOTE-001"), item: created }) }]);
    renderWithProviders(<PromoteNoteDialog note={NOTE} items={ITEMS} onClose={vi.fn()} />);

    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Parent (optional)" }), "EPIC-001");
    await userEvent.selectOptions(screen.getByRole("combobox", { name: "Pflicht für Parent" }), "No");
    await userEvent.click(screen.getByRole("button", { name: "Befördern" }));

    await waitFor(() => expect(calls).toHaveLength(1));
    expect(await calls[0]!.body()).toMatchObject({ parent: "EPIC-001", required_for_parent: "No" });
  });

  it("shows a refusal of the server as a text and keeps the form", async () => {
    stubRoutes([{ method: "POST", path: PROMOTE, respond: () => errorResponse(409, "parent_closed", { id: "STORY-009", items: "EPIC-001" }) }]);
    renderWithProviders(<PromoteNoteDialog note={NOTE} items={ITEMS} onClose={vi.fn()} />);

    await userEvent.click(screen.getByRole("button", { name: "Befördern" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("abgeschlossenen Parent");
    expect(screen.getByRole("textbox", { name: "Titel" })).toBeInTheDocument();
  });
});

describe("DemoteItemDialog", () => {
  const open = apiItem("TASK-4", { title: "Maybe later" });
  const route = (respond: Route["respond"]): Route[] => [
    { method: "GET", path: "/api/v2/notes/index", respond: () => ({ topics: [indexTopic("TOPIC-001", { name: "Ideas", path: ["Ideas"] })], notes: [] }) },
    { method: "POST", path: "/api/v2/items/s/TASK-4/demote", respond },
  ];

  it("explains what happens, sends the version and an optional topic, and offers the note", async () => {
    const calls = stubRoutes(route(() => ({ item: apiItem("TASK-4", { status: "Rejected" }), note: noteOut("NOTE-007") })));
    const onDemoted = vi.fn();
    renderWithProviders(<DemoteItemDialog item={toItems([open])[0]!} onDemoted={onDemoted} onClose={vi.fn()} />);

    expect(screen.getByText(/wird abgelehnt und archiviert/)).toBeInTheDocument();
    await userEvent.selectOptions(await screen.findByRole("combobox", { name: "Topic der Note (optional)" }), "TOPIC-001");
    await userEvent.click(screen.getByRole("button", { name: "Zurückstufen" }));

    expect(await screen.findByText("Note NOTE-007 angelegt.")).toBeInTheDocument();
    expect(await calls.find((c) => c.method === "POST")!.body()).toEqual({ version: "v-TASK-4", topic: "TOPIC-001" });
    expect(onDemoted).toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Note öffnen" })).toBeInTheDocument();
  });

  it("shows each refusal as a localized text", async () => {
    stubRoutes(route(() => errorResponse(409, "demote_has_children", { id: "TASK-4", items: "TASK-5" })));
    renderWithProviders(<DemoteItemDialog item={toItems([open])[0]!} onDemoted={vi.fn()} onClose={vi.fn()} />);

    await userEvent.click(screen.getByRole("button", { name: "Zurückstufen" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("TASK-4 hat Kinder und lässt sich nicht zur Note zurückstufen: TASK-5.");
  });
});

describe("demoting from the detail panel", () => {
  const SOURCES = [{ id: "s", project: "P", path: "/p", backend: "markdown" as const, sync_path: null, primary: "markdown" as const, markdown_path: "/p", mirror: "none" as const, item_count: 1, problem: null }];
  const panel = (status: string) => {
    const items = toItems([apiItem("TASK-4", { status })]);
    stubRoutes([
      { method: "GET", path: "/api/v2/trash", respond: () => [] },
      { method: "GET", path: "/api/v2/projects/P/items/TASK-4/notes", respond: () => [] },
    ]);
    renderWithProviders(<DetailPanel item={items[0]!} items={items} byUid={new Map(items.map((i) => [i.uid, i]))} sourcePath="/p" sources={SOURCES} onSelect={vi.fn()} onRetyped={vi.fn()} onClose={vi.fn()} />);
  };

  it("offers it for an open item", () => {
    panel("Open");

    expect(screen.getByRole("button", { name: "Zur Note zurückstufen" })).toBeInTheDocument();
  });

  it("does not offer it once work has started", () => {
    panel("In progress");

    expect(screen.queryByRole("button", { name: "Zur Note zurückstufen" })).not.toBeInTheDocument();
  });
});

describe("origin links", () => {
  it("shows at an item the note it was promoted from", async () => {
    stubRoutes([{ method: "GET", path: "/api/v2/projects/P/items/STORY-009/notes", respond: () => [{ project: "P", label: "NOTE-001", summary: "x", status: "promoted", role: "origin", link_id: 1 }] }]);
    renderWithProviders(<ItemOrigin item={toItems([created])[0]!} />);

    expect(await screen.findByRole("button", { name: "Aus Note P · NOTE-001" })).toBeInTheDocument();
  });

  it("shows nothing at an item without an origin", async () => {
    const calls = stubRoutes([{ method: "GET", path: "/api/v2/projects/P/items/STORY-009/notes", respond: () => [{ project: "P", label: "NOTE-002", summary: "x", status: "waiting", role: "reference", link_id: 2 }] }]);
    renderWithProviders(<ItemOrigin item={toItems([created])[0]!} />);

    await waitFor(() => expect(calls).toHaveLength(1));
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows at a note the item it came from, or became", async () => {
    stubRoutes([{ method: "GET", path: "/api/v2/projects/P/notes/NOTE-001/links", respond: () => [linkOut(1, { role: "origin", target: "STORY-9", target_display: "P · STORY-9" })] }]);
    const { unmount } = renderWithProviders(<NoteOrigin project="P" label="NOTE-001" promoted={false} />);
    expect(await screen.findByRole("button", { name: "Herkunft: Item P · STORY-9" })).toBeInTheDocument();
    unmount();

    renderWithProviders(<NoteOrigin project="P" label="NOTE-001" promoted />);
    expect(await screen.findByRole("button", { name: "Wurde zu Item P · STORY-9" })).toBeInTheDocument();
  });
});
