import { badgeLabel } from "../domain/notes";
import { useI18n } from "../i18n/i18n";

interface DueBadgeProps {
  count: number;
  onOpen: () => void;
}

/** The discreet red exclamation mark next to the title with the number of due notes. Not shown at zero. */
export function DueBadge({ count, onOpen }: DueBadgeProps) {
  const { t } = useI18n();
  if (count <= 0) return null;
  const label = t("due.badge", { n: count });
  return (
    <button className="due-badge" title={label} aria-label={label} onClick={onOpen}>
      <svg viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
        <circle cx="8" cy="8" r="8" fill="currentColor" />
        <rect x="7.1" y="3.2" width="1.8" height="6" rx=".9" fill="#fff" />
        <circle cx="8" cy="11.8" r="1.1" fill="#fff" />
      </svg>
      <span className="due-badge-count">{badgeLabel(count)}</span>
    </button>
  );
}
