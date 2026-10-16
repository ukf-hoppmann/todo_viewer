import { useState } from "react";
import { changedFields, type ConflictChoice, type ConflictChoices, choiceOf, conflictKey, conflictSummary, decidedCount, isBulkDecidable, type SyncConflict } from "../domain/sync";
import { diffLines } from "../domain/diff";
import { useI18n } from "../i18n/i18n";

const CHOICES: readonly ConflictChoice[] = ["defer", "database", "markdown"];
const isLong = (value: string | null) => value !== null && (value.includes("\n") || value.length > 60);

interface Props {
  conflicts: readonly SyncConflict[];
  choices: ConflictChoices;
  onChoose: (conflict: SyncConflict, choice: ConflictChoice) => void;
  /** One decision for every conflict a bulk decision covers (not the deletions). */
  onChooseAll: (choice: ConflictChoice) => void;
}

const BULK: readonly ConflictChoice[] = ["database", "markdown", "defer"];

/**
 * The conflicts of a preview: one compact row each, with what differs in one line and a decision of its own
 * (deferring is preselected). Above the rows, the same decision can be given to all changes on both sides at once; every
 * row can still be changed afterwards. Deletions are decided one by one only.
 */
export function SyncConflicts({ conflicts, choices, onChoose, onChooseAll }: Props) {
  const { t } = useI18n();
  const bulk = conflicts.filter(isBulkDecidable).length;
  return (
    <div className="sync-conflicts" role="group" aria-label={t("sync.conflicts.title")}>
      <div className="sync-conflicts-head">
        <h4>
          ⚠ {t("sync.conflicts.title")} <span className="sync-conflicts-count">{t("sync.conflicts.count", { n: conflicts.length, d: decidedCount(conflicts, choices) })}</span>
        </h4>
        <p className="hint">{t("sync.conflicts.hint")} {t("sync.conflicts.legend")}</p>
        {bulk > 1 && (
          <div className="sync-bulk" role="group" aria-label={t("sync.bulk.label", { n: bulk })}>
            <span>{t("sync.bulk.label", { n: bulk })}</span>
            {BULK.map((choice) => (
              <button key={choice} type="button" className="btn small" onClick={() => onChooseAll(choice)}>
                {t(`sync.bulk.${choice}`)}
              </button>
            ))}
            {bulk < conflicts.length && <span className="hint">{t("sync.bulk.note")}</span>}
          </div>
        )}
      </div>
      <ul>
        {conflicts.map((c) => (
          <ConflictRow key={conflictKey(c)} conflict={c} choice={choiceOf(choices, c)} onChoose={(choice) => onChoose(c, choice)} />
        ))}
      </ul>
    </div>
  );
}

/** One line: the fields that differ (database red, file green), or that a text differs, or which side lacks the entry. */
function Summary({ conflict }: { conflict: SyncConflict }) {
  const { t } = useI18n();
  const summary = conflictSummary(conflict);
  if (summary.kind === "missing") return <div className="sync-summary">{t("sync.compare.sideMissing", { s: t(`sync.compare.${summary.side}`) })}</div>;
  if (summary.kind === "text") return <div className="sync-summary">{t("sync.summary.text")}</div>;
  const shown = (value: string | null) => (value === null ? t("sync.compare.missing") : value || "—");
  return (
    <div className="sync-summary">
      {summary.fields.map((f) => (
        <span key={f.name} className="sync-field">
          <b>{f.name}</b> <span className="diff-removed" title={f.database ?? undefined}>{shown(f.database)}</span> → <span className="diff-added" title={f.markdown ?? undefined}>{shown(f.markdown)}</span>
        </span>
      ))}
      {summary.more > 0 && <span>{t("sync.summary.more", { n: summary.more })}</span>}
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
      <div className="sync-conflict-main">
        <div className="sync-conflict-head">
          <strong>{name}</strong> <span className="hint">({t(`sync.conflict.${conflict.reason}`)})</span>
        </div>
        <Summary conflict={conflict} />
        <button type="button" className="btn link" aria-expanded={open} onClick={() => setOpen(!open)}>
          {t(open ? "sync.compare.hide" : "sync.compare.show")}
        </button>
      </div>
      <div className="backend-choice sync-choice" role="radiogroup" aria-label={t("sync.decide", { n: name })}>
        {CHOICES.map((c) => (
          <label key={c}>
            <input type="radio" name={`decide-${key}`} checked={choice === c} onChange={() => onChoose(c)} />
            {t(`sync.choice.${c}`)}
          </label>
        ))}
      </div>
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
