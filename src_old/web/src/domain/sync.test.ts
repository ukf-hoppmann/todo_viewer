import type { Schemas } from "../api/client";
import { buildResolutions, canRun, summarizePreview, visibleKinds, changeCount, changedFields, choiceOf, conflictCount, conflictKey, conflictSummary, decidedCount, decideMany, directionOf, isBulkDecidable, isInSync, needsAttention, type SyncState, switchDirection } from "./sync";

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
    const states: SyncState[] = ["none", "in_sync", "mirror_changed", "primary_changed", "both_changed", "unknown", "unreadable", "conflicts"];

    expect(states.filter((s) => needsAttention(s))).toEqual(["mirror_changed", "both_changed", "unreadable", "conflicts"]);
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

describe("reading a conflict at a glance", () => {
  const side = (fields: [string, string][]) => ({ fields: fields.map(([name, value]) => ({ name, value })), text: null });
  const item = (db: [string, string][] | null, md: [string, string][] | null, reason: Conflict["reason"] = "both_changed"): Conflict => ({
    kind: "item", label: "A", title: "T A", name: null, reason, database: db && side(db), markdown: md && side(md),
  });

  it("names the fields that differ, each with the value of both sides", () => {
    const c = item([["id", "A"], ["status", "Open"], ["priority", "High"]], [["id", "A"], ["status", "Completed"], ["priority", "High"]]);

    expect(conflictSummary(c)).toEqual({ kind: "fields", fields: [{ name: "status", database: "Open", markdown: "Completed" }], more: 0 });
  });

  it("shows the first three differing fields and counts the rest", () => {
    const names = ["a", "b", "c", "d", "e"];
    const c = item(names.map((n) => [n, "db"]), names.map((n) => [n, "file"]));

    const summary = conflictSummary(c);

    expect(summary).toMatchObject({ kind: "fields", more: 2 });
    expect(summary.kind === "fields" && summary.fields.map((f) => f.name)).toEqual(["a", "b", "c"]);
    expect(conflictSummary(c, 5)).toMatchObject({ kind: "fields", more: 0 });
  });

  it("says which side is missing for a deletion, instead of listing every field", () => {
    expect(conflictSummary(item(null, [["id", "A"]], "database_deleted"))).toEqual({ kind: "missing", side: "database" });
    expect(conflictSummary(item([["id", "A"]], null, "markdown_deleted"))).toEqual({ kind: "missing", side: "markdown" });
  });

  it("calls a conflict of two texts a text difference, and so an item whose listed fields do not differ", () => {
    const doc: Conflict = { ...item(null, null), kind: "document", name: "a.md", database: { fields: null, text: "x" }, markdown: { fields: null, text: "y" } };

    expect(conflictSummary(doc)).toEqual({ kind: "text" });
    expect(conflictSummary(item([["id", "A"]], [["id", "A"]]))).toEqual({ kind: "text" });
  });
});

describe("deciding many conflicts at once", () => {
  const conflict = (label: string, reason: Conflict["reason"]): Conflict => ({ kind: "item", label, title: `T ${label}`, name: null, reason, database: null, markdown: null });
  const a = conflict("A", "both_changed");
  const b = conflict("B", "both_new");
  const c = conflict("C", "database_deleted");
  const d = conflict("D", "markdown_deleted");

  it("covers what changed or is new on both sides, never a deletion", () => {
    expect([a, b, c, d].map(isBulkDecidable)).toEqual([true, true, false, false]);
  });

  it("sets the decision for every covered conflict and leaves the deletions as they are", () => {
    const before = { [conflictKey(c)]: "markdown" } as const;

    const after = decideMany([a, b, c, d], before, "database");

    expect(after).toEqual({ [conflictKey(c)]: "markdown", [conflictKey(a)]: "database", [conflictKey(b)]: "database" });
  });

  it("deferring all drops the decisions instead of storing 'defer', and keeps a decided deletion", () => {
    const decided = decideMany([a, b, c, d], { [conflictKey(d)]: "database" }, "markdown");

    expect(decideMany([a, b, c, d], decided, "defer")).toEqual({ [conflictKey(d)]: "database" });
  });

  it("leaves a single decision made afterwards in place, and a bulk decision overrides earlier single ones", () => {
    const all = decideMany([a, b], {}, "database");
    const own = { ...all, [conflictKey(b)]: "markdown" } as const;

    expect([choiceOf(own, a), choiceOf(own, b)]).toEqual(["database", "markdown"]);
    expect([choiceOf(decideMany([a, b], own, "database"), b)]).toEqual(["database"]);
  });

  it("counts the decided conflicts of this list, and a deferred or foreign decision does not count", () => {
    const choices = { [conflictKey(a)]: "database", [conflictKey(b)]: "defer", [conflictKey(c)]: "markdown", "item/Z/": "database" } as const;

    expect(decidedCount([a, b, c, d], choices)).toBe(2);
    expect(decidedCount([a, b, c, d], {})).toBe(0);
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
