import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useUiState } from "../state/useUiStateStore";
import type { Schemas } from "../api/client";
import { toItems } from "../domain/model";
import { errorResponse, noteOut, stubRoutes, type Route } from "../test/api";
import { apiItem, renderWithProviders } from "../test/render";
import { DueModal } from "./DueModal";

type Due = Schemas["DueNoteOut"];

const due = (label: string, over: Partial<Due> = {}): Due => ({
  project: "P",
  label,
  summary: `Summary ${label}`,
  status: "due",
  reason: "trigger",
  review_at: null,
  topic: null,
  topic_path: [],
  archived: false,
  triggers: [],
  actions: ["keep", "snooze", "done", "dropped"],
  ...over,
});

const notice = (id: number, cause: string, over: Partial<Schemas["todo_viewer__api__v2__notes_schemas__NoticeOut"]> = {}) => ({
  id,
  side: "note" as const,
  project: "P",
  label: "NOTE-003",
  cause,
  counterpart: { kind: "item", project: "Q", label: "STORY-001" },
  created_at: "2027-01-01T00:00:00Z",
  decided_at: null,
  decision: null,
  options: ["keep", "detach", "drop", "promote"],
  ...over,
});

const ITEMS = toItems([apiItem("EPIC-001", { type: "Epic" })]);

/** A due list that the actions can change: `remove(label)` takes a note out like the server does after an action. */
function dueRoutes(initial: Due[]) {
  let rows = [...initial];
  const remove = (label: string) => {
    rows = rows.filter((r) => r.label !== label);
  };
  const routes: Route[] = [
    { method: "GET", path: "/api/v2/notes/due", respond: () => rows },
    { method: "GET", path: "/api/v2/notices", respond: () => [notice(11, "item_completed")] },
  ];
  return { routes, remove };
}

const ROWS = [
  due("NOTE-001", { reason: "review_expired" }),
  due("NOTE-002", {
    reason: "trigger",
    triggers: [{ id: 1, kind: "event", at: null, fired_at: "2027-01-01T00:00:00Z", already_met: false, target: "STORY-001", target_project: "Q", target_display: "Q · STORY-001", target_status: "Completed", reachable: true, unreachable_reason: null }],
  }),
  due("NOTE-003", { reason: "notice", actions: ["keep", "detach", "drop", "promote"] }),
  due("NOTE-004", { reason: "topic_due", topic_path: ["Ideas", "Later"] }),
];

function renderModal(onClose = vi.fn()) {
  return renderWithProviders(<DueModal items={ITEMS} projects={["P", "Q"]} onClose={onClose} />);
}

afterEach(() => vi.unstubAllGlobals());

