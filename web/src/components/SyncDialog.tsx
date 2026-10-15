import { useState } from "react";
import type { SourceStatus } from "../api/client";
import { useSwitchBackend, useSyncSource } from "../api/queries";
import { canRun, directionOf, isInSync, type SyncMode, type SyncPreview, type SyncScope, switchDirection } from "../domain/sync";
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

type Entry = Pick<SyncPreview["items"]["created"][number], "label" | "name" | "title">;
const entryText = (e: Entry) => (e.name ? `${e.label} / ${e.name}` : `${e.label} — ${e.title}`);
/** Which side the entry comes from: the arrow points to where it goes. */
const origin = (e: { origin: "database" | "markdown" | null }) => (e.origin === "database" ? " →" : e.origin === "markdown" ? " ←" : "");

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
  const [chosen, setChosen] = useState<SyncScope>("both");
  const direction = switching ? switchDirection(source.backend) : directionOf(chosen);

  const preview: SyncPreview | null = sync.data && !sync.data.executed ? sync.data : null;
  const result: SyncPreview | null = sync.data?.executed ? sync.data : null;
  const busy = sync.isPending || move.isPending;
  const error = sync.error ?? move.error;
  const request = { sourceId: source.id, direction, language: i18n.lang };

  const run = () => {
    if (!preview) return;
    const confirmed = { ...request, token: preview.token };
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
            {(["both", "to_md", "from_md"] as const).map((d) => (
              <label key={d}>
                <input
                  type="radio"
                  name="direction"
                  checked={chosen === d}
                  onChange={() => {
                    setChosen(d);
                    sync.reset();
                  }}
                />
                {t(`sync.dir.${d}`)}
                {d === "both" && ` ${t("sync.dir.default")}`}
              </label>
            ))}
          </div>
        </>
      )}

      {preview && <PreviewView preview={preview} switching={switching} />}
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
          <button className="btn primary" disabled={busy || !canRun(preview, mode)} onClick={run}>
            {t(switching ? "sync.runSwitch" : "sync.run")}
          </button>
        )}
      </div>
    </Modal>
  );
}

function PreviewView({ preview, switching }: { preview: SyncPreview; switching: boolean }) {
  const { t } = useI18n();
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
                <li key={`+${e.label}${e.name ?? ""}`}>{`＋ ${entryText(e)}${origin(e)}`}</li>
              ))}
              {s.changed.map((e) => (
                <li key={`~${e.label}${e.name ?? ""}`} title={t("sync.changedHint")}>{`≠ ${entryText(e)}${origin(e)}`}</li>
              ))}
            </ul>
          </section>
        );
      })}
      {preview.conflicts.length > 0 && (
        <div className="sync-missing" role="group" aria-label={t("sync.conflicts.title")}>
          <h4>⚠ {t("sync.conflicts.title")}</h4>
          <p>{t("sync.conflicts.hint")}</p>
          <ul className="sync-list">
            {preview.conflicts.map((c) => (
              <li key={`c${c.kind}${c.label}${c.name ?? ""}`}>{`${entryText(c)} (${t(`sync.conflict.${c.reason}`)})`}</li>
            ))}
          </ul>
          {switching && <p className="field-error">{t("sync.conflicts.needed")}</p>}
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
      {result.deferred.length > 0 && <div>{t("sync.done.deferred", { n: result.deferred.length })}</div>}
    </div>
  );
}
