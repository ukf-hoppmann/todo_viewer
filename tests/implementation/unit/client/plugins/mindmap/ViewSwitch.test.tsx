import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { flushUiState } from "../../../../../../client/src/core/ui-state/uiState";
import { plugin } from "../../../../../../client/src/plugins/mindmap";
import { ViewSwitch } from "../../../../../../client/src/plugins/mindmap/ViewSwitch";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

async function renderSwitch(documents: Record<string, Record<string, unknown>> = {}) {
	const backend = fakeMindmapBackend({ documents });
	await renderWorkspace(<ViewSwitch />, { backend });
	return backend;
}
const stored = async (backend: Awaited<ReturnType<typeof renderSwitch>>) => {
	await flushUiState(backend.store);
	return backend.documents.get("mindmap") as { view?: string } | undefined;
};
const pressed = (value: string) => screen.getByTestId(ids.viewOption(value)).getAttribute("aria-pressed");

describe("ViewSwitch: the sidebar section for the view of the mind map", () => {
	it("offers the single and the overall view, the single view at the start", async () => {
		await renderSwitch();

		const section = await screen.findByTestId(ids.viewSwitch);
		expect(section.textContent).toContain("Einzeln");
		expect(section.textContent).toContain("Gesamt");
		expect(pressed("single")).toBe("true");
		expect(pressed("all")).toBe("false");
	});

	it("switches to the overall view and keeps the choice in the UI state of the server", async () => {
		const backend = await renderSwitch();
		await screen.findByTestId(ids.viewSwitch);

		fireEvent.click(screen.getByTestId(ids.viewOption("all")));

		await waitFor(async () => expect((await stored(backend))?.view).toBe("all"));
		expect(pressed("all")).toBe("true");
		expect(pressed("single")).toBe("false");
	});

	it("shows a stored choice and switches back to the single view", async () => {
		const backend = await renderSwitch({ mindmap: { view: "all" } });
		await screen.findByTestId(ids.viewSwitch);
		await waitFor(() => expect(pressed("all")).toBe("true"));

		fireEvent.click(screen.getByTestId(ids.viewOption("single")));

		await waitFor(async () => expect((await stored(backend))?.view).toBe("single"));
	});

	it("does not clear the choice when the pressed button is pressed again", async () => {
		await renderSwitch({ mindmap: { view: "all" } });
		await screen.findByTestId(ids.viewSwitch);
		await waitFor(() => expect(pressed("all")).toBe("true"));

		fireEvent.click(screen.getByTestId(ids.viewOption("all")));

		expect(pressed("all")).toBe("true");
	});

	it("is contributed to the sidebar of the mind map page", () => {
		expect(plugin.contributions).toContainEqual(expect.objectContaining({ slot: "core.sidebar-sections", name: "view", when: ["mindmap/main"] }));
	});
});