describe("DueModal", () => {
  it("groups the notes by reason in a fixed order, each with its count", async () => {
    stubRoutes(dueRoutes(ROWS).routes);
    renderModal();

    await screen.findByText("Summary NOTE-001");
    const headings = screen.getAllByRole("heading", { level: 4 }).map((h) => h.textContent);
    expect(headings).toEqual(["Auslöser (1)", "Änderungshinweis (1)", "Termin (1)", "Prüfung (1)"]);
    expect(screen.getByText("Ideas › Later")).toBeInTheDocument();
    expect(screen.getByText(/Eingetroffen: Wenn Q · STORY-001 den Status „Completed“ erreicht/)).toBeInTheDocument();
  });

  it("shows what a change notice says and offers its decisions", async () => {
    stubRoutes(dueRoutes(ROWS).routes);
    renderModal();

    const row = (await screen.findByText("Summary NOTE-003")).closest(".due-row") as HTMLElement;
    expect(await within(row).findByText("Q · STORY-001 wurde abgeschlossen.")).toBeInTheDocument();
    expect(within(row).getAllByRole("button").map((b) => b.textContent)).toEqual(["Behalten", "Abkoppeln", "Note verwerfen", "Befördern", "In Notes öffnen"]);
  });

  it("decides a notice with keep and sends the notice's id", async () => {
    const { routes, remove } = dueRoutes(ROWS);
    const calls = stubRoutes([
      ...routes,
      {
        method: "POST",
        path: "/api/v2/notices/11/decision",
        respond: () => {
          remove("NOTE-003");
          return { notice: notice(11, "item_completed"), note: noteOut("NOTE-003"), item: null };
        },
      },
    ]);
    renderModal();

    const row = (await screen.findByText("Summary NOTE-003")).closest(".due-row") as HTMLElement;
    await userEvent.click(await within(row).findByRole("button", { name: "Behalten" }));

    await waitFor(() => expect(screen.queryByText("Summary NOTE-003")).not.toBeInTheDocument());
    expect(await calls.find((c) => c.path === "/api/v2/notices/11/decision")!.body()).toEqual({ decision: "keep" });
  });

  it("closes a note as done on its current version, and the row goes only after the server worked", async () => {
    const { routes, remove } = dueRoutes(ROWS);
    const calls = stubRoutes([
      ...routes,
      { method: "GET", path: "/api/v2/projects/P/notes/NOTE-001", respond: () => noteOut("NOTE-001", { version: "v-current" }) },
      {
        method: "POST",
        path: "/api/v2/projects/P/notes/NOTE-001/finish",
        respond: () => {
          remove("NOTE-001");
          return noteOut("NOTE-001", { archived: true });
        },
      },
    ]);
    renderModal();

    await userEvent.click(within((await screen.findByText("Summary NOTE-001")).closest(".due-row") as HTMLElement).getByRole("button", { name: "Erledigen" }));

    await waitFor(() => expect(screen.queryByText("Summary NOTE-001")).not.toBeInTheDocument());
    expect(await calls.find((c) => c.path.endsWith("/finish"))!.body()).toEqual({ version: "v-current", status: "done" });
    expect(screen.getByText("Summary NOTE-002")).toBeInTheDocument();
  });

  it("keeps the row and shows the error when the action fails", async () => {
    stubRoutes([
      ...dueRoutes(ROWS).routes,
      { method: "GET", path: "/api/v2/projects/P/notes/NOTE-001", respond: () => noteOut("NOTE-001") },
      { method: "POST", path: "/api/v2/projects/P/notes/NOTE-001/finish", respond: () => errorResponse(409, "version_conflict", { id: "NOTE-001" }) },
    ]);
    renderModal();

    const row = (await screen.findByText("Summary NOTE-001")).closest(".due-row") as HTMLElement;
    await userEvent.click(within(row).getByRole("button", { name: "Erledigen" }));

    expect(await within(row).findByRole("alert")).toHaveTextContent("inzwischen geändert");
    expect(screen.getByText("Summary NOTE-001")).toBeInTheDocument();
  });

  it("snoozes a note from the row with the version it just read", async () => {
    const { routes, remove } = dueRoutes(ROWS);
    const calls = stubRoutes([
      ...routes,
      { method: "GET", path: "/api/v2/projects/P/notes/NOTE-001", respond: () => noteOut("NOTE-001", { version: "v-now" }) },
      {
        method: "POST",
        path: "/api/v2/projects/P/notes/NOTE-001/snooze",
        respond: () => {
          remove("NOTE-001");
          return noteOut("NOTE-001");
        },
      },
    ]);
    renderModal();

    await userEvent.click(within((await screen.findByText("Summary NOTE-001")).closest(".due-row") as HTMLElement).getByRole("button", { name: "Zurückstellen" }));
    await userEvent.click(await screen.findByRole("button", { name: "In einer Woche" }));

    await waitFor(() => expect(screen.queryByText("Summary NOTE-001")).not.toBeInTheDocument());
    expect(await calls.find((c) => c.path.endsWith("/snooze"))!.body()).toMatchObject({ version: "v-now" });
  });

  it("promotes the note of a notice through the decision of that notice", async () => {
    const { routes, remove } = dueRoutes(ROWS);
    const calls = stubRoutes([
      ...routes,
      { method: "GET", path: "/api/v2/projects/P/notes/NOTE-003", respond: () => noteOut("NOTE-003", { version: "v-n3", summary: "Third", body: "Text" }) },
      {
        method: "POST",
        path: "/api/v2/notices/11/decision",
        respond: () => {
          remove("NOTE-003");
          return { notice: notice(11, "item_completed"), note: noteOut("NOTE-003", { status: "promoted" }), item: apiItem("STORY-077", { type: "Story" }) };
        },
      },
    ]);
    renderModal();

    const row = (await screen.findByText("Summary NOTE-003")).closest(".due-row") as HTMLElement;
    await userEvent.click(await within(row).findByRole("button", { name: "Befördern" }));
    const dialog = await screen.findByRole("dialog", { name: "Note NOTE-003 befördern" });
    await userEvent.type(within(dialog).getByRole("textbox", { name: "Bereich" }), "Core");
    await userEvent.type(within(dialog).getByRole("textbox", { name: "Fertigstellungskriterien" }), "Done.");
    await userEvent.click(within(dialog).getByRole("button", { name: "Befördern" }));

    expect(await screen.findByText("Befördert zu STORY-077.")).toBeInTheDocument();
    expect(await calls.find((c) => c.path.endsWith("/decision"))!.body()).toMatchObject({
      decision: "promote",
      version: "v-n3",
      promotion: { item_type: "Story", area: "Core", goal: "Text", completion_criteria: "Done." },
    });
  });

  it("opens a note in the Notes area and closes", async () => {
    stubRoutes(dueRoutes(ROWS).routes);
    const onClose = vi.fn();
    function Probe() {
      const { state } = useUiState();
      return <div data-testid="open">{state.currentView}:{state.selectedNote?.label ?? ""}</div>;
    }
    renderWithProviders(
      <>
        <DueModal items={ITEMS} projects={["P"]} onClose={onClose} />
        <Probe />
      </>,
    );

    await userEvent.click(within((await screen.findByText("Summary NOTE-002")).closest(".due-row") as HTMLElement).getByRole("button", { name: "In Notes öffnen" }));

    expect(onClose).toHaveBeenCalled();
    expect(screen.getByTestId("open")).toHaveTextContent("notes:NOTE-002");
  });

  it("says so when nothing is due, and closes once the last row is done", async () => {
    const { routes, remove } = dueRoutes([due("NOTE-001")]);
    const onClose = vi.fn();
    stubRoutes([
      ...routes,
      { method: "GET", path: "/api/v2/projects/P/notes/NOTE-001", respond: () => noteOut("NOTE-001") },
      {
        method: "POST",
        path: "/api/v2/projects/P/notes/NOTE-001/finish",
        respond: () => {
          remove("NOTE-001");
          return noteOut("NOTE-001", { archived: true });
        },
      },
    ]);
    renderModal(onClose);

    await userEvent.click(await screen.findByRole("button", { name: "Erledigen" }));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it("shows an empty list as such", async () => {
    stubRoutes(dueRoutes([]).routes);
    renderModal();

    expect(await screen.findByText("Nichts ist fällig.")).toBeInTheDocument();
  });
});
