import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { flushUiState } from "../../../../../../client/src/core/ui-state/uiState";
import { MapFilters } from "../../../../../../client/src/plugins/mindmap/MapFilters";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

async function renderFilters(documents: Record<string, Record<string, unknown>> = {}) {
	const backend = fakeMindmapBackend({ documents });
	await renderWorkspace(<MapFilters />, { backend });
	return backend;
}
const stored = async (backend: Awaited<ReturnType<typeof renderFilters>>) => {
	await flushUiState(backend.store);
	return backend.documents.get("mindmap") as { hiddenStates?: string[]; showUnassigned?: boolean } | undefined;
};

describe("MapFilters: the sidebar section of the mind map", () => {
	it("offers the four states, all shown at the start, and the switch for the side view", async () => {
		await renderFilters();

		const section = await screen.findByTestId(ids.stateFilter);
		expect(section.textContent).toContain("Idee");
		for (const state of ["idea", "planned", "in_progress", "done"]) {
			expect((screen.getByTestId(sharedTestIds.filterOption(state)) as HTMLInputElement).checked).toBe(true);
		}
		expect((screen.getByTestId(ids.unassignedSwitch) as HTMLInputElement).checked).toBe(true);
	});

	it("keeps a hidden state in the UI state of the server", async () => {
		const backend = await renderFilters();
		await screen.findByTestId(ids.stateFilter);

		fireEvent.click(screen.getByTestId(sharedTestIds.filterOption("done")));

		await waitFor(async () => expect((await stored(backend))?.hiddenStates).toEqual(["done"]));
		expect((screen.getByTestId(sharedTestIds.filterOption("done")) as HTMLInputElement).checked).toBe(false);
	});

	it("switches the side view off and keeps that", async () => {
		const backend = await renderFilters({ mindmap: { hiddenStates: ["idea"] } });
		await screen.findByTestId(ids.stateFilter);
		await waitFor(() => expect((screen.getByTestId(sharedTestIds.filterOption("idea")) as HTMLInputElement).checked).toBe(false));

		fireEvent.click(screen.getByTestId(ids.unassignedSwitch));

		await waitFor(async () => expect((await stored(backend))?.showUnassigned).toBe(false));
	});
});
