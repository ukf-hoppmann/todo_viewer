import { describeProject, type ProjectSource } from "./projects";
import type { SyncState } from "./sync";

const database = (over: Partial<ProjectSource> = {}): ProjectSource => ({ primary: "database", mirror: "markdown", markdown_path: "/repos/central", auto_sync: false, ...over });
const markdown = (over: Partial<ProjectSource> = {}): ProjectSource => ({ primary: "markdown", mirror: "none", markdown_path: "/repos/a/docs", auto_sync: false, ...over });
const status = (state: SyncState, conflicts = 0) => ({ state, conflicts });

describe("describeProject: what the card says about a project", () => {
  it("is loading until the state is known, and then offers the sync of a mirrored project", () => {
    const view = describeProject(database(), undefined);

    expect(view.status).toBe("loading");
    expect(view.tone).toBe("loading");
    expect(view.action).toBe("sync");
  });

  it.each([
    ["in_sync", "ok"],
    ["mirror_changed", "attention"],
    ["both_changed", "attention"],
    ["unreadable", "attention"],
    ["conflicts", "attention"],
    ["primary_changed", "pending"],
    ["unknown", "pending"],
  ] as const)("shows state %s with the tone %s", (state, tone) => {
    const view = describeProject(database(), status(state));

    expect(view.status).toBe(state);
    expect(view.tone).toBe(tone);
    expect(view.action).toBe("sync");
  });

  it("puts open conflicts first, whatever the state says, and offers to decide them", () => {
    const view = describeProject(database(), status("in_sync", 15));

    expect(view.status).toBe("conflicts");
    expect(view.tone).toBe("attention");
    expect(view.conflicts).toBe(15);
    expect(view.action).toBe("resolve");
  });

  it("does not show a project without a mirror as a problem", () => {
    const view = describeProject(markdown(), status("none"));

    expect(view.hasMirror).toBe(false);
    expect(view.status).toBe("none");
    expect(view.tone).toBe("idle");
  });
});

describe("describeProject: the one action that fits", () => {
  it("lets a markdown project without a mirror start a database mirror", () => {
    expect(describeProject(markdown(), status("none")).action).toBe("enableMirror");
  });

  it("lets a database project switch its markdown mirror on again, because the folder is still there", () => {
    const view = describeProject(database({ mirror: "none" }), status("none"));

    expect(view.action).toBe("enableMirror");
    expect(view.mirrorOff).toBe(true);
  });

  it("asks a database project without a markdown folder for the folder first", () => {
    const view = describeProject(database({ mirror: "none", markdown_path: null }), status("none"));

    expect(view.action).toBe("setupMirror");
    expect(view.mirrorOff).toBe(false);
  });

  it("has nothing to sync without a mirror, even while the state is still loading", () => {
    expect(describeProject(markdown(), undefined).action).toBe("enableMirror");
  });

  it("offers the sync of a markdown project with a database mirror", () => {
    const view = describeProject(markdown({ mirror: "database" }), status("in_sync"));

    expect(view.hasMirror).toBe(true);
    expect(view.action).toBe("sync");
  });
});

describe("describeProject: switching the primary source", () => {
  it("is possible for a markdown project, which can always go to the database", () => {
    expect(describeProject(markdown(), status("none")).switchBlocked).toBe(false);
  });

  it("is possible for a database project that has a markdown folder, mirrored or not", () => {
    expect(describeProject(database(), status("in_sync")).switchBlocked).toBe(false);
    expect(describeProject(database({ mirror: "none" }), status("none")).switchBlocked).toBe(false);
  });

  it("is blocked for a database project that has no markdown folder to go to", () => {
    expect(describeProject(database({ mirror: "none", markdown_path: null }), status("none")).switchBlocked).toBe(true);
  });
});

describe("describeProject: the automatic sync", () => {
  it("can be switched on only with a mirror, and stays switchable once it is on", () => {
    expect(describeProject(database(), status("in_sync")).autoSwitchable).toBe(true);
    expect(describeProject(markdown(), status("none")).autoSwitchable).toBe(false);
    expect(describeProject(markdown({ auto_sync: true }), status("none")).autoSwitchable).toBe(true);
  });

  it("is on without effect when the mirror is gone", () => {
    expect(describeProject(markdown({ auto_sync: true }), status("none")).autoIdle).toBe(true);
    expect(describeProject(database({ auto_sync: true }), status("in_sync")).autoIdle).toBe(false);
    expect(describeProject(markdown(), status("none")).autoIdle).toBe(false);
  });
});
