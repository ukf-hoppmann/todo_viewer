import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { ThemeProvider } from "@mui/material";
import { I18nextProvider } from "react-i18next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { StartedView } from "../../../../../client/src/app/StartedView";
import { coreContributions } from "../../../../../client/src/app/coreContributions";
import { catalogue } from "../../../../../client/src/app/plugins/catalogue";
import { startApp, type StartResult } from "../../../../../client/src/app/startApp";
import { activePluginSelection } from "../../../../../client/src/app/plugins/activePlugins";
import { banners, coreTestIds, createBanners, createErrors, createModals, initI18n, theme } from "../../../../../client/src/core";
import { createLogging } from "../../../../../client/src/core/logging/createLogging";
import { exampleTestIds } from "../../../../../client/src/plugins/example";
import { layoutTestIds } from "../../../../../client/src/plugins/layout-header-sidebar";
import { FakeEventSource, manualSchedule } from "../../../../helpers/client/fakeEventSource";

/** A server that answers `core/health` and keeps the UI-state documents; counts the health requests. */
function fakeServer(documents: Record<string, Record<string, unknown>> = {}) {
	const state = { health: 0, documents: new Map(Object.entries(documents)), online: true };
	const fetch = vi.fn(async (request: Request) => {
		if (!state.online) throw new TypeError("Failed to fetch");
		const { pathname } = new URL(request.url, "http://localhost");
		if (pathname === "/api/core/health") {
			state.health += 1;
			return Response.json({ status: "ok" });
		}
		const owner = pathname.split("/").at(-1)!;
		if (pathname.startsWith("/api/core/ui-state/")) {
			if (request.method === "PUT") state.documents.set(owner, ((await request.json()) as { document: Record<string, unknown> }).document);
			return Response.json({ owner, document: state.documents.get(owner) ?? {} });
		}
		return new Response(null, { status: 404 });
	});
	return { state, fetch };
}

async function start(documents: Record<string, Record<string, unknown>> = {}, lng = "de") {
	FakeEventSource.reset();
	const i18n = await initI18n({ lng });
	const server = fakeServer(documents);
	const timers = manualSchedule();
	const logging = createLogging();
	const started = await startApp({
		i18n,
		catalogue,
		coreContributions,
		devRoutes: [],
		selection: activePluginSelection(["layout-header-sidebar", "example"]),
		logging,
		errors: createErrors({ logging, modals: createModals() }),
		banners: createBanners(),
		connection: { fetch: server.fetch },
		events: { createSource: (url) => new FakeEventSource(url), schedule: timers.schedule },
		router: { initialEntries: ["/example/overview"] },
	});
	return { started, i18n, server, timers };
}

function show(started: StartResult, i18n: Awaited<ReturnType<typeof initI18n>>) {
	render(
		<I18nextProvider i18n={i18n}>
			<ThemeProvider theme={theme}>
				<StartedView started={started} />
			</ThemeProvider>
		</I18nextProvider>,
	);
}

beforeEach(() => banners.clear());
afterEach(cleanup);

describe("startApp: the application without login", () => {
	it("starts the plugins and shows the app bar with the tabs, the header widget and the sidebar section", async () => {
		const { started, i18n } = await start();
		expect(started.kind).toBe("app");

		show(started, i18n);

		expect(await screen.findByTestId(coreTestIds.appBar)).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.navTab("example", "overview")).textContent).toBe("Beispiel");
		expect(screen.getByTestId(coreTestIds.navTab("core", "settings")).textContent).toBe("Einstellungen");
		expect(screen.getByTestId(layoutTestIds.headerAction("example", "event-counter"))).toBeTruthy();
		expect(screen.getByTestId(layoutTestIds.sidebarSection("example", "info"))).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.languageSelect)).toBeTruthy();
	});

	it("shows the sidebar section only on the main route it belongs to", async () => {
		const { started, i18n } = await start();
		show(started, i18n);
		expect(await screen.findByTestId(layoutTestIds.sidebar)).toBeTruthy();

		fireEvent.click(screen.getByTestId(coreTestIds.navTab("core", "settings")));

		await waitFor(() => expect(screen.queryByTestId(layoutTestIds.sidebar)).toBeNull());
		expect(await screen.findByTestId(coreTestIds.settingsSection("example", "info"))).toBeTruthy();
		expect(screen.getByTestId(exampleTestIds.settingsText)).toBeTruthy();
	});

	it("does not contain any login: no login page, no logout button", async () => {
		const { started, i18n } = await start();
		show(started, i18n);

		await screen.findByTestId(coreTestIds.appBar);

		expect(screen.queryByText(/anmelden|abmelden|sign in|sign out/i)).toBeNull();
	});
});

