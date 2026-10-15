import { diffLines } from "./diff";

describe("diffLines", () => {
  it("marks lines both texts share as same and the rest as removed (left only) or added (right only)", () => {
    expect(diffLines("a\nb\nc", "a\nB\nc")).toEqual([
      { kind: "same", text: "a" },
      { kind: "removed", text: "b" },
      { kind: "added", text: "B" },
      { kind: "same", text: "c" },
    ]);
  });

  it("keeps inserted and deleted lines in their place", () => {
    expect(diffLines("a\nc", "a\nb\nc").map((l) => l.kind)).toEqual(["same", "added", "same"]);
    expect(diffLines("a\nb\nc", "a\nc").map((l) => l.kind)).toEqual(["same", "removed", "same"]);
  });

  it("treats a missing side as no lines", () => {
    expect(diffLines(null, "x\ny")).toEqual([{ kind: "added", text: "x" }, { kind: "added", text: "y" }]);
    expect(diffLines("x", null)).toEqual([{ kind: "removed", text: "x" }]);
    expect(diffLines(null, null)).toEqual([]);
  });

  it("gives all same lines for equal texts, with Windows line ends ignored", () => {
    expect(diffLines("a\r\nb", "a\nb").every((l) => l.kind === "same")).toBe(true);
  });

  it("handles texts without any common line", () => {
    expect(diffLines("a", "b").map((l) => l.kind)).toEqual(["removed", "added"]);
  });
});
