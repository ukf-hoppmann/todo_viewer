import { useState } from "react";
import { changedFields, type ConflictChoice, type ConflictChoices, choiceOf, conflictKey, type SyncConflict } from "../domain/sync";
import { diffLines } from "../domain/diff";
import { useI18n } from "../i18n/i18n";

const CHOICES: readonly ConflictChoice[] = ["defer", "database", "markdown"];
const isLong = (value: string | null) => value !== null && (value.includes("\n") || value.length > 60);

interface Props {
  conflicts: readonly SyncConflict[];
  choices: ConflictChoices;
  onChoose: (conflict: SyncConflict, choice: ConflictChoice) => void;
}

/** The conflicts of a preview: both versions side by side, one decision each (deferring is preselected). */
export function SyncConflicts({ conflicts, choices, onChoose }: Props) {
  const { t } = useI18n();
  return (
    <div className="sync-conflicts" role="group" aria-label={t("sync.conflicts.title")}>
      <h4>⚠ {t("sync.conflicts.title")}</h4>
      <p>{t("sync.conflicts.hint")}</p>
      <ul>
        {conflicts.map((c) => (
          <ConflictRow key={conflictKey(c)} conflict={c} choice={choiceOf(choices, c)} onChoose={(choice) => onChoose(c, choice)} />
        ))}
      </ul>
    </div>
  );
}

function ConflictRow({ conflict, choice, onChoose }: { conflict: SyncConflict; choice: ConflictChoice; onChoose: (c: ConflictChoice) => void }) {
  const { t } = useI18n();
  const [open, setOpen] = useState(false);
  const key = conflictKey(conflict);
  const name = conflict.name ? `${conflict.label} / ${conflict.name}` : `${conflict.label} — ${conflict.title}`;
  return (
    <li className="sync-conflict">
      <div className="sync-conflict-head">
        <strong>{name}</strong> <span className="hint">({t(`sync.conflict.${conflict.reason}`)})</span>
      </div>
      <div className="backend-choice" role="radiogroup" aria-label={t("sync.decide", { n: name })}>
        {CHOICES.map((c) => (
          <label key={c}>
            <input type="radio" name={`decide-${key}`} checked={choice === c} onChange={() => onChoose(c)} />
            {t(`sync.choice.${c}`)}
          </label>
        ))}
      </div>
      <button type="button" className="btn small" aria-expanded={open} onClick={() => setOpen(!open)}>
        {t(open ? "sync.compare.hide" : "sync.compare.show")}
      </button>
      {open && <ConflictDiff conflict={conflict} />}
    </li>
  );
}

/** Item: the fields that differ, side by side (long values as a line comparison); document: line comparison. */
function ConflictDiff({ conflict }: { conflict: SyncConflict }) {
  const { t } = useI18n();
  const missing = <em>{t("sync.compare.missing")}</em>;
  if (conflict.kind === "document" || conflict.kind === "note_document") {
    const lines = diffLines(conflict.database?.text ?? null, conflict.markdown?.text ?? null);
    return (
      <div className="sync-diff">
        <div className="hint">{t("sync.compare.legend")}</div>
        {!conflict.database && missing}
        {!conflict.markdown && missing}
        <pre className="diff-lines">
          {lines.map((l, n) => (
            <span key={n} className={`diff-${l.kind}`}>{`${l.kind === "removed" ? "− " : l.kind === "added" ? "+ " : "  "}${l.text}\n`}</span>
          ))}
        </pre>
      </div>
    );
  }
  return (
    <table className="sync-diff">
      <thead>
        <tr>
          <th scope="col">{t("sync.compare.field")}</th>
          <th scope="col">{t("sync.compare.database")}</th>
          <th scope="col">{t("sync.compare.markdown")}</th>
        </tr>
      </thead>
      <tbody>
        {!conflict.database && (
          <tr><td colSpan={3}>{t("sync.compare.sideMissing", { s: t("sync.compare.database") })}</td></tr>
        )}
        {!conflict.markdown && (
          <tr><td colSpan={3}>{t("sync.compare.sideMissing", { s: t("sync.compare.markdown") })}</td></tr>
        )}
        {changedFields(conflict).map((f) => (
          <tr key={f.name}>
            <th scope="row">{f.name}</th>
            {isLong(f.database) || isLong(f.markdown) ? (
              <td colSpan={2}>
                <pre className="diff-lines">
                  {diffLines(f.database, f.markdown).map((l, n) => (
                    <span key={n} className={`diff-${l.kind}`}>{`${l.kind === "removed" ? "− " : l.kind === "added" ? "+ " : "  "}${l.text}\n`}</span>
                  ))}
                </pre>
              </td>
            ) : (
              <>
                <td className="diff-removed">{f.database === null ? missing : f.database || "—"}</td>
                <td className="diff-added">{f.markdown === null ? missing : f.markdown || "—"}</td>
              </>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
