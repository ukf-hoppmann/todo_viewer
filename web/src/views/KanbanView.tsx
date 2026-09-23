import { useMemo } from "react";
import { priorityColor } from "../domain/colors";
import { groupByStatus, type Item, type Uid } from "../domain/model";
import { useI18n } from "../i18n/i18n";
import { useUiState } from "../state/useUiStateStore";

interface KanbanViewProps {
  visible: Item[];
  onSelect: (uid: Uid) => void;
}

export function KanbanView({ visible, onSelect }: KanbanViewProps) {
  const { t, vocab } = useI18n();
  const { state } = useUiState();
  const columns = useMemo(() => groupByStatus(visible), [visible]);

  if (columns.length === 0) return <div className="view"><p className="empty-hint">{t("empty")}</p></div>;

  return (
    <div className="view kanban-view">
      {columns.map(({ status, items }) => (
        <section key={status} className="kanban-col" aria-label={vocab("status", status)}>
          <h3>{`${vocab("status", status)} (${items.length})`}</h3>
          {items.map((item) => (
            <button
              key={item.key}
              className={`kanban-card${item.uid === state.selectedId ? " selected" : ""}`}
              style={{ borderLeftColor: priorityColor(item.priority) }}
              onClick={() => onSelect(item.uid)}
            >
              <div className="k-id">{`${item.ref.id} · ${item.project}`}</div>
              <div>{item.title}</div>
              {item.priority && (
                <span className="prio-badge" style={{ background: priorityColor(item.priority) }}>
                  {vocab("priority", item.priority)}
                </span>
              )}
            </button>
          ))}
        </section>
      ))}
    </div>
  );
}
