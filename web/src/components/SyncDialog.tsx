import { useState } from "react";
import type { SourceStatus } from "../api/client";
import { useSwitchBackend, useSyncSource } from "../api/queries";
import { canRun, defaultDirection, hasMissing, isInSync, type SyncDirection, type SyncMode, type SyncPreview, switchDirection } from "../domain/sync";
import { ApiError } from "../api/client";
import { describeError, type I18n, useI18n } from "../i18n/i18n";
import { Modal } from "./Modal";

interface SyncDialogProps {
  /** A database project (sync, switch to markdown) or a markdown project (switch to the database). */
  source: SourceStatus;
  mode: SyncMode;
  onClose: () => void;
  /** The project now lives on the other backend. */
  onSwitched: (project: string) => void;
}

type Entry = SyncPreview["items"]["created"][number];
const entryText = (e: Entry) => (e.name ? `${e.label} / ${e.name}` : `${e.label} — ${e.title}`);

/** Like describeError, but names why a folder could not be synced. */
function syncError(i18n: I18n, error: unknown): string {
  if (error instanceof ApiError && error.code === "sync_source_invalid") {
    const reason = i18n.errorText(error.details.reason, error.details.reason ?? "");
    return `${i18n.errorText(error.code, error.message)}: ${reason}`;
  }
  return describeError(i18n, error);
}

/** Preview, then confirm: copies a database project to or from its markdown folder, or moves the project. */
export function SyncDialog({ source, mode, onClose, onSwitched }: SyncDialogProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const sync = useSyncSource();
  const move = useSwitchBackend();
  const switching = mode === "switch";
  const folder = source.backend === "database" ? (source.sync_path ?? "") : source.path;
  const primaryToMirror = defaultDirection(source.backend);
  const [chosen, setChosen] = useState<SyncDirection>(primaryToMirror);
  const direction = switching ? switchDirection(source.backend) : chosen;
  const [deleteMissing, setDeleteMissing] = useState(false);

  const preview: SyncPreview | null = sync.data && !sync.data.executed ? sync.data : null;
  const result: SyncPreview | null = sync.data?.executed ? sync.data : null;
  const busy = sync.isPending || move.isPending;
  const error = sync.error ?? move.error;
  const request = { sourceId: source.id, direction, language: i18n.lang };

  const run = () => {
    if (!preview) return;
    const confirmed = { ...request, token: preview.token, deleteMissing };
    if (switching) {
      move.mutate({ ...confirmed, backend: source.backend === "markdown" ? "database" : "markdown" }, { onSuccess: (saved) => onSwitched(saved.project) });
    } else {
      sync.mutate({ ...confirmed, confirm: true });
    }
  };

  const title = switching
    ? t(source.backend === "markdown" ? "sync.switch.toDb.title" : "sync.switch.toMd.title", { p: source.project })
    : t("sync.title", { p: source.project });

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
          <div className="backend-choice" role="radiogroup" aria-label={t("sync.direction")}>
            {(["to_md", "from_md"] as const).map((d) => (
              <label key={d}>
                <input
                  type="radio"
                  name="direction"
                  checked={direction === d}
                  onChange={() => {
                    setChosen(d);
                    sync.reset();
                    setDeleteMissing(false);
                  }}
                />
                {t(`sync.dir.${d}`)}
                {d === primaryToMirror && ` ${t("sync.dir.default")}`}
              </label>
            ))}
          </div>
        </>
      )}

      {preview && <PreviewView preview={preview} deleteMissing={deleteMissing} onDeleteMissing={setDeleteMissing} switching={switching} />}
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
          <button className="btn" disabled={busy} onClick={() => sync.mutate({ ...request, confirm: false })}>
            {t("sync.preview")}
          </button>
        )}
        {preview && (
          <button className="btn primary" disabled={busy || !canRun(preview, mode, deleteMissing)} onClick={run}>
            {t(switching ? "sync.runSwitch" : "sync.run")}
          </button>
        )}
      </div>
    </Modal>
  );
}

function PreviewView({ preview, deleteMissing, onDeleteMissing, switching }: {
  preview: SyncPreview;
  deleteMissing: boolean;
  onDeleteMissing: (value: boolean) => void;
  switching: boolean;
}) {
  const { t } = useI18n();
  const missing = [...preview.items.missing, ...preview.documents.missing];
  return (
    <div className="sync-preview">
      {isInSync(preview) && <div className="sync-equal">{t("sync.inSync")}</div>}
      {(["items", "documents"] as const).map((kind) => {
        const s = preview[kind];
        return (
          <section key={kind}>
            <h4>{t(`sync.${kind}`)}</h4>
            <div>{t("sync.count", { n: s.created.length, c: s.changed.length, u: s.unchanged })}</div>
            <ul className="sync-list">
              {s.created.map((e) => (
                <li key={`+${e.label}${e.name ?? ""}`}>{`＋ ${entryText(e)}`}</li>
              ))}
              {s.changed.map((e) => (
                <li key={`~${e.label}${e.name ?? ""}`} title={t("sync.changedHint")}>{`≠ ${entryText(e)}`}</li>
              ))}
            </ul>
          </section>
        );
      })}
      {missing.length > 0 && (
        <div className="sync-missing" role="group" aria-label={t("sync.missing.title")}>
          <h4>⚠ {t("sync.missing.title")}</h4>
          <p>{t("sync.missing.hint")}</p>
          <ul className="sync-list">
            {missing.map((e) => (
              <li key={`-${e.label}${e.name ?? ""}`}>{entryText(e)}</li>
            ))}
          </ul>
          <label>
            <input type="checkbox" checked={deleteMissing} onChange={(e) => onDeleteMissing(e.target.checked)} />
            {t("sync.deleteMissing")}
          </label>
          {switching && !deleteMissing && hasMissing(preview) && <p className="field-error">{t("sync.deleteMissing.needed")}</p>}
        </div>
      )}
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
      {result.kept.length > 0 && <div>{t("sync.done.kept", { n: result.kept.length })}</div>}
    </div>
  );
}
