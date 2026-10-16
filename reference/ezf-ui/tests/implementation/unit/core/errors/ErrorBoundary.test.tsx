import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { I18nextProvider } from "react-i18next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { coreTestIds, initI18n, useLogger } from "../../../../../src/core";
import { ErrorBoundary } from "../../../../../src/core/errors/ErrorBoundary";
import { logging } from "../../../../../src/core/logging/logging";
import { MemorySink } from "../../../../../src/core/logging/MemorySink";

function Broken(): never {
	throw new Error("kaputt");
}

function Healthy({ label = "gesund" }: { label?: string }) {
	return <p>{label}</p>;
}

/** Breaks while `broken` is true; lets a test fix the cause before the retry. */
let broken = true;
function Flaky() {
	if (broken) throw new Error("kaputt");
	return <p>repariert</p>;
}

function OriginProbe() {
	useLogger().info("probe");
	return null;
}

async function renderWithI18n(ui: React.ReactNode, lng = "de") {
	const i18n = await initI18n({ lng });
	return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);
}

describe("ErrorBoundary", () => {
	beforeEach(() => {
		broken = true;
		// React reports caught render errors on the console; keep the output clean.
		vi.spyOn(console, "error").mockImplementation(() => undefined);
	});

	afterEach(() => {
		cleanup();
		vi.restoreAllMocks();
	});

	it("shows its children while nothing fails", async () => {
		await renderWithI18n(
			<ErrorBoundary origin="core">
				<Healthy />
			</ErrorBoundary>,
		);

		expect(screen.getByText("gesund")).toBeTruthy();
		expect(screen.queryByTestId(coreTestIds.errorFallback)).toBeNull();
	});

	it("replaces a failing area with the fallback text and a retry button", async () => {
		await renderWithI18n(
			<ErrorBoundary origin="variant-filter">
				<Broken />
			</ErrorBoundary>,
		);

		expect(screen.getByTestId(coreTestIds.errorFallback).textContent).toContain(
			"Dieser Bereich konnte nicht angezeigt werden.",
		);
		expect(screen.getByTestId(coreTestIds.errorFallbackRetry).textContent).toBe("Erneut versuchen");
		expect(screen.queryByTestId(coreTestIds.errorFallbackReload)).toBeNull();
	});

	it("renders the area again after a retry", async () => {
		await renderWithI18n(
			<ErrorBoundary origin="core">
				<Flaky />
			</ErrorBoundary>,
		);
		expect(screen.getByTestId(coreTestIds.errorFallback)).toBeTruthy();

		broken = false;
		fireEvent.click(screen.getByTestId(coreTestIds.errorFallbackRetry));

		expect(screen.getByText("repariert")).toBeTruthy();
		expect(screen.queryByTestId(coreTestIds.errorFallback)).toBeNull();
	});

	it("shows the fallback again when the retry fails again", async () => {
		await renderWithI18n(
			<ErrorBoundary origin="core">
				<Broken />
			</ErrorBoundary>,
		);

		fireEvent.click(screen.getByTestId(coreTestIds.errorFallbackRetry));

		expect(screen.getByTestId(coreTestIds.errorFallback)).toBeTruthy();
	});

	it("leaves an area next to the failing one untouched", async () => {
		await renderWithI18n(
			<>
				<ErrorBoundary origin="variant-filter">
					<Broken />
				</ErrorBoundary>
				<ErrorBoundary origin="process-manager">
					<Healthy label="daneben" />
				</ErrorBoundary>
			</>,
		);

		expect(screen.getAllByTestId(coreTestIds.errorFallback)).toHaveLength(1);
		expect(screen.getByText("daneben")).toBeTruthy();
	});

	it("uses the app texts and a reload button for variant app", async () => {
		const reload = vi.fn();
		vi.stubGlobal("location", { ...window.location, reload });
		await renderWithI18n(
			<ErrorBoundary origin="core" variant="app">
				<Broken />
			</ErrorBoundary>,
		);

		expect(screen.getByTestId(coreTestIds.errorFallback).textContent).toContain(
			"Die Anwendung konnte nicht angezeigt werden.",
		);
		expect(screen.queryByTestId(coreTestIds.errorFallbackRetry)).toBeNull();
		fireEvent.click(screen.getByTestId(coreTestIds.errorFallbackReload));

		expect(reload).toHaveBeenCalledOnce();
		vi.unstubAllGlobals();
	});

	it("translates the fallback into the language of the interface", async () => {
		await renderWithI18n(
			<ErrorBoundary origin="core">
				<Broken />
			</ErrorBoundary>,
			"en",
		);

		expect(screen.getByTestId(coreTestIds.errorFallback).textContent).toContain("This area could not be displayed.");
		expect(screen.getByTestId(coreTestIds.errorFallbackRetry).textContent).toBe("Try again");
	});

	it("neither logs nor opens a dialog itself", async () => {
		const sink = new MemorySink("boundary-test");
		logging.addSink(sink, { level: "debug" });

		await renderWithI18n(
			<ErrorBoundary origin="core">
				<Broken />
			</ErrorBoundary>,
		);

		expect(sink.entries).toHaveLength(0);
		logging.removeSink(sink.name);
	});

	it("gives the area below the logger of its origin", async () => {
		const sink = new MemorySink("boundary-origin-test");
		logging.addSink(sink, { level: "debug" });

		await renderWithI18n(
			<ErrorBoundary origin="variant-filter">
				<OriginProbe />
			</ErrorBoundary>,
		);

		expect(sink.entries[0]).toMatchObject({ origin: "variant-filter", message: "probe" });
		logging.removeSink(sink.name);
	});

	it("keeps working after the error in a component that has state", async () => {
		function Counter() {
			const [count, setCount] = useState(0);
			if (count === 1) throw new Error("beim Klick");
			return <button onClick={() => setCount(1)}>klick</button>;
		}
		await renderWithI18n(
			<ErrorBoundary origin="core">
				<Counter />
			</ErrorBoundary>,
		);

		fireEvent.click(screen.getByText("klick"));

		expect(screen.getByTestId(coreTestIds.errorFallback)).toBeTruthy();
		fireEvent.click(screen.getByTestId(coreTestIds.errorFallbackRetry));
		expect(screen.getByText("klick")).toBeTruthy();
	});
});
