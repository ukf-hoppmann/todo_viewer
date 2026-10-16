import { useState } from "react";
import {
  fetchNoteDocument,
  useAppendNoteEntry,
  useNoteDocument,
  useNoteDocumentList,
  useWriteNoteDocument,
} from "../api/queries";
import { useI18n } from "../i18n/i18n";
import { type DocumentBackend, DocumentDialog, type DocumentMode } from "./DocumentDialog";
import { documentLinks } from "./documentLinks";
import { IconButton } from "./IconButton";
import { NoteSection } from "./NoteSection";

interface NoteDocumentsProps {
  project: string;
  label: string;
  summary: string;
  /** Closed or deleted notes can be read but not written. */
  readOnly: boolean;
}

/** The documents of a note read and written like those of a backlog item: the same dialog on other routes. */
function noteBackend(project: string, label: string, summary: string, documents: DocumentBackend["documents"]): DocumentBackend {
  return {
    id: label,
    title: summary,
    documents,
    hasSummary: true,
    useRead: (name) => useNoteDocument(project, label, name),
    useWrite: () => {
      const write = useWriteNoteDocument();
      return {
        mutate: (args, options) => write.mutate({ project, label, ...args }, options),
        isPending: write.isPending,
        error: write.error,
        reset: write.reset,
      };
    },
    useAppend: () => {
      const append = useAppendNoteEntry();
      return {
        mutate: (body, options) => append.mutate({ project, label, body }, options),
        isPending: append.isPending,
        error: append.error,
      };
    },
    fetch: (name) => fetchNoteDocument(project, label, name),
  };
}

/** Lists the notes and specs of a note; a click opens the shared document dialog. */
export function NoteDocuments({ project, label, summary, readOnly }: NoteDocumentsProps) {
  const { t } = useI18n();
  const list = useNoteDocumentList(project, label);
  const [open, setOpen] = useState<{ name: string | null; mode: DocumentMode } | null>(null);
  const documents = list.data ?? [];
  const links = documentLinks({ documents }, t("doc.notes"), t("doc.spec"));

  return (
    <NoteSection
      title={t("note.docs.title")}
      action={
        !readOnly && (
          <>
            <IconButton icon="note" label={t("doc.addNote")} onClick={() => setOpen({ name: null, mode: "note" })} />
            <IconButton icon="spec" label={t("doc.addSpec")} onClick={() => setOpen({ name: null, mode: "newSpec" })} />
          </>
        )
      }
    >
      {links.length === 0 && <div className="hint">{t("note.docs.none")}</div>}
      <div className="note-docs">
        {links.map((link) => (
          <button key={link.name} className="btn small" title={link.name} onClick={() => setOpen({ name: link.name, mode: "view" })}>
            {link.label}
          </button>
        ))}
      </div>
      {open && (
        <DocumentDialog
          backend={noteBackend(project, label, summary, documents)}
          initialName={open.name}
          initialMode={open.mode}
          onClose={() => setOpen(null)}
        />
      )}
    </NoteSection>
  );
}
