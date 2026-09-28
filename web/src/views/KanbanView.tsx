import { useMemo } from "react";
import { priorityColor } from "../domain/colors";
import { ProgressPie } from "../components/ProgressPie";
import { groupByStatus, itemProgress, type Item, type Uid } from "../domain/model";
import { useI18n } from "../i18n/i18n";
import { useUiState } from "../state/useUiStateStore";

interface KanbanViewProps {
  visible: Item[];
  /** All items, unfiltered; progress is computed over these. */
  items: Item[];
  onSelect: (uid: Uid) => void;
}

export function KanbanView({ visible, items, onSelect }: KanbanViewProps) {
  const { t, vocab } = useI18n();
  const { state } = useUiState();
  const columns = useMemo(() => groupByStatus(visible), [visible]);
  const progress = useMemo(() => itemProgress(items), [items]);

  if (columns.length === 0) return <div className="view"><p className="empty-hint">{t("empty")}</p></div>;

  return (
    <div className="view kanban-view">
      {columns.map(({ status, items: cards }) => (
        <section key={status} className="kanban-col" aria-label={vocab("status", status)}>
          <h3>{`${vocab("status", status)} (${cards.length})`}</h3>
          {cards.map((item) => {
            const cardProgress = progress.get(item.uid);
            return (
              <button
                key={item.key}
                className={`kanban-card${item.uid === state.selectedId ? " selected" : ""}`}
                style={{ borderLeftColor: priorityColor(item.priority) }}
                onClick={() => onSelect(item.uid)}
              >
                <div className="k-id">{`${item.ref.id} · ${item.project}`}</div>
                <div>{item.title}</div>
                {(item.priority || cardProgress) && (
                  <div className="k-footer">
                    {item.priority && (
                      <span className="prio-badge" style={{ background: priorityColor(item.priority) }}>
                        {vocab("priority", item.priority)}
                      </span>
                    )}
                    {cardProgress && <ProgressPie progress={cardProgress} />}
                  </div>
                )}
              </button>
            );
          })}
        </section>
      ))}
    </div>
  );
}