describe("startApp: events from the server", () => {
	it("reloads the data of the example plugin when the server reports an event", async () => {
		const { started, i18n, server } = await start();
		show(started, i18n);
		await waitFor(() => expect(screen.getByTestId(exampleTestIds.healthStatus).textContent).toBe("ok"));
		expect(server.state.health).toBe(2); // one for the start, one for the page
		expect(FakeEventSource.last.topics).toEqual(["core.sync.state"]);
		FakeEventSource.last.open();

		act(() => FakeEventSource.last.send("core.sync.state", { project: "p", state: "in_sync" }));

		await waitFor(() => expect(server.state.health).toBe(3));
		await waitFor(() => expect(screen.getByTestId(exampleTestIds.eventCounter).textContent).toBe("1 Ereignis"));
	});

	it("reloads after the stream was interrupted and is back", async () => {
		const { started, i18n, server, timers } = await start();
		show(started, i18n);
		await waitFor(() => expect(server.state.health).toBe(2));
		FakeEventSource.last.open();

		FakeEventSource.last.fail();
		timers.runNext();
		FakeEventSource.last.open();

		await waitFor(() => expect(server.state.health).toBe(3));
	});
});

describe("startApp: the language", () => {
	it("applies the language stored in the UI state of the server", async () => {
		const { started, i18n } = await start({ core: { language: "en" } }, "de");
		show(started, i18n);

		await waitFor(() => expect(screen.getByTestId(coreTestIds.navTab("core", "settings")).textContent).toBe("Settings"));
	});

	it("stores the language the user chooses in the UI state of the server", async () => {
		const { started, i18n, server } = await start({ core: {} }, "de");
		show(started, i18n);
		await waitFor(() => expect(screen.getByTestId(coreTestIds.languageSelect)).toBeTruthy());
		await act(async () => {}); // the stored document is loaded

		fireEvent.mouseDown(screen.getByTestId(coreTestIds.languageSelect));
		fireEvent.click(screen.getByTestId(coreTestIds.languageOption("en")));

		await waitFor(() => expect(screen.getByTestId(coreTestIds.navTab("core", "settings")).textContent).toBe("Settings"));
		await waitFor(() => expect(server.state.documents.get("core")).toEqual({ language: "en" }), { timeout: 3000 });
	});
});

describe("startApp: the backend does not answer", () => {
	it("waits and shows a banner instead of stopping, and starts as soon as the server answers", async () => {
		FakeEventSource.reset();
		const i18n = await initI18n({ lng: "de" });
		const server = fakeServer();
		server.state.online = false;
		const timers = manualSchedule();
		const bannerList = createBanners();
		const logging = createLogging();

		const pending = startApp({
			i18n,
			catalogue,
			coreContributions,
			devRoutes: [],
			selection: activePluginSelection(["layout-header-sidebar"]),
			logging,
			errors: createErrors({ logging, modals: createModals() }),
			banners: bannerList,
			connection: { fetch: server.fetch },
			monitor: { schedule: timers.schedule },
			events: { createSource: (url) => new FakeEventSource(url), schedule: timers.schedule },
		});
		await vi.waitFor(() => expect(bannerList.getSnapshot()).toHaveLength(1));
		expect(bannerList.getSnapshot()[0]!.request.message).toEqual({ key: "connection.startMessage", params: { attempts: 1 } });

		server.state.online = true;
		await vi.waitFor(() => expect(timers.jobs.length).toBeGreaterThan(0));
		timers.runNext();
		const started = await pending;

		expect(started.kind).toBe("app");
		expect(bannerList.getSnapshot()).toHaveLength(0);
	});
});
