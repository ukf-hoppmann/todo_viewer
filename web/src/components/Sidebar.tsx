import type { SourceStatus } from "../api/client";
import { priorityColor, statusColor } from "../domain/colors";
import type { FilterOptions } from "../domain/model";
import { useI18n } from "../i18n/i18n";
import { LANGS } from "../i18n/messages";
import { useUiState } from "../state/useUiStateStore";
import type { HiddenKind } from "../state/uiState";

interface SidebarProps {
  options: FilterOptions;
  sources: SourceStatus[];
  onAddSource: () => void;
  onEditSource: (source: SourceStatus) => void;
  onRemoveSource: (source: SourceStatus) => void;
  onSyncSource: (source: SourceStatus) => void;
  onOpenSettings: () => void;
}

export function Sidebar({ options, sources, onAddSource, onEditSource, onRemoveSource, onSyncSource, onOpenSettings }: SidebarProps) {
  const { t, vocab } = useI18n();
  const { state, dispatch } = useUiState();

  return (
    <aside className="sidebar">
      <div className="sidebar-head">
        <h1>{t("app.title")}</h1>
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
        <ProjectFilters projects={options.projects} sources={sources} onEdit={onEditSource} onRemove={onRemoveSource} onSync={onSyncSource} />
      </section>

      <FilterGroup
        title={t("filter.status")}
        kind="hiddenStatuses"
        values={options.statuses}
        color={statusColor}
        label={(v) => vocab("status", v)}
      />
      <FilterGroup
        title={t("filter.priority")}
        kind="hiddenPriorities"
        values={options.priorities}
        color={priorityColor}
        label={(v) => vocab("priority", v)}
      />
    </aside>
  );
}

interface FilterGroupProps {
  title: string;
  kind: HiddenKind;
  values: string[];
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
  onEdit: (source: SourceStatus) => void;
  onRemove: (source: SourceStatus) => void;
  onSync: (source: SourceStatus) => void;
}

/** One row per source; a project can consist of several sources. */
function ProjectFilters({ projects, sources, onEdit, onRemove, onSync }: ProjectFiltersProps) {
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
                  {source?.backend === "database" && (
                    <span className="db-badge" title={t("source.badge.db.title")}>
                      {t("source.badge.db")}
                    </span>
                  )}
                  {problem && <span className="warn">⚠</span>}
                </div>
                {source && (
                  <>
                    {source.backend === "database" && source.sync_path && (
                      <button className="icon-btn" title={t("source.sync")} aria-label={t("source.sync")} onClick={() => onSync(source)}>
                        ⇄
                      </button>
                    )}
                    <button className="icon-btn" title={t("source.edit.title")} aria-label={t("source.edit.title")} onClick={() => onEdit(source)}>
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
