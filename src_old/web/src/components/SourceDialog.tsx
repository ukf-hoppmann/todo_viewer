import { useState } from "react";
import type { SourceStatus } from "../api/client";
import { type Backend, useFolders, useSaveSource } from "../api/queries";
import { describeError, useI18n } from "../i18n/i18n";
import { useUiState } from "../state/useUiStateStore";
import { Modal } from "./Modal";

/** What the dialog asks for: a new project needs both; an existing one is renamed or gets another folder. */
export type SourcePart = "full" | "name" | "folder";

interface SourceDialogProps {
  /** null = add a new project, otherwise the source being changed. */
  source: SourceStatus | null;
  /** Default: everything for a new project, only the name for an existing one. */
  part?: SourcePart;
  onSaved: (project: string) => void;
  onClose: () => void;
}

function join(folder: string, name: string): string {
  return `${folder.replace(/\/$/, "")}/${name}`;
}

export function SourceDialog({ source, part = source ? "name" : "full", onSaved, onClose }: SourceDialogProps) {
  const i18n = useI18n();
  const { t, errorText } = i18n;
  const save = useSaveSource();
  const [project, setProject] = useState(source?.project ?? "");
  const { state: ui } = useUiState();
  const [chosenBackend, setChosenBackend] = useState<Backend>(ui.defaultBackend);
  const backend: Backend = source?.backend ?? chosenBackend;
  const database = backend === "database";
  // The folder of a markdown project, or the sync folder of a database project.
  const folder = database ? (source?.sync_path ?? null) : (source?.path ?? null);
  // Typed text wins; null means the input follows the folder shown in the browser.
  // A broken path of an existing source stays in the input while the browser shows
  // the nearest existing folder.
  const [typedPath, setTypedPath] = useState<string | null>(folder);
  const [browsePath, setBrowsePath] = useState<string | null>(folder);
  // A sync folder is optional: it stays empty until one is typed or chosen in the browser.
  const [pathChosen, setPathChosen] = useState(folder !== null);
  const [error, setError] = useState(source?.problem ? `⚠ ${errorText(source.problem.code, source.problem.message)}` : "");
  const folders = useFolders(browsePath, part !== "name");
  const listing = folders.data;
  const path = database && !pathChosen ? "" : (typedPath ?? listing?.path ?? "");

  const browseTo = (target: string, keepInput = false) => {
    setBrowsePath(target);
    setPathChosen(true);
    if (!keepInput) {
      setTypedPath(null);
      setError("");
    }
  };

  const submit = (targetPath = path) => {
    const trimmed = targetPath.trim();
    if (database ? !project.trim() : !trimmed) {
      setError(t(database ? "err.value_required" : "err.missing_path"));
      return;
    }
    setError("");
    save.mutate(
      {
        id: source?.id ?? null,
        project: project.trim(),
        // A database project has no folder of its own; its sync folder is sent apart ("" clears it).
        path: database ? "" : trimmed,
        backend: source ? undefined : backend,
        syncPath: database ? (source ? trimmed : trimmed || undefined) : undefined,
      },
      {
        onSuccess: (saved) => onSaved(saved.project),
        onError: (e) => setError(describeError(i18n, e)),
      },
    );
  };

  const onEnter = (e: React.KeyboardEvent) => e.key === "Enter" && submit();

  return (
    <Modal labelledBy="source-title" onDismiss={onClose}>
      <h3 id="source-title">
        {t(!source ? "source.add.title" : part === "name" ? "source.rename.title" : database ? "source.folder.titleDb" : "source.edit.title")}
      </h3>
      {!source ? (
        <div className="backend-choice" role="radiogroup" aria-label={t("source.backend")}>
          {(["markdown", "database"] as const).map((b) => (
            <label key={b}>
              <input type="radio" name="backend" checked={backend === b} onChange={() => setChosenBackend(b)} />
              {t(`source.backend.${b}`)}
            </label>
          ))}
        </div>
      ) : part === "folder" ? (
        <div className="backend-fixed">{t("source.backend.fixed", { b: t(`source.backend.${backend}`) })}</div>
      ) : null}
      {part !== "folder" && (
      <div>
        <label className="field" htmlFor="source-project">
          {t("source.name")}
        </label>
        <input
          id="source-project"
          type="text"
          autoFocus={!source}
          placeholder={t(database ? "source.name.db.ph" : "source.name.ph")}
          value={project}
          onChange={(e) => setProject(e.target.value)}
          onKeyDown={onEnter}
        />
      </div>
      )}
      {part !== "name" && (<>
      <div>
        <label className="field" htmlFor="source-path">
          {t(database ? "source.syncPath" : "source.path")}
        </label>
        <input
          id="source-path"
          type="text"
          autoFocus={!!source}
          placeholder={t("source.path.ph")}
          value={path}
          onChange={(e) => {
            setTypedPath(e.target.value);
            setPathChosen(true);
          }}
          onBlur={() => path.trim() && browseTo(path.trim(), true)}
          onKeyDown={onEnter}
        />
      </div>

      <div className="browser">
        <div className="browser-path">
          <button
            className="icon-btn"
            title={t("browser.up")}
            aria-label={t("browser.up")}
            disabled={!listing?.parent}
            onClick={() => listing?.parent && browseTo(listing.parent)}
          >
            ↑
          </button>
          {/* LRM marks keep the leading "/" visible with right-aligned truncation (direction: rtl). */}
          <span title={listing?.path}>{listing ? `‎${listing.path}‎` : ""}</span>
        </div>
        <div className="browser-list">
          {folders.error ? (
            <div className="browser-empty">{t("browser.failed", { e: describeError(i18n, folders.error) })}</div>
          ) : listing?.error ? (
            <div className="browser-empty">{t("browser.unreadable", { e: listing.error })}</div>
          ) : listing && listing.dirs.length === 0 ? (
            <div className="browser-empty">{t("browser.empty")}</div>
          ) : (
            listing?.dirs.map((dir) => (
              <button
                key={dir.name}
                className="browser-entry"
                onClick={() => browseTo(join(listing.path, dir.name))}
                onDoubleClick={() => {
                  if (!dir.has_todo) return;
                  const target = join(listing.path, dir.name);
                  setTypedPath(target);
                  submit(target);
                }}
              >
                <span className="ico">📁</span>
                <span>{dir.name}</span>
                {dir.has_todo && <span className="todo-tag">TODO.md</span>}
              </button>
            ))
          )}
        </div>
      </div>

      {listing && (!database || path) && (
        <div className={`todo-status ${listing.has_todo ? "ok" : "missing"}`}>
          {t(listing.has_todo ? "browser.hasTodo" : "browser.noTodo")}
        </div>
      )}
      </>)}
      <div className="modal-error">{error}</div>
      <div className="modal-actions">
        <button className="btn" onClick={onClose}>
          {t("cancel")}
        </button>
        <button className="btn primary" disabled={save.isPending} onClick={() => submit()}>
          {t("ok")}
        </button>
      </div>
    </Modal>
  );
}
