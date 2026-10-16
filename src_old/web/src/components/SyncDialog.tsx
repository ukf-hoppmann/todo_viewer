import { useEffect, useRef, useState } from "react";
import type { SourceStatus } from "../api/client";
import { useSwitchBackend, useSyncSource } from "../api/queries";
import { buildResolutions, canRun, changeCount, visibleKinds, type ConflictChoice, type ConflictChoices, conflictKey, decideMany, directionOf, isInSync, summarizePreview, type SyncMode, type SyncPreview, switchDirection } from "../domain/sync";
import { ApiError } from "../api/client";
import { describeError, type I18n, useI18n } from "../i18n/i18n";
import { scopeOf } from "../state/uiState";
import { useUiState } from "../state/useUiStateStore";
import { Modal } from "./Modal";
import { SyncConflicts } from "./SyncConflicts";

interface SyncDialogProps {
  /** A database project (sync, switch to markdown) or a markdown project (switch to the database). */
  source: SourceStatus;
  mode: SyncMode;
  /** "resolve" opens the same dialog from the conflicts of a project; only the title differs. */
  intent?: "sync" | "resolve";
  onClose: () => void;
  /** The project now lives on the other backend. */
  onSwitched: (project: string) => void;
}

type Entry = Pick<SyncPreview["items"]["created"][number], "label" | "name" | "title">;
const FORMAT_REASON = "note_format";
const entryText = (e: Entry) => (e.name ? `${e.label} / ${e.name}` : `${e.label} — ${e.title}`);
/** Which side the entry comes from: the arrow points to where it goes. */
const origin = (e: { origin: "database" | "markdown" | null }) => (e.origin === "database" ? " →" : e.origin === "markdown" ? " ←" : "");

/** Like describeError, but names why a folder could not be synced. */
function syncError(i18n: I18n, error: unknown): string {
  if (error instanceof ApiError && error.code === "sync_source_invalid") {
    const reason = i18n.errorText(error.details.reason, error.details.reason ?? "");
    // A notes file that does not follow the format: the server names the file and the line.
    const where = error.details.reason === FORMAT_REASON ? ` (${error.message.replace(/^Nothing was changed: /, "")})` : "";
    return `${i18n.errorText(error.code, error.message)}: ${reason}${where}`;
  }
  return describeError(i18n, error);
}

/**
 * A sync of a database project with its markdown folder, or the move of a project to the other backend. A sync opens
 * with its preview already loaded (it only reads), conflicts first; switching keeps its own preview step. The direction
 * of a sync is the project's setting (Settings → Projects).
 */
