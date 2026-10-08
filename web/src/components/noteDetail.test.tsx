import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { toItems } from "../domain/model";
import { errorResponse, indexNote, indexTopic, jsonResponse, linkOut, noteOut, stubRoutes, type Route } from "../test/api";
import { apiItem, renderWithProviders } from "../test/render";
import { NoteDetail } from "./NoteDetail";

const REF = { project: "P", label: "NOTE-001" };
const TOPICS = [indexTopic("TOPIC-001", { name: "Ideas", path: ["Ideas"] })];
const NOTES = [indexNote("NOTE-001"), indexNote("NOTE-002", { summary: "The other one" })];
const ITEMS = toItems([apiItem("STORY-001", { title: "Parse backlog", status: "In progress" }), apiItem("TASK-009", { project: "Q", key: "t/TASK-009", source_id: "t", title: "Elsewhere" })]);

const BASE = "/api/v2/projects/P/notes/NOTE-001";

function detailRoutes(note = noteOut("NOTE-001", { body: "Some **long** text", topic: "TOPIC-001" }), more: Route[] = []): Route[] {
  return [
    { method: "GET", path: BASE, respond: () => note },
    { method: "GET", path: `${BASE}/links`, respond: () => [linkOut(1), linkOut(2, { role: "trigger", target: "STORY-002", target_display: "P · STORY-002" })] },
    { method: "GET", path: `${BASE}/documents`, respond: () => [{ name: "NOTE-001_notes.md", kind: "notes" }, { name: "NOTE-001_spec.md", kind: "spec" }] },
    ...more,
  ];
}

function renderDetail(onClose = vi.fn(), onOpenNote = vi.fn()) {
  return renderWithProviders(<NoteDetail note={REF} projects={["P", "Q"]} topics={TOPICS} notes={NOTES} items={ITEMS} onClose={onClose} onOpenNote={onOpenNote} />);
}

afterEach(() => vi.unstubAllGlobals());

