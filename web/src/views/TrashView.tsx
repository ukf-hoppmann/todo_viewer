import { useState } from "react";
import type { SourceStatus } from "../api/client";
import { usePurgeItem, useRestoreItem, useTrash } from "../api/queries";
import { Modal } from "../components/Modal";
import { groupTrash } from "../domain/editing";
import { filterItems, type Item, toItems } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import { useUiState } from "../state/useUiStateStore";

interface TrashViewProps {
  sources: SourceStatus[];
}

const NOTHING_HIDDEN: ReadonlySet<string> = new Set();

/** Deleted items of the projects ticked in the sidebar, cut by its search; restore or purge them with their descendants. */
export function TrashView({ sources }: TrashViewProps) {
  const i18n = useI18n();
  const { t, vocab } = i18n;
  const usable = sources.filter((s) => !s.problem);
  const results = useTrash(usable.map((s) => s.id));
  const restore = useRestoreItem();
  const purge = usePurgeItem();
  const { state } = useUiState();
  const [purging, setPurging] = useState<Item | null>(null);
  const items = filterItems(toItems(results.flatMap((r) => r.data ?? [])), {
    hiddenProjects: state.hiddenProjects,
    hiddenStatuses: NOTHING_HIDDEN,
    hiddenPriorities: NOTHING_HIDDEN,
    search: state.search,
  });
  const groups = groupTrash(items);
  const error = results.find((r) => r.error)?.error ?? restore.error ?? purge.error;
  const address = (item: Item) => ({ sourceId: item.source_id, id: item.id, version: item.version });

  return (
    <div className="view trash-view">
      {error && (
        <div className="field-error" role="alert">
          {t("err.generic", { e: describeError(i18n, error) })}
        </div>
      )}
      {groups.length === 0 && !results.some((r) => r.isLoading) && <p className="empty-hint">{t("trash.empty")}</p>}
      {groups.map(({ project, items: trashed }) => (
        <section key={project} className="project-group" aria-label={project}>
          <div className="project-title">{`${project} (${trashed.length})`}</div>
          {trashed.map((item) => (
            <div key={item.key} className="trash-row">
              <span className="node-type">{vocab("type", item.type)}</span>
              <span className="trash-title">{`${item.id} — ${item.title}`}</span>
              <span className="trash-meta">{t("trash.deletedOn", { date: item.deleted ?? "" })}</span>
              <button className="btn small" disabled={restore.isPending} onClick={() => restore.mutate(address(item))}>
                {t("trash.restore")}
              </button>
              <button className="btn small danger" onClick={() => setPurging(item)}>
                {t("trash.purge")}
              </button>
            </div>
          ))}
        </section>
      ))}
      {purging && (
        <Modal labelledBy="purge-title" onDismiss={() => setPurging(null)}>
          <h3 id="purge-title">{t("trash.purgeTitle", { id: purging.id, title: purging.title })}</h3>
          <p>{t("trash.purgeText")}</p>
          <div className="modal-actions">
            <button className="btn" onClick={() => setPurging(null)}>
              {t("cancel")}
            </button>
            <button
              className="btn danger"
              disabled={purge.isPending}
              onClick={() => purge.mutate(address(purging), { onSettled: () => setPurging(null) })}
            >
              {t("trash.purgeConfirm")}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
