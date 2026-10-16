import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toItems } from "../domain/model";
import { errorResponse, stubRoutes } from "../test/api";
import { apiItem, renderWithProviders } from "../test/render";
import { useUiState } from "../state/useUiStateStore";
import { ItemNotes } from "./ItemNotes";
import { NotesSettings } from "./settings/NotesSettings";

const ITEM = toItems([apiItem("STORY-001")])[0]!;
const linked = (project: string, label: string, status: string, over: Record<string, unknown> = {}) => ({ project, label, summary: `About ${label}`, status, role: "reference", link_id: 1, ...over });
const ROUTE = "/api/v2/projects/P/items/STORY-001/notes";

afterEach(() => vi.unstubAllGlobals());

describe("ItemNotes", () => {
  it("lists the notes of the item from several projects, open ones first, with their status", async () => {
    stubRoutes([
      { method: "GET", path: ROUTE, respond: () => [linked("P", "NOTE-001", "done"), linked("Q", "NOTE-004", "waiting"), linked("P", "NOTE-002", "due")] },
      { method: "GET", path: "/api/v2/notices", respond: () => [] },
    ]);
    renderWithProviders(<ItemNotes item={ITEM} />);

    expect(await screen.findByText("Q · NOTE-004")).toBeInTheDocument();
    const labels = screen.getAllByRole("button").map((b) => b.textContent);
    expect(labels).toEqual(["Q · NOTE-004", "NOTE-002", "NOTE-001"]);
    expect(screen.getByText("wartet")).toBeInTheDocument();
    expect(screen.getByText("erledigt")).toBeInTheDocument();
  });

  it("jumps into the Notes area to the note", async () => {
    stubRoutes([
      { method: "GET", path: ROUTE, respond: () => [linked("Q", "NOTE-004", "waiting")] },
      { method: "GET", path: "/api/v2/notices", respond: () => [] },
    ]);
    function Probe() {
      const { state } = useUiState();
      return <div data-testid="state">{state.currentView}:{state.selectedNote ? `${state.selectedNote.project}/${state.selectedNote.label}` : ""}</div>;
    }
    renderWithProviders(
      <>
        <ItemNotes item={ITEM} />
        <Probe />
      </>,
    );

    await userEvent.click(await screen.findByRole("button", { name: "Q · NOTE-004" }));

    expect(screen.getByTestId("state")).toHaveTextContent("notes:Q/NOTE-004");
  });

  it("shows nothing when no note points at the item", async () => {
    const calls = stubRoutes([
      { method: "GET", path: ROUTE, respond: () => [] },
      { method: "GET", path: "/api/v2/notices", respond: () => [] },
    ]);
    const { container } = renderWithProviders(<ItemNotes item={ITEM} />);

    await waitFor(() => expect(calls).toHaveLength(2));
    expect(container).toBeEmptyDOMElement();
  });

  it("shows an open notice and takes note of it", async () => {
    const calls = stubRoutes([
      { method: "GET", path: ROUTE, respond: () => [] },
      {
        method: "GET",
        path: "/api/v2/notices",
        respond: () => [{ id: 5, side: "item", project: "P", label: "STORY-001", cause: "note_dropped", counterpart: { kind: "note", project: "P", label: "NOTE-004" }, created_at: "2027-01-01T00:00:00Z", decided_at: null, decision: null, options: ["acknowledge"] }],
      },
      { method: "POST", path: "/api/v2/notices/5/decision", respond: () => ({ notice: {}, note: null, item: null }) },
    ]);
    renderWithProviders(<ItemNotes item={ITEM} />);

    expect(await screen.findByText("Note P · NOTE-004 wurde verworfen.")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Zur Kenntnis nehmen" }));

    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(await calls.find((c) => c.method === "POST")!.body()).toEqual({ decision: "acknowledge" });
  });

  it("asks for the notices of the item by its project name, not by the id of its source", async () => {
    const calls = stubRoutes([
      { method: "GET", path: ROUTE, respond: () => [] },
      { method: "GET", path: "/api/v2/notices", respond: () => [] },
    ]);
    renderWithProviders(<ItemNotes item={ITEM} />);

    await waitFor(() => expect(calls).toHaveLength(2));
    expect(calls.find((c) => c.path === "/api/v2/notices")!.search).toContain("project=P");
    expect(calls.find((c) => c.path === "/api/v2/notices")!.search).toContain("side=item");
  });
});

describe("NotesSettings", () => {
  const settings = { review_days: 30, max_topic_depth: 3 };

  it("shows the stored values and the hint that the depth does not change existing topics", async () => {
    stubRoutes([{ method: "GET", path: "/api/v2/notes/settings", respond: () => ({ review_days: 14, max_topic_depth: 5 }) }]);
    renderWithProviders(<NotesSettings />);

    expect(await screen.findByLabelText("Prüf-Intervall in Tagen")).toHaveValue(14);
    expect(screen.getByLabelText("Maximale Topic-Tiefe")).toHaveValue(5);
    expect(screen.getByText(/Vorhandene Topics ändern sich nicht/)).toBeInTheDocument();
  });

  it("shows the defaults as placeholders", async () => {
    stubRoutes([{ method: "GET", path: "/api/v2/notes/settings", respond: () => settings }]);
    renderWithProviders(<NotesSettings />);

    expect(await screen.findByLabelText("Prüf-Intervall in Tagen")).toHaveAttribute("placeholder", "30");
    expect(screen.getByLabelText("Maximale Topic-Tiefe")).toHaveAttribute("placeholder", "3");
  });

  it("saves both values", async () => {
    const calls = stubRoutes([
      { method: "GET", path: "/api/v2/notes/settings", respond: () => settings },
      { method: "PUT", path: "/api/v2/notes/settings", respond: () => ({ review_days: 7, max_topic_depth: 4 }) },
    ]);
    renderWithProviders(<NotesSettings />);

    const days = await screen.findByLabelText("Prüf-Intervall in Tagen");
    await userEvent.clear(days);
    await userEvent.type(days, "7");
    const depth = screen.getByLabelText("Maximale Topic-Tiefe");
    await userEvent.clear(depth);
    await userEvent.type(depth, "4");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true));
    expect(await calls.find((c) => c.method === "PUT")!.body()).toEqual({ review_days: 7, max_topic_depth: 4 });
    expect(await screen.findByText("Gespeichert.")).toBeInTheDocument();
  });

  it("shows an invalid value refused by the server as a text", async () => {
    stubRoutes([
      { method: "GET", path: "/api/v2/notes/settings", respond: () => settings },
      { method: "PUT", path: "/api/v2/notes/settings", respond: () => errorResponse(400, "invalid_value", { field: "review_days" }) },
    ]);
    renderWithProviders(<NotesSettings />);

    const days = await screen.findByLabelText("Prüf-Intervall in Tagen");
    await userEvent.clear(days);
    await userEvent.type(days, "100");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Ungültiger Wert");
    expect(screen.queryByText("Gespeichert.")).not.toBeInTheDocument();
  });

  it("says when the settings cannot be loaded", async () => {
    stubRoutes([{ method: "GET", path: "/api/v2/notes/settings", respond: () => errorResponse(500, "boom") }]);
    renderWithProviders(<NotesSettings />);

    expect(await screen.findByText(/konnten nicht geladen werden/)).toBeInTheDocument();
  });
});
