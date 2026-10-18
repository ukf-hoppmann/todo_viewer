import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { I18nextProvider } from "react-i18next";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it } from "vitest";
import { coreTestIds, initI18n, PluginRegistryProvider, usePageDetail, type MainLayout } from "../../../../../../client/src/core";
import { logging } from "../../../../../../client/src/core/logging/logging";
import { MemorySink } from "../../../../../../client/src/core/logging/MemorySink";
import { SubLayout } from "../../../../../../client/src/core/navigation/SubLayout";
import { definePlugin } from "../../../../../../client/src/core/plugins/definePlugin";
import type { ActivePlugin, Contribution } from "../../../../../../client/src/core/plugins/types";

const i18nTexts = { de: {}, en: {} };
const section = (name: string, text: string, extra: Partial<Contribution> = {}) =>
	({ slot: "core.sidebar-sections", name, component: () => <p>{text}</p>, ...extra }) as Contribution;
const plugin = (id: string, contributions: Contribution[]): ActivePlugin => ({ id, definition: definePlugin({ i18n: i18nTexts, contributions }) });

/** Renders the sub layout of the main route `demo/main` with the given areas and plugins. */
async function renderLayout(page: ReactNode, layout: MainLayout | undefined, active: ActivePlugin[] = []) {
	const i18n = await initI18n({ lng: "en" });
	const router = createMemoryRouter(
		[
			{
				path: "/demo/main",
				element: (
					<SubLayout ownerId="demo" layout={layout}>
						{page}
					</SubLayout>
				),
			},
		],
		{ initialEntries: ["/demo/main"] },
	);
	render(
		<I18nextProvider i18n={i18n}>
			<PluginRegistryProvider registry={{ active: () => active, statuses: () => [] }}>
				<RouterProvider router={router} />
			</PluginRegistryProvider>
		</I18nextProvider>,
	);
}

function PageWithDetail({ initial = "Detail A" }: { initial?: string }) {
	const [selected, setSelected] = useState<string | undefined>(initial);
	usePageDetail(selected && <p>{selected}</p>);
	return (
		<>
			<button onClick={() => setSelected("Detail B")}>B wählen</button>
			<button onClick={() => setSelected(undefined)}>schließen</button>
			<p>Inhalt</p>
		</>
	);
}

describe("SubLayout: sidebar", () => {
	afterEach(cleanup);

	it("shows the sections of the slot core.sidebar-sections left of the content when the route asks for a sidebar", async () => {
		await renderLayout(<p>Inhalt</p>, { sidebar: true }, [plugin("b", [section("late", "B")]), plugin("a", [section("first", "A", { order: -1 })])]);

		const sidebar = screen.getByTestId(coreTestIds.sidebar);
		expect(screen.getAllByTestId(/^core\.sidebar-section\./).map((entry) => entry.getAttribute("data-testid"))).toEqual([
			"core.sidebar-section.a.first",
			"core.sidebar-section.b.late",
		]);
		expect(sidebar.compareDocumentPosition(screen.getByTestId(coreTestIds.content)) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	});

	it("has no sidebar unless the route asks for one, even with sections", async () => {
		await renderLayout(<p>Inhalt</p>, undefined, [plugin("a", [section("first", "A")])]);

		expect(screen.queryByTestId(coreTestIds.sidebar)).toBeNull();
	});

	it("leaves out sections whose `when` names other routes, and the sidebar without any section", async () => {
		await renderLayout(<p>Inhalt</p>, { sidebar: true }, [plugin("a", [section("elsewhere", "A", { when: ["notes/main"] })])]);

		expect(screen.queryByTestId(coreTestIds.sidebar)).toBeNull();
	});

	it("puts the header above the sidebar", async () => {
		await renderLayout(<p>Inhalt</p>, { header: true, sidebar: true }, [plugin("a", [section("first", "A")])]);

		const header = screen.getByTestId(coreTestIds.pageHeader);
		expect(header.compareDocumentPosition(screen.getByTestId(coreTestIds.sidebar)) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	});
});

describe("SubLayout: detail column", () => {
	afterEach(cleanup);

	it("shows what the page puts into the detail column right of the content", async () => {
		await renderLayout(<PageWithDetail />, { detail: true });

		const detail = screen.getByTestId(coreTestIds.detail);
		expect(detail.textContent).toBe("Detail A");
		expect(screen.getByTestId(coreTestIds.content).compareDocumentPosition(detail) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	});

	it("follows the page and hides the column when the page empties it", async () => {
		await renderLayout(<PageWithDetail />, { detail: true });

		fireEvent.click(screen.getByText("B wählen"));
		expect(screen.getByTestId(coreTestIds.detail).textContent).toBe("Detail B");

		fireEvent.click(screen.getByText("schließen"));
		expect(screen.queryByTestId(coreTestIds.detail)).toBeNull();
	});

	it("has no column while the page sets nothing", async () => {
		await renderLayout(<PageWithDetail initial="" />, { detail: true });

		expect(screen.queryByTestId(coreTestIds.detail)).toBeNull();
	});

	it("shows nothing and warns in development when the route did not ask for a detail column", async () => {
		const sink = new MemorySink("sub-layout-detail-warning-test");
		logging.addSink(sink, { level: "debug" });

		await renderLayout(<PageWithDetail />, undefined);

		expect(screen.queryByTestId(coreTestIds.detail)).toBeNull();
		expect(screen.queryByText("Detail A")).toBeNull();
		expect(sink.entries.filter((entry) => entry.level === "warn")).toEqual([expect.objectContaining({ action: "page-detail" })]);
		logging.removeSink(sink.name);
	});

	it("keeps an error in the detail to the column", async () => {
		function Broken(): ReactNode {
			throw new Error("kaputt");
		}
		function Page() {
			usePageDetail(<Broken />);
			return <p>Inhalt</p>;
		}
		await renderLayout(<Page />, { detail: true });

		expect(screen.getByTestId(coreTestIds.content).textContent).toBe("Inhalt");
		expect(screen.getByTestId(coreTestIds.detail).querySelector(`[data-testid="${coreTestIds.errorFallback}"]`)).not.toBeNull();
	});
});
