import type { Item } from "../domain/model";
import { useI18n } from "../i18n/i18n";

const MAX_CHOICES = 50;

interface ItemPickerProps {
  projects: readonly string[];
  items: readonly Item[];
  project: string;
  onProject: (project: string) => void;
  /** The chosen item's label. */
  value: string;
  onChange: (label: string) => void;
  search: string;
  onSearch: (text: string) => void;
}

/** Chooses a backlog item of any project: the project, a search over label and title, and the matching items. */
export function ItemPicker({ projects, items, project, onProject, value, onChange, search, onSearch }: ItemPickerProps) {
  const { t } = useI18n();
  const needle = search.trim().toLowerCase();
  const choices = items.filter((i) => i.project === project && `${i.id} ${i.title}`.toLowerCase().includes(needle)).slice(0, MAX_CHOICES);
  return (
    <>
      <label className="field">
        {t("note.links.project")}
        <select
          value={project}
          onChange={(e) => {
            onProject(e.target.value);
            onChange("");
          }}
        >
          {projects.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        {t("note.links.search")}
        <input value={search} onChange={(e) => onSearch(e.target.value)} />
      </label>
      <label className="field">
        {t("note.links.target")}
        <select value={value} onChange={(e) => onChange(e.target.value)}>
          <option value="" />
          {choices.map((i) => (
            <option key={i.id} value={i.id}>
              {`${i.id} — ${i.title}`}
            </option>
          ))}
        </select>
      </label>
    </>
  );
}
