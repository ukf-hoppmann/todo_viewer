// Line comparison of two texts (longest common subsequence): pure, no libraries.

export interface DiffLine {
  /** same: in both texts; removed: only in the left text; added: only in the right one. */
  kind: "same" | "removed" | "added";
  text: string;
}

const lines = (text: string | null): string[] => (text === null || text === "" ? [] : text.replace(/\r\n/g, "\n").split("\n"));

/** The lines of `left` and `right` in order, each marked as shared or as belonging to one side only. */
export function diffLines(left: string | null, right: string | null): DiffLine[] {
  const a = lines(left);
  const b = lines(right);
  // lcs[i][j]: length of the longest common subsequence of a[i..] and b[j..]
  const lcs = Array.from({ length: a.length + 1 }, () => new Array<number>(b.length + 1).fill(0));
  for (let i = a.length - 1; i >= 0; i--) {
    for (let j = b.length - 1; j >= 0; j--) {
      lcs[i]![j] = a[i] === b[j] ? lcs[i + 1]![j + 1]! + 1 : Math.max(lcs[i + 1]![j]!, lcs[i]![j + 1]!);
    }
  }
  const result: DiffLine[] = [];
  let i = 0;
  let j = 0;
  while (i < a.length && j < b.length) {
    if (a[i] === b[j]) {
      result.push({ kind: "same", text: a[i]! });
      i++;
      j++;
    } else if (lcs[i + 1]![j]! >= lcs[i]![j + 1]!) {
      result.push({ kind: "removed", text: a[i++]! });
    } else {
      result.push({ kind: "added", text: b[j++]! });
    }
  }
  while (i < a.length) result.push({ kind: "removed", text: a[i++]! });
  while (j < b.length) result.push({ kind: "added", text: b[j++]! });
  return result;
}
