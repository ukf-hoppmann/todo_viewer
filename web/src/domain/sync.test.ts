import type { Schemas } from "../api/client";
import { canRun, changeCount, defaultDirection, hasMissing, isInSync, needsAttention, type SyncState, switchDirection } from "./sync";

type Section = Schemas["SyncSectionOut"];
const entry = (label: string, name: string | null = null) => ({ label, title: `Title ${label}`, name });
const section = (over: Partial<Section> = {}): Section => ({ created: [], changed: [], unchanged: 0, missing: [], ...over });
const preview = (items: Partial<Section> = {}, documents: Partial<Section> = {}): Schemas["SyncOut"] => ({
  executed: false,
  token: "t",
  items: section(items),
  documents: section(documents),
  skipped: [],
  deleted: [],
  kept: [],
});

describe("sync preview helpers", () => {
  it("counts what a sync would do, items and documents together", () => {
    const p = preview({ created: [entry("A"), entry("B")], changed: [entry("C")], unchanged: 5 }, { missing: [entry("A", "a.md")] });

    expect(changeCount(p)).toBe(4);
    expect(hasMissing(p)).toBe(true);
    expect(isInSync(p)).toBe(false);
  });

  it("is in sync when nothing is created, changed, or missing", () => {
    const p = preview({ unchanged: 3 }, { unchanged: 1 });

    expect([changeCount(p), hasMissing(p), isInSync(p)]).toEqual([0, false, true]);
  });

  it("a plain sync can always run; a switch must not leave missing entries behind", () => {
    const missing = preview({ missing: [entry("A")] });

    expect(canRun(missing, "sync", false)).toBe(true);
    expect(canRun(missing, "switch", false)).toBe(false);
    expect(canRun(missing, "switch", true)).toBe(true);
    expect(canRun(preview({ created: [entry("A")] }), "switch", false)).toBe(true);
  });

  it("a markdown project is read into the database, a database project is written out", () => {
    expect(switchDirection("markdown")).toBe("from_md");
    expect(switchDirection("database")).toBe("to_md");
  });
});

describe("sync direction and state", () => {
  it("syncs from the primary source to the mirror unless told otherwise", () => {
    expect(defaultDirection("database")).toBe("to_md");
    expect(defaultDirection("markdown")).toBe("from_md");
  });

  it("asks for attention where something has to be done, not where the primary source simply moved on", () => {
    const states: SyncState[] = ["none", "in_sync", "mirror_changed", "primary_changed", "both_changed", "unknown", "unreadable"];

    expect(states.filter(needsAttention)).toEqual(["mirror_changed", "both_changed", "unreadable"]);
  });
});
