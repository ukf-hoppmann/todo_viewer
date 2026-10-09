import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { errorResponse, indexNote, indexTopic, notesBaseRoutes, stubRoutes } from "../test/api";
import { renderWithProviders, sourceStatus } from "../test/render";
import { NotesView } from "../views/NotesView";

const TOPICS = [
  indexTopic("TOPIC-001", { name: "Ideas", path: ["Ideas"], note_count: 1 }),
  indexTopic("TOPIC-002", { name: "Later", parent: "TOPIC-001", path: ["Ideas", "Later"], note_count: 1 }),
  indexTopic("TOPIC-003", { name: "Plans", path: ["Plans"] }),
];
const NOTES = [
  indexNote("NOTE-001", { summary: "An idea", topic: "TOPIC-001", status: "due", reason: "trigger" }),
  indexNote("NOTE-002", { summary: "Something for later", topic: "TOPIC-002", review_at: "2027-06-15T12:00:00Z" }),
  indexNote("NOTE-003", { summary: "No topic yet" }),
];

afterEach(() => vi.unstubAllGlobals());

/** The row of a topic (or project), where its actions sit. */
const row = (name: string | RegExp) => screen.getByText(name).closest(".node-line, .project-title") as HTMLElement;

describe("NotesView", () => {
  it("shows project, topics, sub-topics and notes as one tree, empty topics and notes without topic included", async () => {
    stubRoutes(notesBaseRoutes(TOPICS, NOTES));
    renderWithProviders(<NotesView items={[]} />);

    expect(await screen.findByText("P (3)")).toBeInTheDocument();
    const lines = [...document.querySelectorAll(".node-title")].map((e) => e.textContent);
    expect(lines).toEqual(["Ideas", "Later", "NOTE-002 — Something for later", "NOTE-001 — An idea", "Plans", "Ohne Topic", "NOTE-003 — No topic yet"]);
    expect(within(row("Later")).getByText("Topic")).toHaveClass("node-type");
    expect(within(row("Ideas")).getByText("2")).toBeInTheDocument();
    const first = screen.getByText("An idea").closest(".nt-note") as HTMLElement;
    expect(within(first).getAllByTitle("fällig")).toHaveLength(2);
    expect(within(first).getByText("Auslöser")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Nach Topic gruppieren" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("inkl. Unterthemen")).not.toBeInTheDocument();
  });

  it("opens the chosen note in the UI state", async () => {
    stubRoutes(notesBaseRoutes(TOPICS, NOTES));
    renderWithProviders(<NotesView items={[]} />);

    await userEvent.click(await screen.findByText("No topic yet"));

    expect(screen.getByText("No topic yet").closest(".nt-note")).toHaveAttribute("aria-pressed", "true");
  });

  it("collapses a branch, remembers it, and unfolds it again for a note opened from elsewhere", async () => {
    stubRoutes(notesBaseRoutes(TOPICS, NOTES));
    const first = renderWithProviders(<NotesView items={[]} />);

    await screen.findByText("Something for later");
    await userEvent.click(within(row("Ideas")).getByRole("button", { name: "Zuklappen" }));
    expect(screen.queryByText("Later")).not.toBeInTheDocument();
    await userEvent.click(within(row("Ideas")).getByRole("button", { name: "Aufklappen" }));
    expect(screen.getByText("Later")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Topics zuklappen" }));
    expect(screen.queryByText("Ideas")).toBeInTheDocument();
    expect(screen.queryByText("Later")).not.toBeInTheDocument();
    expect(screen.queryByText("No topic yet")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Topics aufklappen" }));
    expect(screen.getByText("No topic yet")).toBeInTheDocument();
    first.unmount();

    renderWithProviders(<NotesView items={[]} />, {
      collapsed: new Set(["note-project:P", "note-topic:P/TOPIC-001", "note-topic:P/TOPIC-002"]),
      selectedNote: { project: "P", label: "NOTE-002" },
    });
    expect(await screen.findByText("Something for later")).toBeInTheDocument();
    expect(screen.getByText("Something for later").closest(".nt-note")).toHaveAttribute("aria-pressed", "true");
  });

  it("creates a topic below the chosen one", async () => {
    const calls = stubRoutes([
      ...notesBaseRoutes(TOPICS, NOTES),
      { method: "POST", path: "/api/v2/projects/P/topics", respond: () => new Response(JSON.stringify({ label: "TOPIC-004" }), { status: 201, headers: { "Content-Type": "application/json" } }) },
    ]);
    renderWithProviders(<NotesView items={[]} />);

    await screen.findByText("Plans");
    await userEvent.click(within(row("Plans")).getByRole("button", { name: "＋ Unter-Topic" }));
    await userEvent.type(screen.getByLabelText("Name"), "Drafts");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    const post = calls.find((c) => c.method === "POST")!;
    expect(post.path).toBe("/api/v2/projects/P/topics");
    expect(await post.body()).toEqual({ name: "Drafts", parent: "TOPIC-003" });
  });

  it("shows the depth error of the server as a text", async () => {
    stubRoutes([
      ...notesBaseRoutes(TOPICS, NOTES),
      { method: "POST", path: "/api/v2/projects/P/topics", respond: () => errorResponse(400, "topic_too_deep", { id: "TOPIC-004", max_depth: "3" }) },
    ]);
    renderWithProviders(<NotesView items={[]} />);

    await screen.findByText("Later");
    await userEvent.click(within(row("Later")).getByRole("button", { name: "＋ Unter-Topic" }));
    await userEvent.type(screen.getByLabelText("Name"), "Too deep");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("tiefer als erlaubt (3 Ebenen)");
  });

  it("renames and moves a topic", async () => {
    const calls = stubRoutes([
      ...notesBaseRoutes(TOPICS, NOTES),
      { method: "PATCH", path: "/api/v2/projects/P/topics/TOPIC-003", respond: () => ({}) },
      { method: "POST", path: "/api/v2/projects/P/topics/TOPIC-003/move", respond: () => ({}) },
    ]);
    renderWithProviders(<NotesView items={[]} />);

    await screen.findByText("Plans");
    await userEvent.click(within(row("Plans")).getByRole("button", { name: "Umbenennen" }));
    await userEvent.clear(screen.getByLabelText("Name"));
    await userEvent.type(screen.getByLabelText("Name"), "Plans 2");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));
    await waitFor(() => expect(calls.filter((c) => c.method === "PATCH")).toHaveLength(1));
    expect(await calls.find((c) => c.method === "PATCH")!.body()).toEqual({ name: "Plans 2" });

    await userEvent.click(within(row("Plans")).getByRole("button", { name: "Verschieben" }));
    await userEvent.selectOptions(screen.getByLabelText("Übergeordnetes Topic"), "TOPIC-001");
    await userEvent.click(screen.getByRole("button", { name: "Speichern" }));
    await waitFor(() => expect(calls.filter((c) => c.path.endsWith("/move"))).toHaveLength(1));
    expect(await calls.find((c) => c.path.endsWith("/move"))!.body()).toEqual({ parent: "TOPIC-001" });
  });

  it("asks again before deleting a topic that has content, then deletes it with its content", async () => {
    const calls = stubRoutes([
      ...notesBaseRoutes(TOPICS, NOTES),
      {
        method: "DELETE",
        path: "/api/v2/projects/P/topics/TOPIC-001",
        respond: (request) =>
          new URL(request.url).searchParams.get("cascade") === "true" ? { topics: [], notes: [] } : errorResponse(409, "topic_has_content", { id: "TOPIC-001", items: "NOTE-001, TOPIC-002" }),
      },
    ]);
    renderWithProviders(<NotesView items={[]} />);

    await screen.findByText("Ideas");
    await userEvent.click(within(row("Ideas")).getByRole("button", { name: "Löschen" }));
    await userEvent.click(screen.getByRole("button", { name: "In den Papierkorb" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("NOTE-001, TOPIC-002");

    await userEvent.click(screen.getByRole("button", { name: "Samt Inhalt in den Papierkorb" }));

    await waitFor(() => expect(calls.filter((c) => c.method === "DELETE")).toHaveLength(2));
    expect(calls.filter((c) => c.method === "DELETE").map((c) => c.search)).toEqual(["?cascade=false", "?cascade=true"]);
  });

  it("creates a note in a topic from the topic's row", async () => {
    const calls = stubRoutes([
      ...notesBaseRoutes(TOPICS, NOTES),
      { method: "POST", path: "/api/v2/projects/P/notes", respond: () => new Response(JSON.stringify({ project: "P", label: "NOTE-004" }), { status: 201, headers: { "Content-Type": "application/json" } }) },
    ]);
    renderWithProviders(<NotesView items={[]} />);

    await screen.findByText("Plans");
    await userEvent.click(within(row("Plans")).getByRole("button", { name: "Neue Note in „Plans“" }));
    await userEvent.type(screen.getByLabelText("Kurzfassung"), "A new thought");
    await userEvent.type(screen.getByLabelText("Langtext (optional)"), "More about it");
    await userEvent.click(screen.getByRole("button", { name: "Anlegen" }));

    await waitFor(() => expect(calls.some((c) => c.method === "POST")).toBe(true));
    expect(await calls.find((c) => c.method === "POST")!.body()).toEqual({
      summary: "A new thought",
      body: "More about it",
      topic: "TOPIC-003",
      trigger_mode: "any",
    });
  });

  it("wants a summary before a note can be created", async () => {
    stubRoutes(notesBaseRoutes(TOPICS, NOTES));
    renderWithProviders(<NotesView items={[]} />);

    await userEvent.click(await screen.findByRole("button", { name: "＋ Note" }));

    expect(screen.getByRole("button", { name: "Anlegen" })).toBeDisabled();
  });

  it("sends the statuses ticked in the sidebar to the server instead of cutting them in the browser", async () => {
    const calls = stubRoutes(notesBaseRoutes(TOPICS, NOTES));
    renderWithProviders(<NotesView items={[]} />, { hiddenNoteStatuses: new Set(["waiting", "snoozed", "dropped", "promoted"]) });
    await screen.findByText("An idea");

    const index = calls.filter((c) => c.path === "/api/v2/notes/index" && c.search.includes("status="));
    expect(index.map((c) => c.search)).toContain("?status=due&status=done");
    expect(screen.queryByRole("combobox", { name: "Status" })).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Nur fällige")).not.toBeInTheDocument();
  });

  it("shows nothing when no status is ticked", async () => {
    stubRoutes(notesBaseRoutes(TOPICS, NOTES));
    renderWithProviders(<NotesView items={[]} />, { hiddenNoteStatuses: new Set(["waiting", "due", "snoozed", "done", "dropped", "promoted"]) });

    expect(await screen.findByText("0 Notes")).toBeInTheDocument();
    expect(screen.queryByText("An idea")).not.toBeInTheDocument();
  });

  it("searches the notes with the sidebar search and resets search and statuses", async () => {
    stubRoutes(notesBaseRoutes(TOPICS, NOTES));
    renderWithProviders(<NotesView items={[]} />, { search: "later", hiddenNoteStatuses: new Set(["promoted"]) });

    expect(await screen.findByText("Something for later")).toBeInTheDocument();
    expect(screen.queryByText("An idea")).not.toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "Filter zurücksetzen" }));
    expect(screen.getByText("An idea")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Filter zurücksetzen" })).not.toBeInTheDocument();
  });

  it("shows only the projects ticked in the sidebar and lets the server cut when one is left", async () => {
    const two = [
      { method: "GET" as const, path: "/api/v2/backlog", respond: () => ({ items: [], sources: [sourceStatus({ id: "s1", project: "P", backend: "database" }), sourceStatus({ id: "s2", project: "Q", backend: "database" })] }) },
      { method: "GET" as const, path: "/api/v2/notes/index", respond: () => ({ topics: [], notes: [indexNote("NOTE-001", { summary: "In P" }), indexNote("NOTE-002", { summary: "In Q", project: "Q" })] }) },
    ];
    const calls = stubRoutes(two);
    renderWithProviders(<NotesView items={[]} />, { hiddenProjects: new Set(["Q"]) });

    expect(await screen.findByText("In P")).toBeInTheDocument();
    expect(screen.queryByText("In Q")).not.toBeInTheDocument();
    await waitFor(() => expect(calls.some((c) => c.path === "/api/v2/notes/index" && c.search.includes("project=P"))).toBe(true));
  });
});