describe("NoteDetail", () => {
  it("shows summary, long text, state, topic, links and documents", async () => {
    stubRoutes(detailRoutes());
    renderDetail();

    expect(await screen.findByRole("heading", { name: "Summary NOTE-001" })).toBeInTheDocument();
    expect(screen.getByText("long")).toBeInTheDocument();
    expect(screen.getByText("wartet")).toBeInTheDocument();
    expect(screen.getByText("Ideas")).toBeInTheDocument();
    expect(await screen.findByText("P · STORY-001")).toBeInTheDocument();
    expect(screen.getByText("Parse backlog")).toBeInTheDocument();
    expect(await screen.findByRole("button", { name: "Notizen" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Spec" })).toBeInTheDocument();
  });

  it("saves summary, long text and topic with the version it read", async () => {
    const calls = stubRoutes(detailRoutes(undefined, [{ method: "PATCH", path: BASE, respond: () => noteOut("NOTE-001") }]));
    renderDetail();

    await userEvent.click(await screen.findByRole("button", { name: "Bearbeiten" }));
    await userEvent.clear(screen.getByLabelText("Kurzfassung"));
    await userEvent.type(screen.getByLabelText("Kurzfassung"), "A better summary");
    await userEvent.selectOptions(screen.getByLabelText("Topic"), "");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    await waitFor(() => expect(calls.some((c) => c.method === "PATCH")).toBe(true));
    expect(await calls.find((c) => c.method === "PATCH")!.body()).toEqual({
      version: "v-NOTE-001",
      summary: "A better summary",
      body: "Some **long** text",
      topic: null,
    });
  });

  it("reports a version conflict and reloads the current state on request", async () => {
    let current = noteOut("NOTE-001", { summary: "Mine" });
    stubRoutes(detailRoutes(undefined, [{ method: "PATCH", path: BASE, respond: () => errorResponse(409, "version_conflict", { id: "NOTE-001" }) }]).map((r) => (r.method === "GET" && r.path === BASE ? { ...r, respond: () => current } : r)));
    renderDetail();

    await userEvent.click(await screen.findByRole("button", { name: "Bearbeiten" }));
    current = noteOut("NOTE-001", { summary: "Theirs", version: "v-new" });
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    expect(await screen.findByText(/Die Note wurde inzwischen geändert/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Neu laden" }));

    await waitFor(() => expect(screen.getByLabelText("Kurzfassung")).toHaveValue("Theirs"));
  });

  it("closes a note as done or dropped and keeps it", async () => {
    const calls = stubRoutes(
      detailRoutes(undefined, [
        { method: "POST", path: `${BASE}/finish`, respond: () => noteOut("NOTE-001", { archived: true }) },
        { method: "POST", path: `${BASE}/keep`, respond: () => noteOut("NOTE-001") },
      ]),
    );
    renderDetail();

    await userEvent.click(await screen.findByRole("button", { name: "Behalten" }));
    await userEvent.click(screen.getByRole("button", { name: "Erledigen" }));
    await userEvent.click(screen.getByRole("button", { name: "Verwerfen" }));

    await waitFor(() => expect(calls.filter((c) => c.method === "POST")).toHaveLength(3));
    const bodies = await Promise.all(calls.filter((c) => c.method === "POST").map(async (c) => [c.path.split("/").pop(), await c.body()]));
    expect(bodies).toEqual([
      ["keep", { version: "v-NOTE-001" }],
      ["finish", { version: "v-NOTE-001", status: "done" }],
      ["finish", { version: "v-NOTE-001", status: "dropped" }],
    ]);
  });

  it("deletes after a confirmation and closes the detail", async () => {
    const onClose = vi.fn();
    const calls = stubRoutes(detailRoutes(undefined, [{ method: "DELETE", path: BASE, respond: () => noteOut("NOTE-001", { deleted: "2027-01-01T00:00:00Z" }) }]));
    renderDetail(onClose);

    await userEvent.click(await screen.findByRole("button", { name: "Löschen" }));
    expect(calls.some((c) => c.method === "DELETE")).toBe(false);
    await userEvent.click(screen.getByRole("button", { name: "In den Papierkorb" }));

    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  it("only reads a closed note", async () => {
    stubRoutes(detailRoutes(noteOut("NOTE-001", { archived: true, status: "done" })));
    renderDetail();

    expect(await screen.findByText(/abgeschlossen oder gelöscht/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Bearbeiten" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "＋ Link" })).not.toBeInTheDocument();
  });
});

describe("NoteLinks", () => {
  it("offers to remove a reference link, but not one that belongs to a trigger", async () => {
    const calls = stubRoutes(detailRoutes(undefined, [{ method: "DELETE", path: `${BASE}/links/1`, respond: () => [] }]));
    renderDetail();

    await screen.findByText("P · STORY-001");
    const removeButtons = screen.getAllByRole("button", { name: "Link lösen" });
    expect(removeButtons).toHaveLength(1);
    expect(screen.getByText("Auslöser", { selector: ".badge" })).toBeInTheDocument();

    await userEvent.click(removeButtons[0]!);
    await waitFor(() => expect(calls.some((c) => c.method === "DELETE")).toBe(true));
  });

  it("marks an unreachable target", async () => {
    stubRoutes([
      ...detailRoutes().filter((r) => !r.path.toString().endsWith("/links")),
      { method: "GET", path: `${BASE}/links`, respond: () => [linkOut(1, { reachable: false, unreachable_reason: "project_not_registered", target_project: "Gone", target_display: "Gone · STORY-001" })] },
    ]);
    renderDetail();

    expect(await screen.findByText("nicht erreichbar")).toBeInTheDocument();
  });

  it("links an item of another project", async () => {
    const calls = stubRoutes(detailRoutes(undefined, [{ method: "POST", path: `${BASE}/links`, respond: () => jsonResponse(linkOut(3), 201) }]));
    renderDetail();

    await userEvent.click(await screen.findByRole("button", { name: "＋ Link" }));
    const form = screen.getByRole("form", { name: "＋ Link" });
    await userEvent.selectOptions(within(form).getByLabelText("Projekt"), "Q");
    await userEvent.selectOptions(within(form).getByLabelText("Auswahl"), "TASK-009");
    await userEvent.click(within(form).getByRole("button", { name: "Link setzen" }));

    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(await calls.find((c) => c.method === "POST")!.body()).toEqual({ kind: "item", role: "reference", target: "TASK-009", target_project: "Q" });
  });

  it("links another note and jumps to it", async () => {
    const onOpenNote = vi.fn();
    const calls = stubRoutes([
      ...detailRoutes().filter((r) => !r.path.toString().endsWith("/links")),
      { method: "GET", path: `${BASE}/links`, respond: () => [linkOut(5, { kind: "note", target: "NOTE-002", target_display: "P · NOTE-002" })] },
      { method: "POST", path: `${BASE}/links`, respond: () => jsonResponse(linkOut(6), 201) },
    ]);
    renderDetail(vi.fn(), onOpenNote);

    await userEvent.click(await screen.findByRole("button", { name: "P · NOTE-002" }));
    expect(onOpenNote).toHaveBeenCalledWith({ project: "P", label: "NOTE-002" });

    await userEvent.click(screen.getByRole("button", { name: "＋ Link" }));
    const form = screen.getByRole("form", { name: "＋ Link" });
    await userEvent.selectOptions(within(form).getByLabelText("Ziel"), "note");
    await userEvent.selectOptions(within(form).getByLabelText("Auswahl"), "P/NOTE-002");
    await userEvent.click(within(form).getByRole("button", { name: "Link setzen" }));
    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(await calls.find((c) => c.method === "POST")!.body()).toEqual({ kind: "note", role: "reference", target: "NOTE-002", target_project: "P" });
  });
});

describe("NoteDocuments", () => {
  it("reads a document and writes it back with its version", async () => {
    const calls = stubRoutes(
      detailRoutes(undefined, [
        { method: "GET", path: `${BASE}/documents/NOTE-001_spec.md`, respond: () => ({ name: "NOTE-001_spec.md", kind: "spec", content: "# Spec text", version: "d1" }) },
        { method: "PUT", path: `${BASE}/documents/NOTE-001_spec.md`, respond: () => ({ name: "NOTE-001_spec.md", kind: "spec", content: "# Spec text\nmore", version: "d2" }) },
      ]),
    );
    renderDetail();

    await userEvent.click(await screen.findByRole("button", { name: "Spec" }));
    expect(await screen.findByRole("heading", { name: "Spec text" })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "✎ Bearbeiten" }));
    await userEvent.type(screen.getByLabelText("Markdown"), "\nmore");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    await waitFor(() => expect(calls.some((c) => c.method === "PUT")).toBe(true));
    expect(await calls.find((c) => c.method === "PUT")!.body()).toEqual({ content: "# Spec text\nmore", version: "d1" });
  });

  it("appends a dated notes entry", async () => {
    const calls = stubRoutes(
      detailRoutes(undefined, [
        { method: "POST", path: `${BASE}/notes`, respond: () => ({ name: "NOTE-001_notes.md", kind: "notes", content: "# n", version: "n1" }) },
        { method: "GET", path: `${BASE}/documents/NOTE-001_notes.md`, respond: () => ({ name: "NOTE-001_notes.md", kind: "notes", content: "# n", version: "n1" }) },
      ]),
    );
    renderDetail();

    await userEvent.click(await screen.findByRole("button", { name: /Notiz-Eintrag/ }));
    await userEvent.type(screen.getByLabelText("Thema"), "First talk");
    await userEvent.type(screen.getByLabelText(/^Besprochen/), "A point");
    await userEvent.click(screen.getByRole("button", { name: "Eintrag anhängen" }));

    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(await calls.find((c) => c.method === "POST")!.body()).toMatchObject({ topic: "First talk", discussed: ["A point"] });
  });
});
