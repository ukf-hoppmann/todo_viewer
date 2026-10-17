import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ComponentType } from "react";
import { createRoot } from "react-dom/client";
import { I18nextProvider } from "react-i18next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { coreTestIds, createRootErrorHandlers, initI18n, useLogger } from "../../../../../../client/src/core";
import { logging } from "../../../../../../client/src/core/logging/logging";
import { MemorySink } from "../../../../../../client/src/core/logging/MemorySink";
import { PageHost } from "../../../../../../client/src/core/navigation/PageHost";

type Loader = () => Promise<{ default: ComponentType }>;

const Page = () => <p>die Seite</p>;

function OriginProbe() {
	useLogger().info("probe");
	return <p>geladen</p>;
}

/** A loader whose result the test decides on. */
function deferred() {
	let resolve!: (page: ComponentType) => void;
	let reject!: (error: unknown) => void;
	const promise = new Promise<{ default: ComponentType }>((res, rej) => {
		resolve = (page) => res({ default: page });
		reject = rej;
	});
	return { load: (() => promise) as Loader, resolve, reject };
}

async function renderHost(ui: React.ReactNode) {
	const i18n = await initI18n({ lng: "en" });
	return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);
}

describe("PageHost", () => {
	beforeEach(() => {
		// React reports caught render errors on the console; keep the output clean.
		vi.spyOn(console, "error").mockImplementation(() => undefined);
	});

	afterEach(() => {
		cleanup();
		vi.restoreAllMocks();
	});

	it("shows the loading indicator until the page has loaded, then the page", async () => {
		const { load, resolve } = deferred();
		await renderHost(<PageHost ownerId="example" load={load} />);

		expect(screen.getByTestId(coreTestIds.loading).getAttribute("aria-label")).toBe("Loading");
		expect(screen.queryByText("die Seite")).toBeNull();

		await act(async () => resolve(Page));

		expect(screen.getByText("die Seite")).toBeTruthy();
		expect(screen.queryByTestId(coreTestIds.loading)).toBeNull();
	});

	it("does not call the loader before it is rendered", async () => {
		const load = vi.fn<Loader>(async () => ({ default: Page }));

		expect(load).not.toHaveBeenCalled();
		await renderHost(<PageHost ownerId="example" load={load} />);
		await screen.findByText("die Seite");

		expect(load).toHaveBeenCalledOnce();
	});

	it("gives the page the logger of its owner", async () => {
		const sink = new MemorySink("page-host-origin-test");
		logging.addSink(sink, { level: "debug" });

		await renderHost(<PageHost ownerId="example" load={async () => ({ default: OriginProbe })} />);
		await screen.findByText("geladen");

		expect(sink.entries[0]).toMatchObject({ origin: "example", message: "probe" });
		logging.removeSink(sink.name);
	});

	it("replaces only its own area when the import fails", async () => {
		const { load, reject } = deferred();
		await renderHost(
			<>
				<button>Tab</button>
				<PageHost ownerId="example" load={load} />
			</>,
		);

		await act(async () => reject(new Error("chunk fehlt")));

		expect(screen.getByTestId(coreTestIds.errorFallback)).toBeTruthy();
		expect(screen.getByText("Tab")).toBeTruthy();
		expect(screen.queryByTestId(coreTestIds.loading)).toBeNull();
	});

	it("loads the page again when the user tries again", async () => {
		const load = vi.fn<Loader>().mockRejectedValueOnce(new Error("chunk fehlt")).mockResolvedValue({ default: Page });
		await renderHost(<PageHost ownerId="example" load={load} />);
		await screen.findByTestId(coreTestIds.errorFallback);

		fireEvent.click(screen.getByTestId(coreTestIds.errorFallbackRetry));

		expect(await screen.findByText("die Seite")).toBeTruthy();
		expect(load).toHaveBeenCalledTimes(2);
		expect(screen.queryByTestId(coreTestIds.errorFallback)).toBeNull();
	});

	it("shows the fallback again when the page cannot be loaded on the second try either", async () => {
		const load = vi.fn<Loader>().mockRejectedValue(new Error("chunk fehlt"));
		await renderHost(<PageHost ownerId="example" load={load} />);
		await screen.findByTestId(coreTestIds.errorFallback);

		fireEvent.click(screen.getByTestId(coreTestIds.errorFallbackRetry));

		await vi.waitFor(() => expect(load).toHaveBeenCalledTimes(2));
		expect(await screen.findByTestId(coreTestIds.errorFallback)).toBeTruthy();
	});

	it("reports a failed import with the owner of the page as origin", async () => {
		const i18n = await initI18n({ lng: "en" });
		const container = document.createElement("div");
		const unhandled = { report: vi.fn(), fatal: vi.fn(), recoverable: vi.fn() };
		const root = createRoot(container, createRootErrorHandlers({ i18n, container, unhandled: unhandled as never }));
		const error = new Error("chunk fehlt");

		await act(async () => {
			root.render(
				<I18nextProvider i18n={i18n}>
					<PageHost ownerId="example" load={() => Promise.reject(error)} />
				</I18nextProvider>,
			);
		});

		expect(unhandled.report).toHaveBeenCalledWith(error, expect.objectContaining({ origin: "example" }));
		await act(async () => root.unmount());
	});
});
