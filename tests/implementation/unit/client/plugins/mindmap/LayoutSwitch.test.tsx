import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { flushUiState } from "../../../../../../client/src/core/ui-state/uiState";
import { plugin } from "../../../../../../client/src/plugins/mindmap";
import { LayoutSwitch } from "../../../../../../client/src/plugins/mindmap/LayoutSwitch";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

async function renderSwitch(documents: Record<string, Record<string, unknown>> = {}) {
	const backend = fakeMindmapBackend({ documents });
	await renderWorkspace(<LayoutSwitch />, { backend });
	return backend;
}
const stored = async (backend: Awaited<ReturnType<typeof renderSwitch>>) => {
	await flushUiState(backend.store);
	return backend.documents.get("mindmap") as { layout?: string } | undefined;
};
const pressed = (value: string) => screen.getByTestId(ids.layoutOption(value)).getAttribute("aria-pressed");

describe("LayoutSwitch: the sidebar section for the arrangement of the mind map", () => {
	it("offers the tree to the side and the round arrangement, the tree to the side at the start", async () => {
		await renderSwitch();

		const section = await screen.findByTestId(ids.layoutSwitch);
		expect(section.textContent).toContain("Zur Seite");
		expect(section.textContent).toContain("Rund");
		expect(pressed("side")).toBe("true");
		expect(pressed("round")).toBe("false");
	});

	it("switches to round and keeps the choice in the UI state of the server", async () => {
		const backend = await renderSwitch();
		await screen.findByTestId(ids.layoutSwitch);

		fireEvent.click(screen.getByTestId(ids.layoutOption("round")));

		await waitFor(async () => expect((await stored(backend))?.layout).toBe("round"));
		expect(pressed("round")).toBe("true");
		expect(pressed("side")).toBe("false");
	});

	it("shows a stored choice and switches back to the side", async () => {
		const backend = await renderSwitch({ mindmap: { layout: "round" } });
		await screen.findByTestId(ids.layoutSwitch);
		await waitFor(() => expect(pressed("round")).toBe("true"));

		fireEvent.click(screen.getByTestId(ids.layoutOption("side")));

		await waitFor(async () => expect((await stored(backend))?.layout).toBe("side"));
	});

	it("does not clear the choice when the pressed button is pressed again", async () => {
		await renderSwitch({ mindmap: { layout: "round" } });
		await screen.findByTestId(ids.layoutSwitch);
		await waitFor(() => expect(pressed("round")).toBe("true"));

		fireEvent.click(screen.getByTestId(ids.layoutOption("round")));

		expect(pressed("round")).toBe("true");
	});

	it("is contributed to the sidebar of the mind map page", () => {
		expect(plugin.contributions).toContainEqual(expect.objectContaining({ slot: "core.sidebar-sections", name: "layout", when: ["mindmap/main"] }));
	});
});
