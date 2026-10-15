import type { Schemas } from "../api/client";
import { canRun, changeCount, conflictCount, directionOf, isInSync, needsAttention, type SyncState, switchDirection } from "./sync";

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

    expect(states.filter(needsAttention)).toEqual(["mirror_changed", "both_changed", "unreadable"]);
  });
});
