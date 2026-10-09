import { describe, expect, it } from "vitest";
import { sidebarSections } from "./sidebar";

describe("sidebarSections", () => {
  it("gives the backlog views the item status and priority", () => {
    for (const view of ["tree", "graph", "kanban"] as const) expect(sidebarSections(view)).toEqual(["itemStatus", "itemPriority"]);
  });

  it("gives the notes area the note status and the trash nothing beyond search and projects", () => {
    expect(sidebarSections("notes")).toEqual(["noteStatus"]);
    expect(sidebarSections("trash")).toEqual([]);
  });
});
