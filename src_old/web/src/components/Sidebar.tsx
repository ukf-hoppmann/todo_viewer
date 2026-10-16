import { DueBadge } from "./DueBadge";
import type { SourceStatus } from "../api/client";
import { noteStatusColor, priorityColor, statusColor } from "../domain/colors";
import type { FilterOptions } from "../domain/model";
import { NOTE_STATUSES } from "../domain/notes";
import { autoSyncOn } from "../domain/projects";
import { sidebarSections } from "../domain/sidebar";
import { needsAttention, type SyncState } from "../domain/sync";
import { useI18n } from "../i18n/i18n";
import { LANGS, type MessageKey } from "../i18n/messages";
import { useUiState } from "../state/useUiStateStore";
import type { HiddenKind } from "../state/uiState";

interface SidebarProps {
  options: FilterOptions;
  sources: SourceStatus[];
  onAddSource: () => void;
  onRemoveSource: (source: SourceStatus) => void;
  onSyncSource: (source: SourceStatus) => void;
  onOpenSettings: () => void;
  /** The sync state of each project by source id; a project whose mirror needs attention gets a badge. */
  syncStates: ReadonlyMap<string, SyncState>;
  /** Open sync conflicts per project (source id); missing = none. */
  syncConflicts?: ReadonlyMap<string, number>;
  /** Opens the settings at this project: from the badge, and from the edit button, which leads to all its settings. */
  onOpenProject: (source: SourceStatus) => void;
  /** Number of due notes (the red exclamation mark shows if above zero) and what a click on it does. */
  dueCount?: number;
  onOpenDue?: () => void;
}

/** Search and projects for every tab; below them the filter sections of the active tab (`sidebarSections`). */
export function Sidebar({ options, sources, onAddSource, onRemoveSource, onSyncSource, onOpenSettings, syncStates, syncConflicts, onOpenProject, dueCount = 0, onOpenDue }: SidebarProps) {
  const { t, vocab } = useI18n();
  const { state, dispatch } = useUiState();

  return (
    <aside className="sidebar">
      <div className="sidebar-head">
        <div className="sidebar-title">
          <h1>{t("app.title")}</h1>
          {onOpenDue && <DueBadge count={dueCount} onOpen={onOpenDue} />}
        </div>
        <div className="sidebar-tools">
          <div className="lang-switch" role="group" aria-label="Sprache / Language">
            {LANGS.map((lang) => (
              <button key={lang} className={state.lang === lang ? "active" : ""} onClick={() => dispatch({ type: "lang", lang })}>
                {lang.toUpperCase()}
              </button>
            ))}
          </div>
          <button className="icon-btn" title={t("settings.open")} aria-label={t("settings.open")} onClick={onOpenSettings}>
            ⚙
          </button>
        </div>
      </div>

      <input
        type="text"
        placeholder={t("search")}
        aria-label={t("search")}
        value={state.search}
        onChange={(e) => dispatch({ type: "search", text: e.target.value })}
      />

      <section className="filter-group">
        <h2 className="with-action">
          <span>{t("filter.projects")}</span>
          <button className="icon-btn add-btn" title={t("source.add.title")} onClick={onAddSource}>
            {t("source.add")}
          </button>
        </h2>
        <ProjectFilters
          projects={options.projects}
          sources={sources}
          syncStates={syncStates}
          syncConflicts={syncConflicts}
          onRemove={onRemoveSource}
          onSync={onSyncSource}
          onOpenProject={onOpenProject}
        />
      </section>

      {sidebarSections(state.currentView).map((section) => {
        switch (section) {
          case "itemStatus":
            return (
              <FilterGroup
                key={section}
                title={t("filter.status")}
                kind="hiddenStatuses"
                values={options.statuses}
                color={statusColor}
                label={(v) => vocab("status", v)}
              />
            );
          case "itemPriority":
            return (
              <FilterGroup
                key={section}
                title={t("filter.priority")}
                kind="hiddenPriorities"
                values={options.priorities}
                color={priorityColor}
                label={(v) => vocab("priority", v)}
              />
            );
          case "noteStatus":
            return (
              <FilterGroup
                key={section}
                title={t("filter.status")}
                kind="hiddenNoteStatuses"
                values={NOTE_STATUSES}
                color={noteStatusColor}
                label={(v) => t(`note.status.${v}` as MessageKey)}
              />
            );
        }
      })}
    </aside>
  );
}

