import type { Item } from "../domain/model";

export interface DocumentLink {
  name: string;
  kind: "notes" | "spec";
  label: string;
}

/** Notes and spec documents of an item, labelled "Notes", "Notes 2", "Spec", ... */
export function documentLinks(item: Item, notesLabel: string, specLabel: string): DocumentLink[] {
  const links = (kind: DocumentLink["kind"], label: string) => {
    const docs = item.documents.filter((d) => d.kind === kind);
    return docs.map((d, n) => ({ name: d.name, kind, label: label + (docs.length > 1 ? ` ${n + 1}` : "") }));
  };
  return [...links("notes", notesLabel), ...links("spec", specLabel)];
}
