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
}

export function Sidebar({ options, sources, onAddSource, onEditSource, onRemoveSource }: SidebarProps) {
  const { t, vocab } = useI18n();
  const { state, dispatch } = useUiState();

  return (
    <aside className="sidebar">
      <div className="sidebar-head">
        <h1>{t("app.title")}</h1>
        <div className="lang-switch" role="group" aria-label="Sprache / Language">
          {LANGS.map((lang) => (
            <button key={lang} className={state.lang === lang ? "active" : ""} onClick={() => dispatch({ type: "lang", lang })}>
              {lang.toUpperCase()}
            </button>
          ))}
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
        <ProjectFilters projects={options.projects} sources={sources} onEdit={onEditSource} onRemove={onRemoveSource} />
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
}

/** One row per source; a project can consist of several sources. */
function ProjectFilters({ projects, sources, onEdit, onRemove }: ProjectFiltersProps) {
  const { t, errorText } = useI18n();
  const { state, dispatch } = useUiState();

  return (
    <>
      {projects.flatMap((project) => {
        const own = sources.filter((s) => s.project === project);
        const rows: (SourceStatus | null)[] = own.length ? own : [null];
        return rows.map((source, idx) => {
          const problem = source?.problem ?? null;
          const problemText = problem ? errorText(problem.code, problem.message) : "";
          return (
            <div key={source?.id ?? project}>
              <div className={`source-row${problem ? " broken" : ""}`}>
                <label title={source ? source.path + (problem ? `\n⚠ ${problemText}` : "") : ""}>
                  <input
                    type="checkbox"
                    checked={!state.hiddenProjects.has(project)}
                    onChange={() => dispatch({ type: "toggleHidden", kind: "hiddenProjects", value: project })}
                  />
                  <span className="name">{rows.length > 1 ? `${project} (${idx + 1})` : project}</span>
                  {problem && <span className="warn">⚠</span>}
                </label>
                {source && (
                  <>
                    <button className="icon-btn" title={t("source.edit.title")} aria-label={t("source.edit.title")} onClick={() => onEdit(source)}>
                      ✎
                    </button>
                    <button className="icon-btn danger" title={t("source.remove.title")} aria-label={t("source.remove.title")} onClick={() => onRemove(source)}>
                      ✕
                    </button>
                  </>
                )}
              </div>
              {source && problem && <div className="source-error">{`${problemText} ${source.path}`}</div>}
            </div>
          );
        });
      })}
    </>
  );
}
