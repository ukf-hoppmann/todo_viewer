import { useState } from "react";
import type { SourceStatus } from "../api/client";
import { usePurgeItem, useRestoreItem, useTrash } from "../api/queries";
import { IconButton } from "../components/IconButton";
import { Modal } from "../components/Modal";
import { groupTrash, topmostSelected } from "../domain/editing";
import { filterItems, type Item, toItems } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import { useUiState } from "../state/useUiStateStore";

interface TrashViewProps {
  sources: SourceStatus[];
}

const NOTHING_HIDDEN: ReadonlySet<string> = new Set();

/** Deleted items of the projects ticked in the sidebar, cut by its search; restore or purge them with their descendants,
 *  one at a time or the ticked ones together. */
export function TrashView({ sources }: TrashViewProps) {
  const i18n = useI18n();
  const { t, vocab } = i18n;
  const usable = sources.filter((s) => !s.problem);
  const results = useTrash(usable.map((s) => s.id));
  const restore = useRestoreItem();
  const purge = usePurgeItem();
  const { state } = useUiState();
  const [chosen, setChosen] = useState<ReadonlySet<string>>(new Set());
  // The items the confirmation is open for: one row, or the ticked ones.
  const [purging, setPurging] = useState<Item[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState<string[]>([]);
  const items = filterItems(toItems(results.flatMap((r) => r.data ?? [])), {
    hiddenProjects: state.hiddenProjects,
    hiddenStatuses: NOTHING_HIDDEN,
    hiddenPriorities: NOTHING_HIDDEN,
    search: state.search,
  });
  const groups = groupTrash(items);
  // Ticks of items that left the view (restored, purged, filtered out) do not count.
  const ticked = items.filter((i) => chosen.has(i.key));
  const allTicked = items.length > 0 && ticked.length === items.length;
  const error = results.find((r) => r.error)?.error ?? restore.error ?? purge.error;
  const address = (item: Item) => ({ sourceId: item.source_id, id: item.id, version: item.version });

  const toggle = (key: string) =>
    setChosen((prev) => {
      const next = new Set(prev);
      if (!next.delete(key)) next.add(key);
      return next;
    });

  /** Runs the action one item after the other, so a failure of one leaves the others done; reports the failed ones. */
  const runAll = async (targets: readonly Item[], action: (item: Item) => Promise<unknown>) => {
    setBusy(true);
    const errors: string[] = [];
    for (const item of topmostSelected(targets, new Set(targets.map((i) => i.key)))) {
      try {
        await action(item);
      } catch (e) {
        errors.push(`${item.id} (${describeError(i18n, e)})`);
      }
    }
    setFailed(errors);
    setChosen(new Set());
    setBusy(false);
  };

  return (
    <div className="view trash-view">
      {error && failed.length === 0 && (
        <div className="field-error" role="alert">
          {t("err.generic", { e: describeError(i18n, error) })}
        </div>
      )}
      {failed.length > 0 && (
        <div className="field-error" role="alert">
          {t("trash.failed", { list: failed.join(", ") })}
        </div>
      )}
      {groups.length === 0 && !results.some((r) => r.isLoading) && <p className="empty-hint">{t("trash.empty")}</p>}
      {items.length > 0 && (
        <div className="trash-bar">
          <input
            type="checkbox"
            aria-label={t("trash.selectAll")}
            title={t("trash.selectAll")}
            checked={allTicked}
            ref={(el) => {
              if (el) el.indeterminate = ticked.length > 0 && !allTicked;
            }}
            onChange={() => setChosen(allTicked ? new Set() : new Set(items.map((i) => i.key)))}
          />
          <span className="hint">{t("trash.selected", { n: ticked.length })}</span>
          <IconButton
            icon="restore"
            label={t("trash.restoreSelected")}
            disabled={ticked.length === 0 || busy}
            onClick={() => void runAll(ticked, (item) => restore.mutateAsync(address(item)))}
          />
          <IconButton icon="trash" label={t("trash.purgeSelected")} variant="danger" disabled={ticked.length === 0 || busy} onClick={() => setPurging(ticked)} />
        </div>
      )}
      {groups.map(({ project, items: trashed }) => (
        <section key={project} className="project-group" aria-label={project}>
          <div className="project-title">{`${project} (${trashed.length})`}</div>
          {trashed.map((item) => (
            <div key={item.key} className="trash-row">
              <input type="checkbox" aria-label={t("trash.select", { id: item.id })} checked={chosen.has(item.key)} onChange={() => toggle(item.key)} />
              <span className="node-type">{vocab("type", item.type)}</span>
              <span className="trash-title">{`${item.id} — ${item.title}`}</span>
              <span className="trash-meta">{t("trash.deletedOn", { date: item.deleted ?? "" })}</span>
              <IconButton icon="restore" label={t("trash.restore")} disabled={restore.isPending || busy} onClick={() => restore.mutate(address(item))} />
              <IconButton icon="trash" label={t("trash.purge")} variant="danger" disabled={busy} onClick={() => setPurging([item])} />
            </div>
          ))}
        </section>
      ))}
      {purging && (
        <Modal labelledBy="purge-title" onDismiss={() => setPurging(null)}>
          {purging.length === 1 ? (
            <>
              <h3 id="purge-title">{t("trash.purgeTitle", { id: purging[0]!.id, title: purging[0]!.title })}</h3>
              <p>{t("trash.purgeText")}</p>
            </>
          ) : (
            <>
              <h3 id="purge-title">{t("trash.purgeSelectedTitle", { n: purging.length })}</h3>
              <p>{t("trash.purgeSelectedText")}</p>
            </>
          )}
          <div className="modal-actions">
            <button className="btn" onClick={() => setPurging(null)}>
              {t("cancel")}
            </button>
            <button
              className="btn danger"
              disabled={busy}
              onClick={() => {
                const targets = purging;
                setPurging(null);
                void runAll(targets, (item) => purge.mutateAsync(address(item)));
              }}
            >
              {t("trash.purgeConfirm")}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
