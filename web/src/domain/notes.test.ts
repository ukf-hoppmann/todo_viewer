import { alreadyMet, badgeLabel, buildTopicTree, describeTrigger, formatDate, snoozePresets, tabTitle, toIsoWithZone, notesOfTopic, sortNotes, topicPath, type IndexNote, type IndexTopic } from "./notes";

function topic(label: string, over: Partial<IndexTopic> = {}): IndexTopic {
  return { project: "P", label, name: `Name ${label}`, parent: null, path: [], due_at: null, due: false, note_count: 0, ...over };
}

function note(label: string, over: Partial<IndexNote> = {}): IndexNote {
  return { project: "P", label, summary: `Summary ${label}`, status: "waiting", reason: null, review_at: null, topic: null, archived: false, ...over };
}

const TOPICS = [
  topic("TOPIC-003", { parent: "TOPIC-002", name: "Deep" }),
  topic("TOPIC-001", { name: "Root" }),
  topic("TOPIC-002", { parent: "TOPIC-001", name: "Mid" }),
  topic("TOPIC-004", { name: "Another root" }),
];

describe("buildTopicTree", () => {
  it("nests topics three levels deep and sorts siblings by name", () => {
    const tree = buildTopicTree(TOPICS);

    expect(tree.map((n) => n.topic.label)).toEqual(["TOPIC-004", "TOPIC-001"]);
    const mid = tree[1]?.children[0];
    expect(tree[1]?.children.map((n) => n.topic.label)).toEqual(["TOPIC-002"]);
    expect(mid?.children.map((n) => n.topic.label)).toEqual(["TOPIC-003"]);
    expect(mid?.children[0]?.children).toEqual([]);
  });

  it("keeps topics of different projects apart even if their labels are equal", () => {
    const tree = buildTopicTree([topic("TOPIC-001", { project: "A" }), topic("TOPIC-001", { project: "B" }), topic("TOPIC-002", { project: "B", parent: "TOPIC-001" })]);

    expect(tree.map((n) => [n.topic.project, n.children.length])).toEqual([["A", 0], ["B", 1]]);
  });

  it("shows an orphan (parent missing) as a root instead of losing it", () => {
    const tree = buildTopicTree([topic("TOPIC-009", { parent: "TOPIC-404" })]);

    expect(tree.map((n) => n.topic.label)).toEqual(["TOPIC-009"]);
  });

  it("returns an empty list without topics", () => {
    expect(buildTopicTree([])).toEqual([]);
  });
});

describe("topicPath", () => {
  it("runs from the root down to the topic", () => {
    expect(topicPath(TOPICS, "P", "TOPIC-003")).toEqual(["Root", "Mid", "Deep"]);
  });

  it("is empty for an unknown topic and ends at a cycle", () => {
    expect(topicPath(TOPICS, "P", "TOPIC-404")).toEqual([]);
    const cyclic = [topic("TOPIC-001", { parent: "TOPIC-002", name: "a" }), topic("TOPIC-002", { parent: "TOPIC-001", name: "b" })];
    expect(topicPath(cyclic, "P", "TOPIC-001").length).toBeLessThanOrEqual(2);
  });
});

describe("notesOfTopic", () => {
  const notes = [
    note("NOTE-001", { topic: "TOPIC-001" }),
    note("NOTE-002", { topic: "TOPIC-002" }),
    note("NOTE-003", { topic: "TOPIC-003" }),
    note("NOTE-004"),
    note("NOTE-001", { project: "Q", topic: "TOPIC-001" }),
  ];

  it("keeps the notes of the topic only", () => {
    expect(notesOfTopic(notes, TOPICS, "P", "TOPIC-002", false).map((n) => n.label)).toEqual(["NOTE-002"]);
  });

  it("includes the notes of all sub-topics on request", () => {
    expect(notesOfTopic(notes, TOPICS, "P", "TOPIC-001", true).map((n) => n.label)).toEqual(["NOTE-001", "NOTE-002", "NOTE-003"]);
  });

  it("returns every note without a topic selection, and only those of the project when one is given", () => {
    expect(notesOfTopic(notes, TOPICS, null, null, true)).toHaveLength(5);
    expect(notesOfTopic(notes, TOPICS, "P", null, true).map((n) => n.label)).toEqual(["NOTE-001", "NOTE-002", "NOTE-003", "NOTE-004"]);
  });
});

describe("sortNotes", () => {
  it("puts due notes first, then orders by review date, notes without a date last, then by label", () => {
    const sorted = sortNotes([
      note("NOTE-005", { review_at: null }),
      note("NOTE-004", { review_at: "2027-01-02T00:00:00Z" }),
      note("NOTE-003", { status: "due", review_at: "2027-03-01T00:00:00Z" }),
      note("NOTE-002", { review_at: "2027-01-01T00:00:00Z" }),
      note("NOTE-001", { status: "due", review_at: "2027-02-01T00:00:00Z" }),
    ]);

    expect(sorted.map((n) => n.label)).toEqual(["NOTE-001", "NOTE-003", "NOTE-002", "NOTE-004", "NOTE-005"]);
  });

  it("does not change its input", () => {
    const input = [note("NOTE-002"), note("NOTE-001")];
    sortNotes(input);
    expect(input.map((n) => n.label)).toEqual(["NOTE-002", "NOTE-001"]);
  });
});

