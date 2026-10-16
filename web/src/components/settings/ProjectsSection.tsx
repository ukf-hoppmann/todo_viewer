import { useEffect, useId, useRef, useState } from "react";
import type { Schemas, SourceStatus } from "../../api/client";
import { useSaveSource, useSourceList, useSyncStatuses } from "../../api/queries";
import { describeProject } from "../../domain/projects";
import type { SyncMode, SyncState } from "../../domain/sync";
import { describeError, useI18n } from "../../i18n/i18n";
import { useUiState } from "../../state/useUiStateStore";
import { SourceDialog } from "../SourceDialog";
import { SyncDialog } from "../SyncDialog";
import type { SectionProps } from "./sections";

type Dialog = { kind: "sync"; source: SourceStatus } | { kind: "switch"; source: SourceStatus } | { kind: "folder"; source: SourceStatus };

/** One card per project: where it lives, whether its mirror still matches, and the one thing to do next. */
export function ProjectsSection({ focusId }: SectionProps) {
  const { t } = useI18n();
  const { dispatch } = useUiState();
  const sources = useSourceList();
  const statuses = useSyncStatuses();
  const [dialog, setDialog] = useState<Dialog | null>(null);
  const stateOf = new Map(statuses.data?.map((s) => [s.source_id, s]));

  if (!sources.data) return <div className="hint">{t("settings.db.loading")}</div>;
  return (
    <div className="settings-section">
      {sources.data.length === 0 && <p className="hint">{t("projects.empty")}</p>}
      {sources.data.map((source) => (
        <ProjectCard
          key={source.id}
          source={source}
          state={stateOf.get(source.id)}
          checking={statuses.isFetching}
          focused={source.id === focusId}
          onCheck={() => void statuses.refetch()}
          onOpen={(kind) => setDialog({ kind, source })}
        />
      ))}
      {dialog && (dialog.kind === "folder" ? (
        <SourceDialog source={dialog.source} part="folder" onClose={() => setDialog(null)} onSaved={() => setDialog(null)} />
      ) : (
        <SyncDialog
          source={dialog.source}
          mode={dialog.kind as SyncMode}
          onClose={() => setDialog(null)}
          onSwitched={(project) => {
            dispatch({ type: "showProject", project });
            setDialog(null);
          }}
        />
      ))}
    </div>
  );
}

interface ProjectCardProps {
  source: SourceStatus;
  state: Pick<Schemas["SyncStatusOut"], "state" | "last_sync_at" | "conflicts" | "auto_sync" | "auto_last_run_at" | "auto_paused"> & { state: SyncState } | undefined;
  checking: boolean;
  focused: boolean;
  onCheck: () => void;
  onOpen: (kind: Dialog["kind"]) => void;
}

