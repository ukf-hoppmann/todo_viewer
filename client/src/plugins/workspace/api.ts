import { createPluginApi } from "../../core";
import type { components } from "../../shared";

export type Project = components["schemas"]["ProjectOut"];
export type FolderListing = components["schemas"]["FolderListingOut"];
export type SyncDirection = Project["sync_direction"];
export type CreateProjectBody = components["schemas"]["WorkspaceCreateProjectBody"];
export type LinkRole = components["schemas"]["LinkedElement"]["role"];
export type LinkedElement = components["schemas"]["LinkedElement"];
export type LinksOut = components["schemas"]["LinksOut"];
export type ElementOut = components["schemas"]["ElementOut"];
export type TrashedElement = components["schemas"]["TrashedElement"];
export type DeleteResult = components["schemas"]["DeleteResult"];
export type SyncStatus = components["schemas"]["SyncStatus"];
export type SyncPreview = components["schemas"]["Preview"];
export type SyncConflict = components["schemas"]["ConflictOut"];
export type SyncTransfer = components["schemas"]["TransferOut"];
export type SyncResult = components["schemas"]["SyncResult"];
export type SyncChoice = components["schemas"]["Decision"]["choice"];
export type SyncSettings = components["schemas"]["SyncSettingsOut"];
export type UpdateProjectBody = components["schemas"]["WorkspaceUpdateProjectBody"];

/**
 * The API of the plugin (`workspace.api`): projects and the folder browser. A change of a project invalidates
 * the tag `Projects`; the server event `workspace.project.changed` does the same for changes from elsewhere.
 */
export const workspaceApi = createPluginApi(
	"workspace",
	(build) => ({
		listProjects: build.query<Project[], void>({
			query: () => "workspace/projects",
			providesTags: ["Projects"],
		}),
		createProject: build.mutation<Project, CreateProjectBody>({
			query: (body) => ({ url: "workspace/projects", method: "POST", body }),
			invalidatesTags: ["Projects"],
		}),
		updateProject: build.mutation<Project, UpdateProjectBody & { uid: string }>({
			query: ({ uid, ...body }) => ({ url: `workspace/projects/${uid}`, method: "PUT", body }),
			invalidatesTags: ["Projects"],
		}),
		moveProject: build.mutation<Project[], { uid: string; version: number; position: number }>({
			query: ({ uid, ...body }) => ({ url: `workspace/projects/${uid}/move`, method: "POST", body }),
			invalidatesTags: ["Projects"],
		}),
		removeProject: build.mutation<{ trashed: number }, { uid: string; version: number; confirm?: boolean }>({
			query: ({ uid, version, confirm }) => ({
				url: `workspace/projects/${uid}`,
				method: "DELETE",
				params: confirm ? { version, confirm } : { version },
			}),
			invalidatesTags: ["Projects"],
		}),
		listLinks: build.query<LinksOut, string>({
			query: (uid) => `workspace/elements/${uid}/links`,
			providesTags: ["Links"],
		}),
		addLink: build.mutation<LinkedElement, { from_uid: string; to_uid: string; role: LinkRole }>({
			query: (body) => ({ url: "workspace/links", method: "POST", body }),
			invalidatesTags: ["Links"],
		}),
		removeLink: build.mutation<{ removed: boolean }, string>({
			query: (uid) => ({ url: `workspace/links/${uid}`, method: "DELETE" }),
			invalidatesTags: ["Links"],
		}),
		searchElements: build.query<ElementOut[], string>({
			query: (query) => ({ url: "workspace/elements", params: { query } }),
		}),
		deleteElement: build.mutation<DeleteResult, { uid: string; version: number; cascade?: boolean }>({
			query: ({ uid, version, cascade }) => ({
				url: `workspace/elements/${uid}`,
				method: "DELETE",
				params: cascade ? { version, cascade } : { version },
			}),
			invalidatesTags: ["Trash", "Links"],
		}),
		listTrash: build.query<TrashedElement[], { projects: string[]; query: string }>({
			query: ({ projects, query }) => ({ url: "workspace/trash", params: { projects: projects.join(","), query } }),
			providesTags: ["Trash"],
		}),
		restoreElements: build.mutation<{ uids: string[] }, string[]>({
			query: (uids) => ({ url: "workspace/trash/restore", method: "POST", body: { uids } }),
			invalidatesTags: ["Trash", "Links"],
		}),
		purgeElements: build.mutation<{ uids: string[] }, string[]>({
			query: (uids) => ({ url: "workspace/trash/purge", method: "POST", body: { uids } }),
			invalidatesTags: ["Trash", "Links"],
		}),
		getSyncStatus: build.query<SyncStatus, string>({
			query: (project) => `core/sync/${project}/status`,
			providesTags: (_result, _error, project) => [{ type: "Sync", id: project }],
		}),
		getSyncPreview: build.query<SyncPreview, { project: string; direction: SyncDirection }>({
			query: ({ project, direction }) => ({ url: `core/sync/${project}/preview`, params: { direction } }),
			keepUnusedDataFor: 0,
		}),
		executeSync: build.mutation<
			SyncResult,
			{ project: string; token: string; direction: SyncDirection; decisions: components["schemas"]["Decision"][]; delete_missing: boolean }
		>({
			query: ({ project, ...body }) => ({ url: `core/sync/${project}/execute`, method: "POST", body }),
			invalidatesTags: (_result, _error, { project }) => [{ type: "Sync", id: project }, "Projects", "Trash", "Links"],
		}),
		getSyncSettings: build.query<SyncSettings, void>({
			query: () => "core/settings/sync",
			providesTags: ["SyncSettings"],
		}),
		updateSyncSettings: build.mutation<SyncSettings, { auto_sync_interval_seconds: number }>({
			query: (body) => ({ url: "core/settings/sync", method: "PUT", body }),
			invalidatesTags: ["SyncSettings"],
		}),
		browseFolders: build.query<FolderListing, string | undefined>({
			query: (path) => ({ url: "workspace/folders", params: path ? { path } : undefined }),
		}),
	}),
	{ tagTypes: ["Projects", "Links", "Trash", "Sync", "SyncSettings"] },
);

export const {
	useListProjectsQuery,
	useCreateProjectMutation,
	useUpdateProjectMutation,
	useMoveProjectMutation,
	useRemoveProjectMutation,
	useBrowseFoldersQuery,
	useListLinksQuery,
	useAddLinkMutation,
	useRemoveLinkMutation,
	useSearchElementsQuery,
	useDeleteElementMutation,
	useListTrashQuery,
	useRestoreElementsMutation,
	usePurgeElementsMutation,
	useGetSyncStatusQuery,
	useGetSyncPreviewQuery,
	useExecuteSyncMutation,
	useGetSyncSettingsQuery,
	useUpdateSyncSettingsMutation,
} = workspaceApi;

/** The text the server gave for an error of a request, if it gave one. */
export function errorMessage(error: unknown, fallback: string): string {
	const data = (error as { data?: { message?: unknown } } | undefined)?.data;
	return typeof data?.message === "string" ? data.message : fallback;
}

/** The code the server gave for an error of a request (`project_not_empty`, …). */
export function errorCode(error: unknown): string | undefined {
	const data = (error as { data?: { code?: unknown } } | undefined)?.data;
	return typeof data?.code === "string" ? data.code : undefined;
}
