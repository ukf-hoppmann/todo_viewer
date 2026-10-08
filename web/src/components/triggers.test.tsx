import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { Schemas } from "../api/client";
import { toItems } from "../domain/model";
import { toIsoWithZone } from "../domain/notes";
import { indexNote, indexTopic, jsonResponse, linkOut, noteOut, notesBaseRoutes, stubRoutes, type Route } from "../test/api";
import { apiItem, renderWithProviders } from "../test/render";
import { NoteDetail } from "./NoteDetail";
import { SnoozeDialog } from "./SnoozeDialog";

const BASE = "/api/v2/projects/P/notes/NOTE-001";
const ITEMS = toItems([
  apiItem("STORY-001", { title: "Parse backlog", status: "In progress" }),
  apiItem("TASK-009", { project: "Q", key: "t/TASK-009", source_id: "t", title: "Elsewhere", status: "Completed" }),
]);
const TRIGGER = (over: Partial<Schemas["TriggerOut"]> = {}): Schemas["TriggerOut"] => ({
  id: 7,
  kind: "time",
  at: "2027-06-15T12:00:00Z",
  fired_at: null,
  already_met: false,
  target: null,
  target_project: null,
  target_display: null,
  target_status: null,
  reachable: null,
  unreachable_reason: null,
  ...over,
});

function routes(note = noteOut("NOTE-001"), more: Route[] = []): Route[] {
  return [
    { method: "GET", path: BASE, respond: () => note },
    { method: "GET", path: `${BASE}/links`, respond: () => [linkOut(1)] },
    { method: "GET", path: `${BASE}/documents`, respond: () => [] },
    ...more,
  ];
}

