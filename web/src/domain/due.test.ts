import { describeNotice, type DueNote, type Notice, groupDueByReason, nextAfterAction, rowActions, rowKey, sortLinkedNotes } from "./due";

function due(label: string, over: Partial<DueNote> = {}): DueNote {
  return {
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
  };
}

describe("groupDueByReason", () => {
  it("returns no groups for an empty list", () => {
    expect(groupDueByReason([])).toEqual([]);
  });

  it("makes one group when all notes are due for the same reason", () => {
    const groups = groupDueByReason([due("NOTE-001"), due("NOTE-002")]);

    expect(groups.map((g) => [g.reason, g.notes.map((n) => n.label)])).toEqual([["trigger", ["NOTE-001", "NOTE-002"]]]);
  });

  it("orders the groups trigger, notice, topic due, review, however the notes come", () => {
    const groups = groupDueByReason([
      due("NOTE-001", { reason: "review_expired" }),
      due("NOTE-002", { reason: "topic_due" }),
      due("NOTE-003", { reason: "notice" }),
      due("NOTE-004", { reason: "trigger" }),
    ]);

    expect(groups.map((g) => g.reason)).toEqual(["trigger", "notice", "topic_due", "review_expired"]);
  });

  it("keeps the order of the notes within a group and leaves out empty groups", () => {
    const groups = groupDueByReason([due("NOTE-003", { reason: "notice" }), due("NOTE-001", { reason: "notice" }), due("NOTE-002", { reason: "notice" })]);

    expect(groups).toHaveLength(1);
    expect(groups[0]?.notes.map((n) => n.label)).toEqual(["NOTE-003", "NOTE-001", "NOTE-002"]);
  });

  it("files a note without a reason under review", () => {
    expect(groupDueByReason([due("NOTE-001", { reason: null })]).map((g) => g.reason)).toEqual(["review_expired"]);
  });

  it("does not change its input", () => {
    const input = [due("NOTE-002", { reason: "notice" }), due("NOTE-001")];
    groupDueByReason(input);
    expect(input.map((n) => n.label)).toEqual(["NOTE-002", "NOTE-001"]);
  });
});

describe("rowActions", () => {
  it("offers snooze, done, drop, promote, keep and open for a due note", () => {
    expect(rowActions(due("NOTE-001"))).toEqual(["snooze", "done", "dropped", "promote", "keep", "open"]);
  });

  it("offers keep, detach, drop and promote for a change notice, and open", () => {
    const notice = due("NOTE-001", { reason: "notice", actions: ["keep", "detach", "drop", "promote"] });

    expect(rowActions(notice)).toEqual(["keep", "detach", "drop", "promote", "open"]);
  });

  it("only offers what the server allows, plus open (and promote for a note that is not a notice)", () => {
    expect(rowActions(due("NOTE-001", { actions: ["keep"] }))).toEqual(["promote", "keep", "open"]);
  });
});

describe("nextAfterAction", () => {
  const keys = ["P/NOTE-001", "P/NOTE-002", "P/NOTE-003"];

  it("moves on to the row that followed", () => {
    expect(nextAfterAction(keys, "P/NOTE-001")).toBe("P/NOTE-002");
    expect(nextAfterAction(keys, "P/NOTE-002")).toBe("P/NOTE-003");
  });

  it("goes back to the previous row after the last one", () => {
    expect(nextAfterAction(keys, "P/NOTE-003")).toBe("P/NOTE-002");
  });

  it("is null when nothing is left or the row is unknown", () => {
    expect(nextAfterAction(["P/NOTE-001"], "P/NOTE-001")).toBeNull();
    expect(nextAfterAction(keys, "P/NOTE-404")).toBeNull();
  });
});

describe("rowKey", () => {
  it("is project and label", () => {
    expect(rowKey({ project: "P", label: "NOTE-001" })).toBe("P/NOTE-001");
  });
});

describe("describeNotice", () => {
  const notice = (cause: string, over: Partial<Notice> = {}): Notice => ({
    id: 1,
    side: "note",
    project: "P",
    label: "NOTE-001",
    cause,
    counterpart: { kind: "item", project: "Q", label: "STORY-001" },
    created_at: "2027-01-01T00:00:00Z",
    decided_at: null,
    decision: null,
    options: [],
    ...over,
  });

  it("names the cause with the other end as project and label", () => {
    expect(describeNotice(notice("item_completed"))).toEqual({ key: "notice.item_completed", params: { other: "Q · STORY-001" } });
    expect(describeNotice(notice("project_unreachable"))).toEqual({ key: "notice.project_unreachable", params: { other: "Q · STORY-001" } });
    expect(describeNotice(notice("note_dropped", { side: "item", counterpart: { kind: "note", project: "P", label: "NOTE-004" } }))).toEqual({
      key: "notice.note_dropped",
      params: { other: "P · NOTE-004" },
    });
  });

  it("falls back to a generic text for a cause it does not know", () => {
    expect(describeNotice(notice("something_new")).key).toBe("notice.unknown");
  });
});

describe("sortLinkedNotes", () => {
  const linked = (label: string, status: string) => ({ project: "P", label, summary: label, status, role: "reference", link_id: 1 });

  it("puts open notes before closed ones and keeps the order otherwise", () => {
    const sorted = sortLinkedNotes([linked("NOTE-001", "done"), linked("NOTE-002", "waiting"), linked("NOTE-003", "promoted"), linked("NOTE-004", "due")]);

    expect(sorted.map((n) => n.label)).toEqual(["NOTE-002", "NOTE-004", "NOTE-001", "NOTE-003"]);
  });

  it("does not change its input", () => {
    const input = [linked("NOTE-001", "done"), linked("NOTE-002", "waiting")];
    sortLinkedNotes(input);
    expect(input.map((n) => n.label)).toEqual(["NOTE-001", "NOTE-002"]);
  });
});
