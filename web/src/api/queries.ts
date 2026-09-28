// TanStack Query hooks: the only place components talk to the API.
import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ItemFields, type Schemas, unwrap } from "./client";

export const POLL_INTERVAL_MS = 5000;

const keys = {
  backlog: ["backlog"] as const,
  uiState: ["ui-state"] as const,
  folders: (path: string | null) => ["folders", path] as const,
  document: (sourceId: string, itemId: string, name: string) => ["document", sourceId, itemId, name] as const,
  trash: (sourceId: string) => ["trash", sourceId] as const,
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

export function useCreateItem() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (body: Schemas["ItemCreateIn"]) => unwrap(api.POST("/api/v2/items", { body })),
    onSettled: () => client.invalidateQueries({ queryKey: keys.backlog }),
  });
}

/** The trash of every given source. */
export function useTrash(sourceIds: readonly string[]) {
  return useQueries({
    queries: sourceIds.map((sourceId) => ({
      queryKey: keys.trash(sourceId),
      queryFn: () => unwrap(api.GET("/api/v2/trash", { params: { query: { source_id: sourceId } } })),
    })),
  });
}

type ItemAddress = { sourceId: string; id: string; version: string };

function useTrashMutation<T extends ItemAddress>(call: (args: T) => Promise<unknown>) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: call,
    onSettled: () => {
      void client.invalidateQueries({ queryKey: keys.backlog });
      void client.invalidateQueries({ queryKey: ["trash"] });
    },
  });
}

/** Moves an item to the trash; `cascade` includes its descendants (otherwise has_children lists them). */
export function useDeleteItem() {
  return useTrashMutation(({ sourceId, id, version, cascade }: ItemAddress & { cascade: boolean }) =>
    unwrap(api.DELETE("/api/v2/items/{source_id}/{item_id}", { params: { path: { source_id: sourceId, item_id: id }, query: { version, cascade } } })),
  );
}

export function useRestoreItem() {
  return useTrashMutation(({ sourceId, id, version }: ItemAddress) =>
    unwrap(api.POST("/api/v2/trash/{source_id}/{item_id}/restore", { params: { path: { source_id: sourceId, item_id: id } }, body: { version } })),
  );
}

export function usePurgeItem() {
  return useTrashMutation(({ sourceId, id, version }: ItemAddress) =>
    unwrap(api.DELETE("/api/v2/trash/{source_id}/{item_id}", { params: { path: { source_id: sourceId, item_id: id }, query: { version } } })),
  );
}

function useDocumentMutation<T extends { sourceId: string; itemId: string }>(call: (args: T) => Promise<Schemas["DocumentOut"]>) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: call,
    onSuccess: (doc, { sourceId, itemId }) => client.setQueryData(keys.document(sourceId, itemId, doc.name), doc),
    onSettled: () => client.invalidateQueries({ queryKey: keys.backlog }),
  });
}

/** Appends a dated notes entry (the first one creates the notes document). */
export function useAppendNotes() {
  return useDocumentMutation(({ sourceId, itemId, body }: { sourceId: string; itemId: string; body: Schemas["NotesEntryIn"] }) =>
    unwrap(api.POST("/api/v2/items/{source_id}/{item_id}/notes", { params: { path: { source_id: sourceId, item_id: itemId } }, body })),
  );
}

/** Replaces a notes or spec document in `version` with the whole new text, or creates it (`version` null). */
export function useWriteDocument() {
  return useDocumentMutation(
    ({ sourceId, itemId, name, content, version }: { sourceId: string; itemId: string; name: string; content: string; version: string | null }) =>
      unwrap(
        api.PUT("/api/v2/items/{source_id}/{item_id}/documents/{name}", {
          params: { path: { source_id: sourceId, item_id: itemId, name } },
          body: { content, version },
        }),
      ),
  );
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

/** The current content of a document (e.g. after a version conflict). */
export async function fetchDocument(sourceId: string, itemId: string, name: string) {
  return unwrap(
    api.GET("/api/v2/items/{source_id}/{item_id}/documents/{name}", { params: { path: { source_id: sourceId, item_id: itemId, name } } }),
  );
}

/** The current state of one item (e.g. after a version conflict). */
export async function fetchItem(sourceId: string, itemId: string) {
  return unwrap(api.GET("/api/v2/items/{source_id}/{item_id}", { params: { path: { source_id: sourceId, item_id: itemId } } }));
}

export async function fetchUiState(): Promise<Record<string, unknown>> {
  return unwrap(api.GET("/api/v2/ui-state"));
}

export async function saveUiState(state: Record<string, unknown>): Promise<void> {
  await unwrap(api.PUT("/api/v2/ui-state", { body: state }));
}