export function SyncDialog({ source, mode, intent = "sync", onClose, onSwitched }: SyncDialogProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const ui = useUiState();
  const sync = useSyncSource();
  const move = useSwitchBackend();
  const switching = mode === "switch";
  const folder = source.backend === "database" ? (source.sync_path ?? "") : source.path;
  const scope = scopeOf(ui.state, source.id);
  const direction = switching ? switchDirection(source.backend) : directionOf(scope);
  const [choices, setChoices] = useState<ConflictChoices>({});

  const preview: SyncPreview | null = sync.data && !sync.data.executed ? sync.data : null;
  const result: SyncPreview | null = sync.data?.executed ? sync.data : null;
  const busy = sync.isPending || move.isPending;
  const error = sync.error ?? move.error;
  const request = { sourceId: source.id, direction, language: i18n.lang };
  const loadPreview = () => sync.mutate({ ...request, confirm: false });

  // The preview only reads both sides, so a sync shows it as soon as the dialog opens, once.
  const started = useRef(false);
  useEffect(() => {
    if (switching || started.current) return;
    started.current = true;
    sync.mutate({ sourceId: source.id, direction: directionOf(scope), language: i18n.lang, confirm: false });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const run = () => {
    if (!preview) return;
    const confirmed = { ...request, token: preview.token, resolutions: switching ? [] : buildResolutions(preview.conflicts, choices) };
    if (switching) {
      move.mutate({ ...confirmed, backend: source.backend === "markdown" ? "database" : "markdown" }, { onSuccess: (saved) => onSwitched(saved.project) });
    } else {
      sync.mutate({ ...confirmed, confirm: true });
    }
  };

  const title = switching
    ? t(source.backend === "markdown" ? "sync.switch.toDb.title" : "sync.switch.toMd.title", { p: source.project })
    : t(intent === "resolve" ? "sync.resolve.title" : "sync.title", { p: source.project });
  const runLabel = switching ? "sync.runSwitch" : preview && preview.conflicts.length > 0 ? "sync.runDecisions" : "sync.run";

  return (
    <Modal labelledBy="sync-title" onDismiss={onClose} className="sync-dialog">
      <h3 id="sync-title">{title}</h3>
      {switching ? (
        <>
          <p>{t(source.backend === "markdown" ? "sync.switch.toDb.hint" : "sync.switch.toMd.hint", { f: folder })}</p>
          <p className="hint">{t("sync.switch.backupHint")}</p>
        </>
      ) : (
        <>
          <p>{t("sync.folder", { f: folder })}</p>
          {scope !== "both" && <p className="hint">{t("sync.direction.restricted", { d: t(`sync.dir.${scope}`) })}</p>}
        </>
      )}

      {!switching && busy && !preview && !result && <p className="hint" role="status">{t("sync.loading")}</p>}
      {preview && (
        <PreviewView
          preview={preview}
          switching={switching}
          choices={choices}
          onChoose={(c, choice) => setChoices({ ...choices, [conflictKey(c)]: choice })}
          onChooseAll={(choice) => setChoices(decideMany(preview.conflicts, choices, choice))}
        />
      )}
      {result && <ResultView result={result} />}
      {error && (
        <div className="field-error" role="alert">
          {syncError(i18n, error)}
        </div>
      )}

      <div className="modal-actions">
        <button className="btn" onClick={onClose}>
          {result ? t("close") : t("cancel")}
        </button>
        {!result && (
          <button className="btn" disabled={busy} onClick={loadPreview}>
            {t(switching ? "sync.preview" : "sync.reload")}
          </button>
        )}
        {preview && (
          <button className="btn primary" disabled={busy || !canRun(preview, mode)} onClick={run}>
            {t(runLabel)}
          </button>
        )}
      </div>
    </Modal>
  );
}

interface PreviewViewProps {
  preview: SyncPreview;
  switching: boolean;
  choices: ConflictChoices;
  onChoose: (conflict: SyncPreview["conflicts"][number], choice: ConflictChoice) => void;
  onChooseAll: (choice: ConflictChoice) => void;
}

/** The conflicts first, then what else a run would carry over as one line (the lists behind "details"). */
function PreviewView({ preview, switching, choices, onChoose, onChooseAll }: PreviewViewProps) {
  const { t } = useI18n();
  const [details, setDetails] = useState(false);
  const changes = changeCount(preview);
  const { total } = summarizePreview(preview);
  const conflicts = preview.conflicts.length;
  return (
    <div className="sync-preview">
      {conflicts > 0 && (
        <>
          <SyncConflicts conflicts={preview.conflicts} choices={choices} onChoose={onChoose} onChooseAll={onChooseAll} />
          {switching && <p className="field-error">{t("sync.conflicts.needed")}</p>}
        </>
      )}
      <section className="sync-changes">
        {isInSync(preview) && <div className="sync-equal">{t("sync.inSync")}</div>}
        {!isInSync(preview) && changes === 0 && <div className="hint">{t("sync.changes.none")}</div>}
        {changes > 0 && (
          <div className="sync-changes-line">
            <span>{t(conflicts > 0 ? "sync.changes.also" : "sync.changes", { n: changes, c: total.created, m: total.changed })}</span>
            <button type="button" className="btn link" aria-expanded={details} onClick={() => setDetails(!details)}>
              {t(details ? "sync.details.hide" : "sync.details.show")}
            </button>
          </div>
        )}
        {details &&
          visibleKinds(preview).map((kind) => {
            const s = preview[kind];
            return (
              <section key={kind}>
                <h4>{t(`sync.${kind}`)}</h4>
                <div>{t("sync.count", { n: s.created.length, c: s.changed.length, u: s.unchanged })}</div>
                <ul className="sync-list">
                  {s.created.map((e) => (
                    <li key={`+${e.label}${e.name ?? ""}`}>{`＋ ${entryText(e)}${origin(e)}`}</li>
                  ))}
                  {s.changed.map((e) => (
                    <li key={`~${e.label}${e.name ?? ""}`} title={t("sync.changedHint")}>{`≠ ${entryText(e)}${origin(e)}`}</li>
                  ))}
                </ul>
              </section>
            );
          })}
      </section>
      {preview.skipped.length > 0 && (
        <div className="sync-skipped">
          <h4>{t("sync.skipped.title")}</h4>
          <ul className="sync-list">
            {preview.skipped.map((e) => (
              <li key={`s${e.label}${e.name ?? ""}`}>{entryText(e)}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function ResultView({ result }: { result: SyncPreview }) {
  const { t } = useI18n();
  return (
    <div className="sync-result">
      <div>{t("sync.done")}</div>
      {result.deleted.length > 0 && <div>{t("sync.done.deleted", { n: result.deleted.length })}</div>}
      {result.deferred.length > 0 && <div>{t("sync.done.deferred", { n: result.deferred.length })}</div>}
    </div>
  );
}
