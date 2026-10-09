import type { MessageKey } from "../i18n/messages";
import { formatDate, type IndexNote, type NoteGroup } from "../domain/notes";
import { useI18n } from "../i18n/i18n";
import type { NoteRef } from "../state/uiState";

interface NoteListProps {
  notes: readonly IndexNote[];
  /** Notes grouped by topic; when set, the list shows the groups instead of one flat list. */
  groups?: readonly NoteGroup[] | null;
  selected: NoteRef | null;
  /** Show the project in each row (notes of several projects). */
  showProject: boolean;
  onSelect: (note: NoteRef) => void;
}

const REASONS = ["trigger", "notice", "topic_due", "review_expired"];

/** The notes of the chosen topic: summary, status badge, due reason and review date. */
export function NoteList({ notes, groups, selected, showProject, onSelect }: NoteListProps) {
  const { t, lang } = useI18n();
  if (notes.length === 0) return <div className="hint note-empty">{t("notes.empty")}</div>;

  const row = (note: IndexNote) => {
    const isSelected = selected?.project === note.project && selected.label === note.label;
    const reason = note.reason && REASONS.includes(note.reason) ? t(`note.reason.${note.reason}` as MessageKey) : null;
    return (
      <li key={`${note.project}/${note.label}`}>
        <button className={`note-row${isSelected ? " selected" : ""}`} aria-pressed={isSelected} onClick={() => onSelect({ project: note.project, label: note.label })}>
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
  };

  if (!groups) return <ul className="note-list">{notes.map(row)}</ul>;
  return (
    <div className="note-groups">
      {groups.map((group) => (
        <section key={group.key} className="note-group">
          <h4 className="note-group-head" style={{ paddingLeft: Math.max(group.path.length - 1, 0) * 14 }}>
            <span className="note-group-path">{group.path.length > 0 ? group.path.join(" › ") : t("notes.noTopic")}</span>
            <span className="topic-count">{group.notes.length}</span>
          </h4>
          <ul className="note-list">{group.notes.map(row)}</ul>
        </section>
      ))}
    </div>
  );
}
