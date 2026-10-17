import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { flushUiState } from "../../../../../../client/src/core/ui-state/uiState";
import { SearchSection } from "../../../../../../client/src/plugins/workspace/SearchSection";
import { workspaceTestIds as ids } from "../../../../../../client/src/plugins/workspace/testIds";
import { expectPersisted, fakeWorkspaceBackend } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

describe("SearchSection", () => {
	it("shows the typed text at once and keeps it in the UI state", async () => {
		const backend = fakeWorkspaceBackend();
		await renderWorkspace(<SearchSection />, { backend });

		fireEvent.change(screen.getByTestId(ids.searchInput), { target: { value: "sync" } });
	
		expect((screen.getByTestId(ids.searchInput) as HTMLInputElement).value).toBe("sync");
		await expectPersisted(backend, flushUiState, waitFor, { search: "sync" });
	});

	it("starts with the stored text and clears it", async () => {
		const backend = fakeWorkspaceBackend({ documents: { workspace: { search: "alt" } } });
		await renderWorkspace(<SearchSection />, { backend });
		await waitFor(() => expect((screen.getByTestId(ids.searchInput) as HTMLInputElement).value).toBe("alt"));

		fireEvent.click(screen.getByTestId(ids.searchClear));
	
		expect((screen.getByTestId(ids.searchInput) as HTMLInputElement).value).toBe("");
		await expectPersisted(backend, flushUiState, waitFor, { search: "" });
		expect(screen.queryByTestId(ids.searchClear)).toBeNull();
	});
});
