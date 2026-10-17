import type { components } from "../../shared";
import { createPluginApi } from "../api/createPluginApi";

export type UiState = components["schemas"]["UiState"];
export type UiStateDocument = UiState["document"];

/**
 * The API of the core with its own cache (`core.api`): the UI state per owner, `GET/PUT /api/core/ui-state/{owner}`.
 * One JSON document per owner replaces the storage of the browser (scope client 4).
 */
export const coreApi = createPluginApi("core", (build) => ({
	getUiState: build.query<UiState, string>({
		query: (owner) => `core/ui-state/${owner}`,
	}),
	putUiState: build.mutation<UiState, { owner: string; document: UiStateDocument }>({
		query: ({ owner, document }) => ({ url: `core/ui-state/${owner}`, method: "PUT", body: { document } }),
	}),
}));

export const { useGetUiStateQuery } = coreApi;
