import type { Schemas } from "../api/client";
import { buildResolutions, canRun, summarizePreview, visibleKinds, changeCount, changedFields, choiceOf, conflictCount, conflictKey, directionOf, isInSync, needsAttention, type SyncState, switchDirection } from "./sync";

type Section = Schemas["SyncSectionOut"];
type Conflict = Schemas["SyncConflictOut"];
const entry = (label: string, name: string | null = null) => ({ label, title: `Title ${label}`, name, origin: null });
const conflict = (label: string, name: string | null = null): Conflict => ({
  kind: name ? "document" : "item", label, title: `Title ${label}`, name, reason: "both_changed", database: null, markdown: null,
});
const section = (over: Partial<Section> = {}): Section => ({ created: [], changed: [], unchanged: 0, ...over });
const preview = (items: Partial<Section> = {}, documents: Partial<Section> = {}, conflicts: Conflict[] = []): Schemas["SyncOut"] => ({
  executed: false,
  token: "t",
  items: section(items),
  documents: section(documents),
  topics: section(),
  notes: section(),
  note_documents: section(),
  conflicts,
  skipped: [],
  resolved: [],
  deleted: [],
  deferred: [],
  kept: [],
});

describe("sync preview helpers", () => {
  it("counts what a sync would carry over, items and documents together; conflicts are counted apart", () => {
    const p = preview({ created: [entry("A"), entry("B")], changed: [entry("C")], unchanged: 5 }, { changed: [entry("A", "a.md")] }, [conflict("D")]);

    expect(changeCount(p)).toBe(4);
    expect(conflictCount(p)).toBe(1);
    expect(isInSync(p)).toBe(false);
  });

  it("is in sync when nothing is carried over and nothing is in conflict", () => {
    const p = preview({ unchanged: 3 }, { unchanged: 1 });

    expect([changeCount(p), conflictCount(p), isInSync(p)]).toEqual([0, 0, true]);
    expect(isInSync(preview({}, {}, [conflict("A")]))).toBe(false);
  });

  it("a plain sync can always run; a switch waits for the conflicts to be decided", () => {
    const conflicting = preview({}, {}, [conflict("A")]);

    expect(canRun(conflicting, "sync")).toBe(true);
    expect(canRun(conflicting, "switch")).toBe(false);
    expect(canRun(preview({ created: [entry("A")] }), "switch")).toBe(true);
  });

  it("a markdown project is read into the database, a database project is written out", () => {
    expect(switchDirection("markdown")).toBe("from_md");
    expect(switchDirection("database")).toBe("to_md");
  });
});

describe("sync direction and state", () => {
  it("syncs in both directions unless the run is restricted to one", () => {
    expect(directionOf("both")).toBeNull();
    expect(directionOf("to_md")).toBe("to_md");
    expect(directionOf("from_md")).toBe("from_md");
  });

  it("asks for attention where something has to be done, not where the primary source simply moved on", () => {
    const states: SyncState[] = ["none", "in_sync", "mirror_changed", "primary_changed", "both_changed", "unknown", "unreadable"];

    expect(states.filter((s) => needsAttention(s))).toEqual(["mirror_changed", "both_changed", "unreadable"]);
  });

  it("asks for attention for open conflicts even where the states says the sides are in sync", () => {
    expect(needsAttention("in_sync", 2)).toBe(true);
    expect(needsAttention("in_sync", 0)).toBe(false);
  });
});

describe("deciding conflicts", () => {
  const item = (label: string, reason: Schemas["SyncConflictOut"]["reason"] = "both_changed"): Schemas["SyncConflictOut"] => ({
    kind: "item", label, title: `T ${label}`, name: null, reason, database: null, markdown: null,
  });
  const doc: Schemas["SyncConflictOut"] = { ...item("A"), kind: "document", name: "a.md" };

  it("keys a conflict by kind, label and document name", () => {
    expect(conflictKey(item("A"))).toBe("item/A/");
    expect(conflictKey(doc)).toBe("document/A/a.md");
  });

  it("sends only the decisions that are not 'defer'", () => {
    const choices = { [conflictKey(item("A"))]: "database", [conflictKey(doc)]: "markdown", [conflictKey(item("B"))]: "defer" } as const;

    expect(buildResolutions([item("A"), doc, item("B"), item("C")], choices)).toEqual([
      { kind: "item", label: "A", name: null, choice: "database" },
      { kind: "document", label: "A", name: "a.md", choice: "markdown" },
    ]);
  });

  it("defers everything by default", () => {
    expect(buildResolutions([item("A")], {})).toEqual([]);
    expect(choiceOf({}, item("A"))).toBe("defer");
  });

  it("lists the item fields that differ between the two versions, in order", () => {
    const c: Schemas["SyncConflictOut"] = {
      ...item("A"),
      database: { fields: [{ name: "id", value: "A" }, { name: "title", value: "x" }, { name: "goal", value: "g" }], text: null },
      markdown: { fields: [{ name: "id", value: "A" }, { name: "title", value: "y" }, { name: "goal", value: "g" }], text: null },
    };

    expect(changedFields(c).map((f) => f.name)).toEqual(["title"]);
    expect(changedFields({ ...c, database: null }).map((f) => f.name)).toEqual(["id", "title", "goal"]);
  });
});

describe("notes in the preview", () => {
  const notesPreview = (): Schemas["SyncOut"] => ({
    ...preview({ created: [entry("A")], unchanged: 1 }),
    topics: section({ unchanged: 2 }),
    notes: section({ created: [entry("NOTE-1"), entry("NOTE-2")], changed: [entry("NOTE-3")] }),
    note_documents: section({ changed: [entry("NOTE-3", "NOTE-3_notes.md")] }),
    conflicts: [{ ...conflict("NOTE-9"), kind: "note" }],
  });

  it("counts topics, notes, and their documents with the rest", () => {
    const p = notesPreview();

    expect(changeCount(p)).toBe(5);
    expect(conflictCount(p)).toBe(1);
    expect(isInSync(p)).toBe(false);
    expect(isInSync({ ...preview({ unchanged: 1 }), notes: section({ changed: [entry("NOTE-1")] }) })).toBe(false);
  });

  it("summarizes each kind and the total", () => {
    const sum = summarizePreview(notesPreview());

    expect(sum.notes).toEqual({ created: 2, changed: 1, unchanged: 0 });
    expect(sum.topics).toEqual({ created: 0, changed: 0, unchanged: 2 });
    expect(sum.total).toEqual({ created: 3, changed: 2, unchanged: 3 });
  });

  it("shows items and documents always and the notes sections only when there is something in them", () => {
    expect(visibleKinds(preview())).toEqual(["items", "documents"]);
    expect(visibleKinds(notesPreview())).toEqual(["items", "documents", "topics", "notes", "note_documents"]);
  });
});