interface FilterGroupProps {
  title: string;
  kind: HiddenKind;
  values: readonly string[];
  color: (value: string) => string;
  label: (value: string) => string;
}

function FilterGroup({ title, kind, values, color, label }: FilterGroupProps) {
  const { state, dispatch } = useUiState();
  return (
    <section className="filter-group">
      <h2>{title}</h2>
      {values.map((value) => (
        <label key={value}>
          <input
            type="checkbox"
            checked={!state[kind].has(value)}
            onChange={() => dispatch({ type: "toggleHidden", kind, value })}
          />
          <span className="dot" style={{ background: color(value) }} />
          {label(value)}
        </label>
      ))}
    </section>
  );
}

interface ProjectFiltersProps {
  projects: string[];
  sources: SourceStatus[];
  onRemove: (source: SourceStatus) => void;
  onSync: (source: SourceStatus) => void;
  syncStates: ReadonlyMap<string, SyncState>;
  /** Open sync conflicts per project (source id); missing = none. */
  syncConflicts?: ReadonlyMap<string, number>;
  onOpenProject: (source: SourceStatus) => void;
}

/** One row per source; a project can consist of several sources. */
function ProjectFilters({ projects, sources, syncStates, syncConflicts, onRemove, onSync, onOpenProject }: ProjectFiltersProps) {
  const { t, errorText } = useI18n();
  const { state, dispatch } = useUiState();

  return (
    <>
      {projects.flatMap((project) => {
        const own = sources.filter((s) => s.project === project);
        const rows: (SourceStatus | null)[] = own.length ? own : [null];
        const marked = state.markedProjects.has(project);
        return rows.map((source, idx) => {
          const problem = source?.problem ?? null;
          const problemText = problem ? errorText(problem.code, problem.message) : "";
          return (
            <div key={source?.id ?? project}>
              <div className={`source-row${problem ? " broken" : ""}${marked ? " marked" : ""}`}>
                <div className="source-label" title={source ? (source.backend === "database" ? (source.sync_path ?? "") : source.path) + (problem ? `\n⚠ ${problemText}` : "") : ""}>
                  <input
                    type="checkbox"
                    aria-label={project}
                    checked={!state.hiddenProjects.has(project)}
                    onChange={() => dispatch({ type: "toggleHidden", kind: "hiddenProjects", value: project })}
                  />
                  <button
                    className="name"
                    aria-pressed={marked}
                    title={t("filter.mark")}
                    onClick={() => dispatch({ type: "toggleMarked", project })}
                  >
                    {rows.length > 1 ? `${project} (${idx + 1})` : project}
                  </button>
                  {source?.backend === "markdown" && (
                    <span className="md-badge" title={t("source.badge.md.title")}>
                      {t("source.badge.md")}
                    </span>
                  )}
                  {source && autoSyncOn(source) && (
                    <span className="auto-sync-badge" role="img" title={t("source.badge.auto.title")} aria-label={t("source.badge.auto.title")}>
                      ↻
                    </span>
                  )}
                  {problem && <span className="warn">⚠</span>}
                  {source && !problem && needsAttention(syncStates.get(source.id) ?? "none", syncConflicts?.get(source.id) ?? 0) && (
                    <button
                      className="sync-badge"
                      title={(syncConflicts?.get(source.id) ?? 0) > 0 ? t("sync.badge.conflicts", { n: syncConflicts?.get(source.id) ?? 0 }) : t(`sync.state.${syncStates.get(source.id) ?? "none"}`)}
                      aria-label={t("projects.badge", { p: source.project })}
                      onClick={() => onOpenProject(source)}
                    >
                      ⚠
                    </button>
                  )}
                </div>
                {source && (
                  <>
                    {source.mirror !== "none" && (
                      <button className="icon-btn" title={t("source.sync")} aria-label={t("source.sync")} onClick={() => onSync(source)}>
                        ⇄
                      </button>
                    )}
                    <button className="icon-btn" title={t("source.edit.open")} aria-label={t("source.edit.open")} onClick={() => onOpenProject(source)}>
                      ✎
                    </button>
                    <button className="icon-btn danger" title={t("source.remove.title")} aria-label={t("source.remove.title")} onClick={() => onRemove(source)}>
                      ✕
                    </button>
                  </>
                )}
              </div>
              {source && problem && <div className="source-error">{`${problemText} ${source.path || source.sync_path || ""}`}</div>}
            </div>
          );
        });
      })}
    </>
  );
}
