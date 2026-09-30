// TanStack Query hooks: the only place components talk to the API.
import { type QueryClient, useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type ItemFields, type Schemas, unwrap } from "./client";

export const POLL_INTERVAL_MS = 5000;

const keys = {
  backlog: ["backlog"] as const,
  uiState: ["ui-state"] as const,
  storage: ["storage"] as const,
  syncStatus: ["sync-status"] as const,
  folders: (path: string | null) => ["folders", path] as const,
  document: (sourceId: string, itemId: string, name: string) => ["document", sourceId, itemId, name] as const,
  trash: (sourceId: string) => ["trash", sourceId] as const,
};

const fetchBacklog = () => unwrap(api.GET("/api/v2/backlog"));

/** All sources and items. Polls; structural sharing keeps unchanged data referentially stable. */
export function useBacklog(paused: boolean) {
  return useQuery({
    queryKey: keys.backlog,
    queryFn: fetchBacklog,
    refetchInterval: paused ? false : POLL_INTERVAL_MS,
  });
}

/** The projects, from the same data the polling query keeps fresh (no request of its own while that one runs). */
export function useSourceList() {
  return useQuery({ queryKey: keys.backlog, queryFn: fetchBacklog, select: (backlog) => backlog.sources });
}

/**
 * Which side of each project with a mirror changed since its last sync. Reading it makes the server read both sides,
 * so it is asked for on load, on window focus, by hand (`refetch`) and after a sync or change of a project, never on a timer.
 */
export function useSyncStatuses() {
  return useQuery({ queryKey: keys.syncStatus, queryFn: () => unwrap(api.GET("/api/v2/sync-status")) });
}

/** After anything that changes a project or its sides: the projects and their sync state are read again. */
function refreshSources(client: QueryClient) {
  void client.invalidateQueries({ queryKey: keys.backlog });
  void client.invalidateQueries({ queryKey: keys.syncStatus });
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

/** Reopens closed items one after the other (top-down, as parent_closed lists them) by setting In progress. */
export function useReopenItems() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async ({ sourceId, ids }: { sourceId: string; ids: readonly string[] }) => {
      for (const id of ids) {
        const path = { source_id: sourceId, item_id: id };
        const { version } = await unwrap(api.GET("/api/v2/items/{source_id}/{item_id}", { params: { path } }));
        await unwrap(api.PATCH("/api/v2/items/{source_id}/{item_id}", { params: { path }, body: { version, fields: { status: "In progress" }, resolution: null } }));
      }
    },
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

/** Changes an item's type. It gets a new id and its documents move, so backlog, trash and documents reload. */
export function useRetypeItem() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ sourceId, id, version, type }: ItemAddress & { type: string }) =>
      unwrap(api.POST("/api/v2/items/{source_id}/{item_id}/retype", { params: { path: { source_id: sourceId, item_id: id } }, body: { version, type } })),
    onSettled: () => {
      void client.invalidateQueries({ queryKey: keys.backlog });
      void client.invalidateQueries({ queryKey: ["trash"] });
      void client.invalidateQueries({ queryKey: ["document"] });
    },
  });
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

export type Backend = Schemas["SourceIn"]["backend"] & string;

export interface SaveSourceRequest {
  /** null = add a new project. */
  id: string | null;
  project: string;
  /** Markdown projects: the backlog folder. Unused for database projects. */
  path: string;
  /** Only a new project chooses its backend; a change of an existing one goes through useSwitchBackend. */
  backend?: Backend;
  /** Database projects: the folder their markdown files are synced with ("" = none). */
  syncPath?: string;
  /** The other side to keep as a mirror; unset leaves it as it is. */
  mirror?: Schemas["SourceIn"]["mirror"];
}

export function useSaveSource() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, path, project, backend, syncPath, mirror }: SaveSourceRequest) => {
      const body = { path, project, backend, sync_path: syncPath, mirror };
      return id
        ? unwrap(api.PUT("/api/v2/sources/{source_id}", { params: { path: { source_id: id } }, body }))
        : unwrap(api.POST("/api/v2/sources", { body }));
    },
    onSuccess: () => refreshSources(client),
  });
}

export interface SyncRequest {
  sourceId: string;
  direction: Schemas["SyncIn"]["direction"];
  /** false asks for a preview, true carries the sync out (with the token of the preview). */
  confirm: boolean;
  token?: string;
  deleteMissing?: boolean;
  language: "de" | "en";
}

function runSync({ sourceId, direction, confirm, token, deleteMissing, language }: SyncRequest) {
  return unwrap(
    api.POST("/api/v2/sources/{source_id}/sync", {
      params: { path: { source_id: sourceId } },
      body: { direction, confirm, token, delete_missing: deleteMissing ?? false, language },
    }),
  );
}

/** A preview (`confirm` false) or the sync itself; a sync changes the items, so the backlog reloads. */
export function useSyncSource() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: runSync,
    onSuccess: (result) => {
      if (result.executed) refreshSources(client);
    },
  });
}

/** Syncs (with the token of the confirmed preview) and then moves the project to `backend`. */
export function useSwitchBackend() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: async ({ backend, ...sync }: Omit<SyncRequest, "confirm"> & { backend: Backend }) => {
      await runSync({ ...sync, confirm: true });
      return unwrap(api.PUT("/api/v2/sources/{source_id}", { params: { path: { source_id: sync.sourceId } }, body: { path: "", backend } })); // the server takes the folder from the stored project
    },
    onSettled: () => refreshSources(client),
  });
}

export function useRemoveSource() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => unwrap(api.DELETE("/api/v2/sources/{source_id}", { params: { path: { source_id: id } } })),
    onSettled: () => refreshSources(client),
  });
}

/** Type, location and schema version of the central database; read once, it does not change while the server runs. */
export function useStorageInfo() {
  return useQuery({
    queryKey: keys.storage,
    queryFn: () => unwrap(api.GET("/api/v2/storage")),
    staleTime: Infinity,
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
