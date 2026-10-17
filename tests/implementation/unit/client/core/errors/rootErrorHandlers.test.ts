import { createInstance } from "i18next";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { coreTestIds, initI18n } from "../../../../../../client/src/core";
import { createErrors } from "../../../../../../client/src/core/errors/createErrors";
import { createUnhandledErrors } from "../../../../../../client/src/core/errors/createUnhandledErrors";
import { ErrorBoundary } from "../../../../../../client/src/core/errors/ErrorBoundary";
import { createRootErrorHandlers } from "../../../../../../client/src/core/errors/rootErrorHandlers";
import { createLogging } from "../../../../../../client/src/core/logging/createLogging";
import { MemorySink } from "../../../../../../client/src/core/logging/MemorySink";
import { createModals } from "../../../../../../client/src/core/modals/createModals";

async function setup(lng = "de") {
	const logging = createLogging();
	const sink = new MemorySink("memory");
	logging.addSink(sink, { level: "debug" });
	const modals = createModals();
	const unhandled = createUnhandledErrors({ errors: createErrors({ logging, modals }), logging });
	const container = document.createElement("div");
	container.id = "root";
	document.body.append(container);
	const i18n = await initI18n({ lng });
	const handlers = createRootErrorHandlers({ unhandled, i18n, container });
	return { sink, modals, container, handlers };
}

describe("createRootErrorHandlers", () => {
	beforeEach(() => {
		document.body.innerHTML = "";
	});

	afterEach(() => {
		document.body.innerHTML = "";
	});

	describe("onCaughtError (a boundary caught a render error)", () => {
		it("logs once with the origin of the boundary, the component stack and action render, and shows one hint", async () => {
			const { handlers, sink, modals } = await setup();
			const error = new Error("beim Rendern");
			const boundary = new ErrorBoundary({ origin: "variant-filter", children: null });

			handlers.onCaughtError(error, { componentStack: "at Broken", errorBoundary: boundary });

			expect(sink.entries).toHaveLength(1);
			expect(sink.entries[0]).toMatchObject({
				level: "error",
				origin: "variant-filter",
				action: "render",
				error,
				data: { componentStack: "at Broken" },
			});
			expect(modals.getSnapshot()?.kind).toBe("alert");
		});

		it("uses the origin core for a boundary that is not an ErrorBoundary of the core", async () => {
			const { handlers, sink } = await setup();
			// A boundary of another library or the ModalHost: it has props, but no origin of ours.
			const foreign = { props: { origin: "fremd" } } as never;

			handlers.onCaughtError(new Error("x"), { componentStack: "", errorBoundary: foreign });
			handlers.onCaughtError(new Error("y"), { componentStack: "" });

			expect(sink.entries.map((entry) => entry.origin)).toEqual(["core", "core"]);
		});
	});

	describe("onRecoverableError (React recovered by itself)", () => {
		it("only logs a warning, without a hint", async () => {
			const { handlers, sink, modals } = await setup();
			const error = new Error("hydration");

			handlers.onRecoverableError(error, { componentStack: "at X" });

			expect(sink.entries).toHaveLength(1);
			expect(sink.entries[0]).toMatchObject({
				level: "warn",
				origin: "core",
				action: "render-recovered",
				error,
				data: { componentStack: "at X" },
			});
			expect(modals.getSnapshot()).toBeUndefined();
		});
	});

	describe("onUncaughtError (no boundary caught the render error)", () => {
		it("logs once as error with action render-uncaught and opens no dialog", async () => {
			const { handlers, sink, modals } = await setup();
			const error = new Error("ganz oben");

			handlers.onUncaughtError(error, { componentStack: "at App" });

			expect(sink.entries).toHaveLength(1);
			expect(sink.entries[0]).toMatchObject({
				level: "error",
				origin: "core",
				action: "render-uncaught",
				error,
				data: { componentStack: "at App" },
			});
			expect(modals.getSnapshot()).toBeUndefined();
		});

		it("replaces the content of the root element by the crash message with error id and session id", async () => {
			const { handlers, sink, container } = await setup();
			container.innerHTML = "<p>alte Oberfläche</p>";

			handlers.onUncaughtError(new Error("x"), { componentStack: "" });

			const message = container.querySelector(`[data-testid="${coreTestIds.crashMessage}"]`);
			expect(message).not.toBeNull();
			expect(container.textContent).not.toContain("alte Oberfläche");
			expect(message?.textContent).toContain("Die Anwendung ist abgestürzt. Bitte laden Sie die Seite neu.");
			expect(message?.textContent).toContain(`Fehler-ID: ${sink.entries[0]?.id}`);
			expect(message?.textContent).toContain(`Sitzungs-ID: ${sink.entries[0]?.sessionId}`);
		});

		it("writes the crash message in the language of the interface", async () => {
			const { handlers, container } = await setup("en");

			handlers.onUncaughtError(new Error("x"), { componentStack: "" });

			expect(container.textContent).toContain("The application has crashed. Please reload the page.");
			expect(container.textContent).toContain("Error ID:");
		});

		it("falls back to German when the texts are not available", async () => {
			const logging = createLogging();
			const sink = new MemorySink("memory");
			logging.addSink(sink, { level: "debug" });
			const unhandled = createUnhandledErrors({
				errors: createErrors({ logging, modals: createModals() }),
				logging,
			});
			const container = document.createElement("div");
			const empty = createInstance();
			await empty.init({ lng: "xx", resources: {} });
			const handlers = createRootErrorHandlers({ unhandled, i18n: empty, container });

			handlers.onUncaughtError(new Error("x"), { componentStack: "" });

			expect(container.textContent).toContain("Die Anwendung ist abgestürzt. Bitte laden Sie die Seite neu.");
			expect(container.textContent).toContain("Fehler-ID:");
		});

		it("shows an error object that is a string as well", async () => {
			const { handlers, sink, container } = await setup();

			handlers.onUncaughtError("nur Text", { componentStack: "" });

			expect(sink.entries).toHaveLength(1);
			expect(container.querySelector(`[data-testid="${coreTestIds.crashMessage}"]`)).not.toBeNull();
		});
	});
});