describe("formatDate", () => {
  it("is empty without a moment and shows the year otherwise", () => {
    expect(formatDate(null, "de")).toBe("");
    expect(formatDate("2027-06-15T12:00:00Z", "en")).toContain("2027");
  });
});

describe("snoozePresets", () => {
  const at = (date: Date) => [date.getFullYear(), date.getMonth() + 1, date.getDate(), date.getHours(), date.getMinutes()];

  it("offers tomorrow, in a week and in 30 days, each at 08:00 local time", () => {
    const presets = snoozePresets(new Date(2027, 5, 10, 15, 30));

    expect(presets.map((p) => p.key)).toEqual(["tomorrow", "week", "month"]);
    expect(presets.map((p) => at(p.at))).toEqual([
      [2027, 6, 11, 8, 0],
      [2027, 6, 17, 8, 0],
      [2027, 7, 10, 8, 0],
    ]);
  });

  it("rolls over the end of a month and a year", () => {
    expect(snoozePresets(new Date(2027, 11, 31, 23, 0)).map((p) => at(p.at))).toEqual([
      [2028, 1, 1, 8, 0],
      [2028, 1, 7, 8, 0],
      [2028, 1, 30, 8, 0],
    ]);
    expect(snoozePresets(new Date(2028, 1, 28, 9, 0))[0]?.at.getDate()).toBe(29); // leap year
  });

  it("keeps 08:00 local time over a change of daylight saving time", () => {
    // Whatever zone the tests run in: the clock time stays 08:00 on every day.
    for (const start of [new Date(2027, 2, 26, 12, 0), new Date(2027, 9, 29, 12, 0)]) {
      for (const preset of snoozePresets(start)) expect(preset.at.getHours()).toBe(8);
    }
  });
});

describe("toIsoWithZone", () => {
  it("reads a local date and time and returns the moment as UTC", () => {
    expect(toIsoWithZone("2027-06-10T08:00")).toBe(new Date(2027, 5, 10, 8, 0).toISOString());
  });

  it("is null for an empty or broken value", () => {
    expect(toIsoWithZone("")).toBeNull();
    expect(toIsoWithZone("not a date")).toBeNull();
  });
});

describe("alreadyMet", () => {
  it("is true when the item has the target status already", () => {
    expect(alreadyMet({ status: "Completed" }, "Completed")).toBe(true);
    expect(alreadyMet({ status: "Open" }, "Completed")).toBe(false);
    expect(alreadyMet(undefined, "Completed")).toBe(false);
  });
});

describe("describeTrigger", () => {
  const base = { id: 1, kind: "time", at: null, fired_at: null, already_met: false, target: null, target_project: null, target_display: null, target_status: null, reachable: null, unreachable_reason: null };

  it("names a time trigger with its moment and whether it fired", () => {
    const open = describeTrigger({ ...base, at: "2027-06-15T12:00:00Z" }, "en");
    expect(open.key).toBe("trigger.time");
    expect(open.params.at).toContain("2027");
    expect(open.fired).toBe(false);
    expect(describeTrigger({ ...base, at: "2027-06-15T12:00:00Z", fired_at: "2027-06-15T12:00:00Z" }, "en").fired).toBe(true);
  });

  it("names an event trigger with its target and status, and marks an already met one", () => {
    const text = describeTrigger({ ...base, kind: "event", target: "STORY-001", target_display: "P · STORY-001", target_status: "Completed", already_met: true }, "de");
    expect(text).toEqual({ key: "trigger.event", params: { target: "P · STORY-001", status: "Completed" }, fired: false, alreadyMet: true });
  });

  it("names a topic due trigger", () => {
    expect(describeTrigger({ ...base, kind: "topic_due" }, "de").key).toBe("trigger.topicDue");
  });
});

describe("tabTitle", () => {
  it("puts the number of due notes in front of the title, and nothing at zero", () => {
    expect(tabTitle("ToDo Viewer", 0)).toBe("ToDo Viewer");
    expect(tabTitle("ToDo Viewer", 1)).toBe("(1) ToDo Viewer");
    expect(tabTitle("ToDo Viewer", 99)).toBe("(99) ToDo Viewer");
    expect(tabTitle("ToDo Viewer", 100)).toBe("(99+) ToDo Viewer");
  });
});

describe("badgeLabel", () => {
  it("shows the number up to 99 and 99+ above", () => {
    expect(badgeLabel(1)).toBe("1");
    expect(badgeLabel(99)).toBe("99");
    expect(badgeLabel(100)).toBe("99+");
    expect(badgeLabel(2500)).toBe("99+");
  });
});
