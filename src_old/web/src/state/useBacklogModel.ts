import { useMemo } from "react";
import type { SourceStatus } from "../api/client";
import { useBacklog } from "../api/queries";
import { filterItems, filterOptions, type FilterOptions, indexByUid, type Item, toItems, type Uid } from "../domain/model";
import { usePollingPaused } from "./pollingPause";
import type { UiState } from "./uiState";

export interface BacklogModel {
  /** All items, unfiltered (progress, parents and children are computed over these). */
  items: Item[];
  byUid: Map<Uid, Item>;
  sources: SourceStatus[];
  /** Items passing the current filters. */
  visible: Item[];
  options: FilterOptions;
  isLoading: boolean;
  error: unknown;
}

const EMPTY: never[] = [];

export function useBacklogModel(ui: UiState): BacklogModel {
  const query = useBacklog(usePollingPaused());
  const data = query.data;

  const items = useMemo(() => (data ? toItems(data.items) : EMPTY), [data]);
  const sources = data?.sources ?? EMPTY;
  const byUid = useMemo(() => indexByUid(items), [items]);
  const options = useMemo(() => filterOptions(items, sources), [items, sources]);
  const visible = useMemo(
    () => filterItems(items, ui),
    [items, ui.hiddenProjects, ui.hiddenStatuses, ui.hiddenPriorities, ui.search], // eslint-disable-line react-hooks/exhaustive-deps
  );

  return { items, byUid, sources, visible, options, isLoading: query.isLoading, error: query.error };
}
