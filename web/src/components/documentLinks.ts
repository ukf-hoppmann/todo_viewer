import type { Item } from "../domain/model";

export interface DocumentLink {
  path: string;
  label: string;
}

/** Notes and spec files of an item, labelled "Notes", "Notes 2", "Spec", ... */
export function documentLinks(item: Item, notesLabel: string, specLabel: string): DocumentLink[] {
  const links = (paths: string[], label: string) =>
    paths.map((path, n) => ({ path, label: label + (paths.length > 1 ? ` ${n + 1}` : "") }));
  return [...links(item.notes, notesLabel), ...links(item.spec, specLabel)];
}
