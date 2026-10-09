import { useState, type ReactNode } from "react";
import { useI18n } from "../i18n/i18n";
import { Icon } from "./IconButton";

/** A collapsible section of the note detail; the add button sits in the header, so it stays at the top. */
export function NoteSection({ title, action, children }: { title: string; action?: ReactNode; children: ReactNode }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(true);
  return (
    <section className="note-section">
      <div className="note-section-head">
        <button type="button" className="section-toggle" aria-expanded={open} title={t("note.section.toggle")} onClick={() => setOpen(!open)}>
          <Icon name={open ? "caretDown" : "caretRight"} />
          <h3>{title}</h3>
        </button>
        {action && <div className="note-section-actions">{action}</div>}
      </div>
      {open && children}
    </section>
  );
}
