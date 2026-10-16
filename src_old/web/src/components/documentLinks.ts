export interface DocumentRef {
  name: string;
  kind: "notes" | "spec";
}

export interface DocumentLink {
  name: string;
  kind: "notes" | "spec";
  label: string;
}

/** Notes and spec documents of an item or a note, labelled "Notes", "Notes 2", "Spec", ... */
export function documentLinks(source: { documents: readonly DocumentRef[] }, notesLabel: string, specLabel: string): DocumentLink[] {
  const links = (kind: DocumentLink["kind"], label: string) => {
    const docs = source.documents.filter((d) => d.kind === kind);
    return docs.map((d, n) => ({ name: d.name, kind, label: label + (docs.length > 1 ? ` ${n + 1}` : "") }));
  };
  return [...links("notes", notesLabel), ...links("spec", specLabel)];
}
