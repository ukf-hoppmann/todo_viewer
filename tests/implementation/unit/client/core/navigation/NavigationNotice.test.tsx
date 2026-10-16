import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { createMemoryRouter, RouterProvider } from "react-router";
import { afterEach, describe, expect, it } from "vitest";
import { coreTestIds, initI18n } from "../../../../../../client/src/core";
import { logging } from "../../../../../../client/src/core/logging/logging";
import { MemorySink } from "../../../../../../client/src/core/logging/MemorySink";
import { NavigationNotice } from "../../../../../../client/src/core/navigation/NavigationNotice";
import { NotFoundView } from "../../../../../../client/src/core/navigation/NotFoundView";
import type { ViewResolution } from "../../../../../../client/src/core/navigation/resolveView";

async function renderAt(path: string, element: React.ReactNode, lng = "en") {
	const i18n = await initI18n({ lng });
	const router = createMemoryRouter(
		[
			{ path: "/", element: <p>Start</p> },
			{ path: "*", element: element },
		],
		{ initialEntries: [path] },
	);
	render(
		<I18nextProvider i18n={i18n}>
			<RouterProvider router={router} />
		</I18nextProvider>,
	);
	return { router };
}

describe("NavigationNotice", () => {
	afterEach(cleanup);

	it.each([
		["not-found", coreTestIds.notFound, { de: "Diese Seite gibt es nicht.", en: "This page does not exist." }],
		[
			"unavailable",
			coreTestIds.unavailable,
			{
				de: "Diese Ansicht ist derzeit nicht verfügbar.",
				en: "This view is currently not available.",
			},
		],
		["no-views", coreTestIds.noViews, { de: "Es sind keine Ansichten verfügbar.", en: "No views are available." }],
		[
			"no-entries",
			coreTestIds.noEntries,
			{
				de: "In diesem Bereich sind keine Einträge verfügbar.",
				en: "No entries are available in this area.",
			},
		],
	] as const)("shows the notice %s in every language", async (kind, testId, texts) => {
		for (const lng of ["de", "en"] as const) {
			cleanup();
			await renderAt("/x", <NavigationNotice kind={kind} />, lng);

			expect(screen.getByTestId(testId).textContent).toContain(texts[lng]);
		}
	});

	it.each(["not-found", "unavailable"] as const)("offers a button to the start page for %s", async (kind) => {
		const { router } = await renderAt("/x", <NavigationNotice kind={kind} />);

		fireEvent.click(screen.getByTestId(coreTestIds.homeButton));

		expect(router.state.location.pathname).toBe("/");
	});

	it.each(["no-views", "no-entries"] as const)("offers no button for the notice %s", async (kind) => {
		await renderAt("/x", <NavigationNotice kind={kind} />);

		expect(screen.queryByTestId(coreTestIds.homeButton)).toBeNull();
	});
});

describe("NotFoundView", () => {
	afterEach(cleanup);

	function resolveTo(resolution: ViewResolution) {
		return () => resolution;
	}

	it("shows the notice for a page that does not exist and logs the path at info level", async () => {
		const sink = new MemorySink("not-found-test");
		logging.addSink(sink, { level: "debug" });

		await renderAt("/ghost/view", <NotFoundView resolve={resolveTo({ kind: "not-found", log: true })} />);

		expect(screen.getByTestId(coreTestIds.notFound)).toBeTruthy();
		expect(sink.entries).toEqual([expect.objectContaining({ level: "info", origin: "core", data: { path: "/ghost/view" } })]);
		logging.removeSink(sink.name);
	});

	it("shows the unavailable notice and logs a plugin that is switched off", async () => {
		const sink = new MemorySink("unavailable-test");
		logging.addSink(sink, { level: "debug" });

		await renderAt("/off/view", <NotFoundView resolve={resolveTo({ kind: "unavailable", log: true })} />);

		expect(screen.getByTestId(coreTestIds.unavailable)).toBeTruthy();
		expect(sink.entries).toHaveLength(1);
		logging.removeSink(sink.name);
	});

	it("logs nothing new for a plugin that failed, which was reported at the start", async () => {
		const sink = new MemorySink("failed-test");
		logging.addSink(sink, { level: "debug" });

		await renderAt("/bad/view", <NotFoundView resolve={resolveTo({ kind: "unavailable", log: false })} />);

		expect(screen.getByTestId(coreTestIds.unavailable)).toBeTruthy();
		expect(sink.entries).toHaveLength(0);
		logging.removeSink(sink.name);
	});

	it("passes the called path to the resolution", async () => {
		const paths: string[] = [];
		await renderAt(
			"/ghost/view",
			<NotFoundView
				resolve={(path) => {
					paths.push(path);
					return { kind: "not-found", log: false };
				}}
			/>,
		);

		expect(paths).toContain("/ghost/view");
	});
});
