import { useEffect, useRef, useState } from "react";
import type { SourceStatus } from "../../api/client";
import { useSaveSource, useSourceList, useSyncStatuses } from "../../api/queries";
import type { SyncMode, SyncState } from "../../domain/sync";
import { describeError, useI18n } from "../../i18n/i18n";
import { useUiState } from "../../state/useUiStateStore";
import { SourceDialog } from "../SourceDialog";
import { SyncDialog } from "../SyncDialog";
import type { SectionProps } from "./sections";

type Dialog = { kind: "sync"; source: SourceStatus } | { kind: "switch"; source: SourceStatus } | { kind: "folder"; source: SourceStatus };

/** One card per project: where it lives, its mirror, whether the two still match, and what can be done about it. */
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
  state: { state: SyncState; last_sync_at: string | null } | undefined;
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
  const ref = useRef<HTMLElement>(null);
  const database = source.primary === "database";
  const folder = source.markdown_path;

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

  const lastSync = state?.last_sync_at ? new Date(state.last_sync_at).toLocaleString(i18n.lang) : t("projects.lastSync.never");

  return (
    <section ref={ref} className={`project-card${focused ? " focused" : ""}`} role="group" aria-label={source.project} aria-current={focused ? "true" : undefined}>
      <header>
        <h4>{source.project}</h4>
        <span className={`project-state ${state?.state ?? ""}`}>{state ? t(`sync.state.${state.state}`) : t("projects.state.loading")}</span>
      </header>
      <dl className="settings-facts">
        <dt>{t("projects.primary")}</dt>
        <dd>
          <span className="project-primary">{t(`source.backend.${source.primary}`)}</span>
          <button className="btn small" disabled={database && !folder} onClick={() => onOpen("switch")}>
            {t("projects.switch")}
          </button>
        </dd>
        <dt>{t("projects.folder")}</dt>
        <dd>
          <span className="mono">{folder ?? t("projects.folder.none")}</span>
          <button className="btn small" onClick={() => onOpen("folder")}>
            {t(folder ? "projects.folder.change" : "projects.folder.set")}
          </button>
        </dd>
        <dt>{t("projects.mirror")}</dt>
        <dd>
          {database ? (
            <>
              <span>{t(source.mirror !== "none" ? "projects.mirror.markdown" : folder ? "projects.mirror.off" : "projects.mirror.none")}</span>
              {folder && (
                <button className="btn small" disabled={save.isPending} onClick={() => setMarkdownMirror(source.mirror === "none")}>
                  {t(source.mirror === "none" ? "projects.mirror.on" : "projects.mirror.remove")}
                </button>
              )}
            </>
          ) : (
            <label>
              <input type="checkbox" checked={source.mirror === "database"} disabled={save.isPending} onChange={(e) => toggleDatabaseMirror(e.target.checked)} />
              {t("projects.mirror.database")}
            </label>
          )}
        </dd>
        <dt>{t("projects.lastSync.title")}</dt>
        <dd>{t("projects.lastSync", { at: lastSync })}</dd>
      </dl>
      {error && <div className="field-error" role="alert">{error}</div>}
      <div className="project-actions">
        <button className="btn small" disabled={source.mirror === "none"} onClick={() => onOpen("sync")}>
          {t("projects.sync")}
        </button>
        <button className="btn small" disabled={checking} onClick={onCheck}>
          {t("projects.state.check")}
        </button>
      </div>
    </section>
  );
}