function ProjectCard({ source, state, checking, focused, onCheck, onOpen }: ProjectCardProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const save = useSaveSource();
  const [error, setError] = useState("");
  const [setupOpen, setSetupOpen] = useState(false);
  const setupId = useId();
  const ref = useRef<HTMLElement>(null);
  const database = source.primary === "database";
  const folder = source.markdown_path;
  const view = describeProject(source, state);

  useEffect(() => {
    if (focused) ref.current?.scrollIntoView?.({ block: "nearest" });
  }, [focused]);

  const change = (request: Parameters<typeof save.mutate>[0], then?: () => void) => {
    setError("");
    save.mutate(request, { onSuccess: then, onError: (e) => setError(describeError(i18n, e)) });
  };

  const toggleDatabaseMirror = (on: boolean) => {
    if (!on && !window.confirm(t("projects.mirror.offConfirm", { p: source.project }))) return;
    change({ id: source.id, project: source.project, path: source.path, mirror: on ? "database" : "none" });
  };

  // The folder is sent again, so switching the mirror off and on keeps it; only an emptied folder removes it.
  const setMarkdownMirror = (on: boolean) =>
    change({ id: source.id, project: source.project, path: "", syncPath: folder ?? "", mirror: on ? "markdown" : "none" });
  const setMirror = database ? setMarkdownMirror : toggleDatabaseMirror;

  const when = (iso: string | null | undefined) => (iso ? new Date(iso).toLocaleString(i18n.lang) : t("projects.lastSync.never"));
  const otherName = t(`source.backend.${database ? "markdown" : "database"}`);

  const stateText = view.status === "loading" ? t("projects.state.loading") : view.status === "none" ? t("projects.state.noMirror") : t(`sync.state.${view.status}`);
  const emphasis = view.tone === "attention" || view.tone === "pending";
  const mainAction = {
    sync: { label: t("projects.sync"), run: () => onOpen("sync") },
    enableMirror: { label: t(database ? "projects.action.enableMarkdown" : "projects.action.enableDatabase"), run: () => setMirror(true) },
    setupMirror: { label: t("projects.folder.set"), run: () => onOpen("folder") },
    resolve: null,
  }[view.action];

  return (
    <section ref={ref} className={`project-card tone-${view.tone}${focused ? " focused" : ""}`} role="group" aria-label={source.project} aria-current={focused ? "true" : undefined}>
      <header>
        <h4>{source.project}</h4>
        <span className={`project-state ${view.tone}`}>{stateText}</span>
      </header>

      <div className="project-flow">
        <div className="project-side">
          <span className="project-role">{t("projects.primary")}</span>
          <span className="project-backend">{t(`source.backend.${source.primary}`)}</span>
          {!database && folder && <span className="mono project-folder" title={folder}>{folder}</span>}
        </div>
        {view.hasMirror && (
          <>
            <span className="project-arrow" aria-hidden="true">⇄</span>
            <div className="project-side">
              <span className="project-role">{t("projects.mirror")}</span>
              <span className="project-backend">{otherName}</span>
              {database && folder && <span className="mono project-folder" title={folder}>{folder}</span>}
            </div>
          </>
        )}
        {view.mirrorOff && folder && (
          <div className="project-side off">
            <span className="project-role">{t("projects.mirror.offRole")}</span>
            <span className="project-backend">{otherName}</span>
            <span className="mono project-folder" title={folder}>{folder}</span>
          </div>
        )}
      </div>

      {view.conflicts > 0 && (
        <div className="project-conflicts" role="status">
          <span>{t("projects.conflicts", { n: view.conflicts })}</span>
          <button className="btn small primary" onClick={() => onOpen("sync")}>{t("projects.resolve")}</button>
        </div>
      )}
      {error && <div className="field-error" role="alert">{error}</div>}

      <footer className="project-footer">
        <div className="project-meta">
          {view.hasMirror && <span className="project-lastsync">{t("projects.lastSync", { at: when(state?.last_sync_at) })}</span>}
          {state?.auto_sync && (
            <span className={`project-auto${state.auto_paused ? " warn" : ""}`} role="status">
              {state.auto_paused
                ? t("projects.auto.paused", { r: i18n.errorText(state.auto_paused, state.auto_paused) })
                : t("projects.auto.lastRun", { at: when(state.auto_last_run_at) })}
            </span>
          )}
        </div>
        <div className="project-actions">
          {view.hasMirror && (
            <button className="btn small ghost" disabled={checking} onClick={onCheck}>
              {t("projects.state.check")}
            </button>
          )}
          {mainAction && (
            <button className={`btn small${emphasis ? " primary" : ""}`} disabled={save.isPending} onClick={mainAction.run}>
              {mainAction.label}
            </button>
          )}
        </div>
      </footer>

      <button className="project-setup-toggle" aria-expanded={setupOpen} aria-controls={setupId} onClick={() => setSetupOpen(!setupOpen)}>
        {t("projects.setup")}
      </button>
      {setupOpen && (
        <dl id={setupId} className="settings-facts project-setup">
          <dt>{t("projects.folder")}</dt>
          <dd>
            <span className="mono project-folder" title={folder ?? undefined}>{folder ?? t("projects.folder.none")}</span>
            <button className="btn link" onClick={() => onOpen("folder")}>
              {t(folder ? "projects.folder.change" : "projects.folder.set")}
            </button>
          </dd>
          <dt>{t("projects.mirror")}</dt>
          <dd>
            <label>
              <input type="checkbox" checked={source.mirror !== "none"} disabled={save.isPending || (database && !folder)} onChange={(e) => setMirror(e.target.checked)} />
              {t(database ? "projects.mirror.markdown" : "projects.mirror.database")}
            </label>
            {database && !folder && <span className="hint">{t("projects.mirror.needsFolder")}</span>}
          </dd>
          <dt>{t("projects.auto")}</dt>
          <dd>
            <label>
              <input
                type="checkbox"
                checked={source.auto_sync}
                disabled={save.isPending || !view.autoSwitchable}
                onChange={(e) => change({ id: source.id, project: source.project, path: source.path, syncPath: database ? (folder ?? "") : undefined, autoSync: e.target.checked })}
              />
              {t("projects.auto.label")}
            </label>
            {view.autoIdle && <span className="hint">{t("projects.auto.noMirror")}</span>}
            {!view.autoSwitchable && <span className="hint">{t("projects.auto.needsMirror")}</span>}
          </dd>
          <dt>{t("projects.primary")}</dt>
          <dd>
            <span>{t(`source.backend.${source.primary}`)}</span>
            <button className="btn link" disabled={view.switchBlocked} onClick={() => onOpen("switch")}>
              {t(database ? "projects.switch.toMarkdown" : "projects.switch.toDatabase")}
            </button>
            <span className="hint">{t(view.switchBlocked ? "projects.switch.blocked" : "projects.switch.hint")}</span>
          </dd>
        </dl>
      )}
    </section>
  );
}
