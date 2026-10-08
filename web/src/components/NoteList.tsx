import type { MessageKey } from "../i18n/messages";
import { formatDate, type IndexNote } from "../domain/notes";
import { useI18n } from "../i18n/i18n";
import type { NoteRef } from "../state/uiState";

interface NoteListProps {
  notes: readonly IndexNote[];
  selected: NoteRef | null;
  /** Show the project in each row (notes of several projects). */
  showProject: boolean;
  onSelect: (note: NoteRef) => void;
}

const REASONS = ["trigger", "notice", "topic_due", "review_expired"];

/** The notes of the chosen topic: summary, status badge, due reason and review date. */
export function NoteList({ notes, selected, showProject, onSelect }: NoteListProps) {
  const { t, lang } = useI18n();
  if (notes.length === 0) return <div className="hint note-empty">{t("notes.empty")}</div>;
  return (
    <ul className="note-list">
      {notes.map((note) => {
        const isSelected = selected?.project === note.project && selected.label === note.label;
        const reason = note.reason && REASONS.includes(note.reason) ? t(`note.reason.${note.reason}` as MessageKey) : null;
        return (
          <li key={`${note.project}/${note.label}`}>
            <button
              className={`note-row${isSelected ? " selected" : ""}`}
              aria-pressed={isSelected}
              onClick={() => onSelect({ project: note.project, label: note.label })}
            >
              <span className="note-summary">{note.summary}</span>
              <span className="note-meta">
                <span className={`badge note-${note.status}`}>{t(`note.status.${note.status}` as MessageKey)}</span>
                {reason && <span className="note-reason">{reason}</span>}
                {note.review_at && <span className="note-review">{t("notes.review", { d: formatDate(note.review_at, lang) })}</span>}
                <span className="note-label">{showProject ? `${note.project} · ${note.label}` : note.label}</span>
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