function renderDetail(topics = [indexTopic("TOPIC-001", { name: "Ideas", path: ["Ideas"] })]) {
  return renderWithProviders(
    <NoteDetail note={{ project: "P", label: "NOTE-001" }} projects={["P", "Q"]} topics={topics} notes={[indexNote("NOTE-001")]} items={ITEMS} onClose={vi.fn()} onOpenNote={vi.fn()} />,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("TriggerEditor", () => {
  it("lists the triggers with their state and removes one", async () => {
    const calls = stubRoutes(
      routes(
        noteOut("NOTE-001", {
          triggers: [
            TRIGGER(),
            TRIGGER({ id: 8, kind: "event", at: null, target: "STORY-001", target_display: "P · STORY-001", target_status: "Completed", fired_at: "2027-01-01T00:00:00Z", already_met: true }),
          ],
        }),
        [{ method: "DELETE", path: `${BASE}/triggers/7`, respond: () => noteOut("NOTE-001") }],
      ),
    );
    renderDetail();

    expect(await screen.findByText(/Zeitpunkt/)).toBeInTheDocument();
    expect(screen.getByText(/Wenn P · STORY-001 den Status „Completed“ erreicht/)).toBeInTheDocument();
    expect(screen.getByText("eingetroffen")).toBeInTheDocument();
    expect(screen.getByText("war beim Anlegen schon erreicht")).toBeInTheDocument();

    await userEvent.click(screen.getAllByRole("button", { name: "Entfernen" })[0]!);
    await waitFor(() => expect(calls.some((c) => c.method === "DELETE")).toBe(true));
  });

  it("adds a time trigger with the local time as a UTC moment", async () => {
    const calls = stubRoutes(routes(undefined, [{ method: "POST", path: `${BASE}/triggers`, respond: () => jsonResponse(noteOut("NOTE-001"), 201) }]));
    renderDetail();

    await userEvent.click(await screen.findByRole("button", { name: "＋ Auslöser" }));
    const form = screen.getByRole("form", { name: "＋ Auslöser" });
    await userEvent.type(within(form).getByLabelText("Datum und Uhrzeit"), "2027-06-15T09:30");
    await userEvent.click(within(form).getByRole("button", { name: "Auslöser anlegen" }));

    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(await calls.find((c) => c.method === "POST")!.body()).toEqual({ kind: "time", at: toIsoWithZone("2027-06-15T09:30") });
  });

  it("warns before saving when the watched item has the status already", async () => {
    const calls = stubRoutes(routes(undefined, [{ method: "POST", path: `${BASE}/triggers`, respond: () => jsonResponse(noteOut("NOTE-001"), 201) }]));
    renderDetail();

    await userEvent.click(await screen.findByRole("button", { name: "＋ Auslöser" }));
    const form = screen.getByRole("form", { name: "＋ Auslöser" });
    await userEvent.selectOptions(within(form).getByLabelText("Art"), "event");
    await userEvent.selectOptions(within(form).getByLabelText("Projekt"), "Q");
    await userEvent.selectOptions(within(form).getByLabelText("Auswahl"), "TASK-009");
    expect(within(form).getByRole("status")).toHaveTextContent("würde sofort eintreffen"); // default target status: Completed

    await userEvent.selectOptions(within(form).getByLabelText("Zielstatus"), "Rejected");
    expect(within(form).queryByRole("status")).not.toBeInTheDocument();

    await userEvent.click(within(form).getByRole("button", { name: "Auslöser anlegen" }));
    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(await calls.find((c) => c.method === "POST")!.body()).toEqual({ kind: "event", target: "TASK-009", target_project: "Q", target_status: "Rejected" });
  });

  it("needs a topic with a due date for a topic-due trigger", async () => {
    stubRoutes(routes());
    renderDetail();

    await userEvent.click(await screen.findByRole("button", { name: "＋ Auslöser" }));
    const form = screen.getByRole("form", { name: "＋ Auslöser" });
    await userEvent.selectOptions(within(form).getByLabelText("Art"), "topic_due");

    expect(within(form).getByText(/Topic mit Termin/)).toBeInTheDocument();
    expect(within(form).getByRole("button", { name: "Auslöser anlegen" })).toBeDisabled();
  });

  it("adds a topic-due trigger when the topic has a date", async () => {
    const calls = stubRoutes(
      routes(noteOut("NOTE-001", { topic: "TOPIC-001" }), [{ method: "POST", path: `${BASE}/triggers`, respond: () => jsonResponse(noteOut("NOTE-001"), 201) }]),
    );
    renderDetail([indexTopic("TOPIC-001", { name: "Ideas", path: ["Ideas"], due_at: "2027-09-01T12:00:00Z" })]);

    await userEvent.click(await screen.findByRole("button", { name: "＋ Auslöser" }));
    const form = screen.getByRole("form", { name: "＋ Auslöser" });
    await userEvent.selectOptions(within(form).getByLabelText("Art"), "topic_due");
    await userEvent.click(within(form).getByRole("button", { name: "Auslöser anlegen" }));

    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(await calls.find((c) => c.method === "POST")!.body()).toEqual({ kind: "topic_due" });
  });

  it("does not offer the trigger mode any/all", async () => {
    stubRoutes(routes());
    renderDetail();

    await userEvent.click(await screen.findByRole("button", { name: "＋ Auslöser" }));

    expect(screen.queryByText(/Modus|any|all/i)).not.toBeInTheDocument();
  });

  it("only reads the triggers of a closed note", async () => {
    stubRoutes(routes(noteOut("NOTE-001", { archived: true, triggers: [TRIGGER()] })));
    renderDetail();

    expect(await screen.findByText(/Zeitpunkt/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Entfernen" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "＋ Auslöser" })).not.toBeInTheDocument();
  });
});

describe("SnoozeDialog", () => {
  it("snoozes until tomorrow 08:00 local time with the version it was opened for", async () => {
    vi.useFakeTimers({ toFake: ["Date"], now: new Date(2027, 5, 10, 15, 30) });
    const calls = stubRoutes([{ method: "POST", path: `${BASE}/snooze`, respond: () => noteOut("NOTE-001") }]);
    const onClose = vi.fn();
    renderWithProviders(<SnoozeDialog project="P" label="NOTE-001" version="v1" projects={["P"]} items={ITEMS} onClose={onClose} />);

    await userEvent.click(screen.getByRole("button", { name: "Morgen früh" }));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
    expect(await calls[0]!.body()).toEqual({ version: "v1", review_at: new Date(2027, 5, 11, 8, 0).toISOString() });
  });

  it("snoozes until an own date", async () => {
    const calls = stubRoutes([{ method: "POST", path: `${BASE}/snooze`, respond: () => noteOut("NOTE-001") }]);
    renderWithProviders(<SnoozeDialog project="P" label="NOTE-001" version="v1" projects={["P"]} items={ITEMS} onClose={vi.fn()} />);

    const input = screen.getByLabelText("Eigenes Datum");
    await userEvent.clear(input);
    await userEvent.type(input, "2027-12-24T18:00");
    await userEvent.click(screen.getByRole("button", { name: "Bis dahin zurückstellen" }));

    await waitFor(() => expect(calls).toHaveLength(1));
    expect(await calls[0]!.body()).toEqual({ version: "v1", review_at: toIsoWithZone("2027-12-24T18:00") });
  });

  it("snoozes until an event with a new trigger", async () => {
    const calls = stubRoutes([{ method: "POST", path: `${BASE}/snooze`, respond: () => noteOut("NOTE-001") }]);
    renderWithProviders(<SnoozeDialog project="P" label="NOTE-001" version="v1" projects={["P", "Q"]} items={ITEMS} onClose={vi.fn()} />);

    await userEvent.click(screen.getByRole("checkbox", { name: "Bei einem Ereignis" }));
    await userEvent.selectOptions(screen.getByLabelText("Auswahl"), "STORY-001");
    await userEvent.click(screen.getByRole("button", { name: "Bis zum Ereignis zurückstellen" }));

    await waitFor(() => expect(calls).toHaveLength(1));
    expect(await calls[0]!.body()).toEqual({
      version: "v1",
      trigger: { kind: "event", target: "STORY-001", target_project: "P", target_status: "Completed" },
    });
  });

  it("shows an error of the server and stays open", async () => {
    stubRoutes([{ method: "POST", path: `${BASE}/snooze`, respond: () => new Response(JSON.stringify({ code: "version_conflict", message: "x", details: {} }), { status: 409, headers: { "Content-Type": "application/json" } }) }]);
    const onClose = vi.fn();
    renderWithProviders(<SnoozeDialog project="P" label="NOTE-001" version="v1" projects={["P"]} items={ITEMS} onClose={onClose} />);

    await userEvent.click(screen.getByRole("button", { name: "In einer Woche" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("inzwischen geändert");
    expect(onClose).not.toHaveBeenCalled();
  });
});

describe("Topic due date", () => {
  it("sets and clears the due date of a topic", async () => {
    const { NotesView } = await import("../views/NotesView");
    const topics = [indexTopic("TOPIC-001", { name: "Ideas", path: ["Ideas"], due_at: "2027-09-01T12:00:00Z" })];
    const calls = stubRoutes([...notesBaseRoutes(topics, []), { method: "PATCH", path: "/api/v2/projects/P/topics/TOPIC-001", respond: () => ({}) }]);
    renderWithProviders(<NotesView items={[]} />);

    await userEvent.click(await screen.findByRole("button", { name: /Ideas/ }));
    await userEvent.click(screen.getByRole("button", { name: "Termin" }));
    await userEvent.clear(screen.getByLabelText("Termin (leer: kein Termin)"));
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    await waitFor(() => expect(calls.some((c) => c.method === "PATCH")).toBe(true));
    expect(await calls.find((c) => c.method === "PATCH")!.body()).toEqual({ due_at: null });
  });
});
