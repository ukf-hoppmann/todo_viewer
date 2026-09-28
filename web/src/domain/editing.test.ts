import type { ApiItem } from "../api/client";
import { apiItem } from "../test/render";
import { changedFields, dependencyCandidates, draftOf, parentCandidates, rebaseDraft } from "./editing";
import { toItems } from "./model";

const [epic, story, task, sub, other, foreign] = toItems([
  apiItem("EPIC-1", { type: "Epic" }),
  apiItem("STORY-1", { type: "Story", parent: "EPIC-1", required_for_parent: true }),
  apiItem("TASK-1", { parent: "STORY-1", required_for_parent: true, dependencies: ["TASK-2"], summary: "S", area: "A" }),
  apiItem("TASK-3", { parent: "TASK-1", required_for_parent: false }),
  apiItem("TASK-2"),
  apiItem("TASK-9", { source_id: "other", key: "other/TASK-9" } as Partial<ApiItem>),
]);
const all = [epic!, story!, task!, sub!, other!, foreign!];

describe("editing", () => {
  it("sends nothing when nothing changed", () => {
    expect(changedFields(task!, draftOf(task!))).toEqual({});
  });

  it("sends only changed fields, trimmed, with null for cleared optional ones", () => {
    const draft = { ...draftOf(task!), title: "  New title ", summary: "  ", goal: "Goal", dependencies: ["TASK-2", "EPIC-1"] };

    expect(changedFields(task!, draft)).toEqual({ title: "New title", summary: null, goal: "Goal", dependencies: ["TASK-2", "EPIC-1"] });
  });

  it("clears the parent and sends required-for-parent with a new parent", () => {
    expect(changedFields(task!, { ...draftOf(task!), parent: "" })).toEqual({ parent: null });
    expect(changedFields(other!, { ...draftOf(other!), parent: "STORY-1", required_for_parent: "No" })).toEqual({
      parent: "STORY-1",
      required_for_parent: "No",
    });
    expect(changedFields(task!, { ...draftOf(task!), required_for_parent: "No" })).toEqual({ required_for_parent: "No" });
  });

  it("offers parents of the right type from the same backlog, never itself or its descendants", () => {
    expect(parentCandidates(epic!, all)).toEqual([]);
    expect(parentCandidates(story!, all).map((i) => i.id)).toEqual(["EPIC-1"]);
    expect(parentCandidates(task!, all).map((i) => i.id)).toEqual(["EPIC-1", "STORY-1"]);
    expect(parentCandidates(other!, all).map((i) => i.id)).toEqual(["EPIC-1", "STORY-1"]);
  });

  it("offers dependencies from the same backlog except the item itself", () => {
    expect(dependencyCandidates(task!, all).map((i) => i.id)).toEqual(["EPIC-1", "STORY-1", "TASK-3", "TASK-2"]);
  });

  it("after a conflict keeps own edits and takes over what others changed", () => {
    const mine = { ...draftOf(task!), title: "My title" };
    const theirs = { ...task!, goal: "Their goal", title: task!.title, version: "v2" };

    const rebased = rebaseDraft(task!, theirs, mine);

    expect(rebased.title).toBe("My title");
    expect(rebased.goal).toBe("Their goal");
    expect(changedFields(theirs, rebased)).toEqual({ title: "My title" });
  });
});
