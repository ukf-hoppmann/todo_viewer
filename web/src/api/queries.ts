// TanStack Query hooks: the only place components talk to the API.
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ItemFields, unwrap } from "./client";

export const POLL_INTERVAL_MS = 5000;

const keys = {
  backlog: ["backlog"] as const,
  uiState: ["ui-state"] as const,
  folders: (path: string | null) => ["folders", path] as const,
  document: (sourceId: string, itemId: string, name: string) => ["document", sourceId, itemId, name] as const,
};

/** All sources and items. Polls; structural sharing keeps unchanged data referentially stable. */
export function useBacklog(paused: boolean) {
  return useQuery({
    queryKey: keys.backlog,
    queryFn: () => unwrap(api.GET("/api/v2/backlog")),
    refetchInterval: paused ? false : POLL_INTERVAL_MS,
  });
}

/** An edit of one item; `version` is the one last read, a changed item answers version_conflict. */
export interface EditItemRequest {
  sourceId: string;
  id: string;
  version: string;
  fields: Partial<ItemFields>;
  resolution: string | null;
}

export function useEditItem() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ sourceId, id, ...body }: EditItemRequest) =>
      unwrap(api.PATCH("/api/v2/items/{source_id}/{item_id}", { params: { path: { source_id: sourceId, item_id: id } }, body })),
    onSettled: () => client.invalidateQueries({ queryKey: keys.backlog }),
  });
}

export function useSaveSource() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, path, project }: { id: string | null; path: string; project: string }) =>
      id
        ? unwrap(api.PUT("/api/v2/sources/{source_id}", { params: { path: { source_id: id } }, body: { path, project } }))
        : unwrap(api.POST("/api/v2/sources", { body: { path, project } })),
    onSuccess: () => client.invalidateQueries({ queryKey: keys.backlog }),
  });
}

export function useRemoveSource() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => unwrap(api.DELETE("/api/v2/sources/{source_id}", { params: { path: { source_id: id } } })),
    onSettled: () => client.invalidateQueries({ queryKey: keys.backlog }),
  });
}

export function useFolders(path: string | null, enabled: boolean) {
  return useQuery({
    queryKey: keys.folders(path),
    queryFn: () => unwrap(api.GET("/api/v2/folders", { params: { query: { path } } })),
    enabled,
    placeholderData: (previous) => previous,
  });
}

/** A notes or spec document of an item, addressed by its name. */
export function useDocument(sourceId: string, itemId: string, name: string | null) {
  return useQuery({
    queryKey: keys.document(sourceId, itemId, name ?? ""),
    queryFn: () =>
      unwrap(
        api.GET("/api/v2/items/{source_id}/{item_id}/documents/{name}", {
          params: { path: { source_id: sourceId, item_id: itemId, name: name ?? "" } },
        }),
      ),
    enabled: name !== null,
  });
}

export async function fetchUiState(): Promise<Record<string, unknown>> {
  return unwrap(api.GET("/api/v2/ui-state"));
}

export async function saveUiState(state: Record<string, unknown>): Promise<void> {
  await unwrap(api.PUT("/api/v2/ui-state", { body: state }));
}
