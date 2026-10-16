import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { initI18n } from "../../../../../../client/src/core";
import { StoreProvider } from "../../../../../../client/src/core/store/StoreProvider";
import { flushUiState } from "../../../../../../client/src/core/ui-state/uiState";
import { exampleTestIds } from "../../../../../../client/src/plugins/example";
import WorkbenchPage from "../../../../../../client/src/plugins/example/pages/WorkbenchPage";
import de from "../../../../../../client/src/plugins/example/locales/de.json";
import en from "../../../../../../client/src/plugins/example/locales/en.json";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { fakeUiStateBackend } from "../../../../../helpers/client/fakeUiStateBackend";

async function renderPage(documents: Record<string, Record<string, unknown>> = {}) {
	const backend = fakeUiStateBackend(documents);
	const i18n = await initI18n({ lng: "de" });
	i18n.addResourceBundle("de", "example", de);
	i18n.addResourceBundle("en", "example", en);
	render(
		<I18nextProvider i18n={i18n}>
			<StoreProvider store={backend.store}>
				<WorkbenchPage />
			</StoreProvider>
		</I18nextProvider>,
	);
	return backend;
}

afterEach(cleanup);

describe("WorkbenchPage: tree, detail panel and editor together", () => {
	it("shows the tree, the detail panel of the selected element, and its note as markdown preview", async () => {
		await renderPage();

		expect(screen.getByTestId(sharedTestIds.treeNode("e1"))).toBeTruthy();
		expect(screen.getByTestId(sharedTestIds.detailTitle).textContent).toBe("Epic");
		expect(screen.getByTestId(sharedTestIds.markdownPreview).querySelector("strong")?.textContent).toBe("Beispiel");
		expect(screen.getByTestId(exampleTestIds.workbenchSelected).textContent).toBe("e1");
	});

	it("selects another element and shows its details", async () => {
		await renderPage({ example: { expanded: ["e1"] } });
		await waitFor(() => expect(screen.getByTestId(sharedTestIds.treeNode("s2"))).toBeTruthy());

		fireEvent.click(screen.getByTestId(sharedTestIds.treeNode("s2")));

		expect(screen.getByTestId(sharedTestIds.detailTitle).textContent).toBe("Story zwei");
		expect(screen.getByTestId(sharedTestIds.markdownPreview).querySelector("h2")?.textContent).toBe("Offen");
	});

	it("keeps the open nodes in the UI state of the server", async () => {
		const backend = await renderPage({ example: { expanded: [] } });
		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.treeNode("s1"))).toBeNull());

		fireEvent.click(screen.getByTestId(sharedTestIds.treeToggle("e1")));
		await waitFor(() => expect(screen.getByTestId(sharedTestIds.treeNode("s1"))).toBeTruthy());
		await flushUiState(backend.store);

		expect(backend.documents.get("example")).toEqual({ expanded: ["e1"] });
	});

	it("renames an element in the inline field and shows the new name in the tree and the title", async () => {
		await renderPage();
		const input = screen.getByTestId(sharedTestIds.inlineFieldInput("title"));

		fireEvent.change(input, { target: { value: "Umbenannt" } });
		fireEvent.blur(input);

		await waitFor(() => expect(screen.getByTestId(sharedTestIds.detailTitle).textContent).toBe("Umbenannt"));
		expect(screen.getByTestId(sharedTestIds.treeNode("e1")).textContent).toContain("Umbenannt");
	});

	it("moves an element when it is dropped into another", async () => {
		await renderPage({ example: { expanded: ["e1"] } });
		await waitFor(() => expect(screen.getByTestId(sharedTestIds.treeNode("s2"))).toBeTruthy());
		const target = screen.getByTestId(sharedTestIds.treeNode("s1"));
		Object.defineProperty(target, "getBoundingClientRect", { value: () => ({ top: 0, height: 40 }) });
		const transfer = { setData: () => {}, getData: () => "", effectAllowed: "", dropEffect: "" };

		fireEvent.dragStart(screen.getByTestId(sharedTestIds.treeNode("s2")), { dataTransfer: transfer });
		fireEvent(target, Object.assign(new Event("drop", { bubbles: true, cancelable: true }), { clientY: 20, dataTransfer: transfer }));

		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.treeNode("s2"))).toBeNull()); // now below s1, which is closed
		fireEvent.click(screen.getByTestId(sharedTestIds.treeToggle("s1")));
		expect((await screen.findByTestId(sharedTestIds.treeNode("s2"))).getAttribute("aria-level")).toBe("3");
	});
});
