import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { initI18n } from "../../../../../../client/src/core/i18n/initI18n";
import { StoreProvider } from "../../../../../../client/src/core/store/StoreProvider";
import { LanguageSync } from "../../../../../../client/src/core/ui-state/LanguageSync";
import { usePersistentState } from "../../../../../../client/src/core/ui-state/usePersistentState";
import { flushUiState, selectUiDocument } from "../../../../../../client/src/core/ui-state/uiState";
import { fakeUiStateBackend } from "../../../../../helpers/client/fakeUiStateBackend";

function Probe({ name = "probe" }: { name?: string }) {
	const [value, setValue, loaded] = usePersistentState("backlog", "counter", 0);
	return (
		<div>
			<span data-testid={`${name}.value`}>{value}</span>
			<span data-testid={`${name}.loaded`}>{String(loaded)}</span>
			<button data-testid={`${name}.up`} onClick={() => setValue((previous) => previous + 1)} />
			<button data-testid={`${name}.set`} onClick={() => setValue(10)} />
		</div>
	);
}

describe("usePersistentState", () => {
	afterEach(cleanup);

	it("returns the default until the document is loaded, then the stored value", async () => {
		const backend = fakeUiStateBackend({ backlog: { counter: 7 } });

		render(
			<StoreProvider store={backend.store}>
				<Probe />
			</StoreProvider>,
		);

		expect(screen.getByTestId("probe.value").textContent).toBe("0");
		expect(screen.getByTestId("probe.loaded").textContent).toBe("false");
		await waitFor(() => expect(screen.getByTestId("probe.value").textContent).toBe("7"));
		expect(screen.getByTestId("probe.loaded").textContent).toBe("true");
	});

	it("keeps the default when the document has no value for the key", async () => {
		const backend = fakeUiStateBackend({ backlog: { other: 1 } });

		render(
			<StoreProvider store={backend.store}>
				<Probe />
			</StoreProvider>,
		);

		await waitFor(() => expect(screen.getByTestId("probe.loaded").textContent).toBe("true"));
		expect(screen.getByTestId("probe.value").textContent).toBe("0");
	});

	it("shows a new value at once everywhere and stores it on the server", async () => {
		const backend = fakeUiStateBackend({ backlog: { counter: 1 } });
		render(
			<StoreProvider store={backend.store}>
				<Probe name="a" />
				<Probe name="b" />
			</StoreProvider>,
		);
		await waitFor(() => expect(screen.getByTestId("a.value").textContent).toBe("1"));

		act(() => screen.getByTestId("a.up").click());
		await waitFor(() => expect(screen.getByTestId("b.value").textContent).toBe("2"));
		await act(() => flushUiState(backend.store));

		expect(backend.documents.get("backlog")).toEqual({ counter: 2 });
	});

	it("lets the setter work with the latest value in a row of changes", async () => {
		const backend = fakeUiStateBackend({ backlog: { counter: 0 } });
		render(
			<StoreProvider store={backend.store}>
				<Probe />
			</StoreProvider>,
		);
		await waitFor(() => expect(screen.getByTestId("probe.loaded").textContent).toBe("true"));

		act(() => {
			screen.getByTestId("probe.up").click();
			screen.getByTestId("probe.up").click();
			screen.getByTestId("probe.up").click();
		});
		await waitFor(() => expect(screen.getByTestId("probe.value").textContent).toBe("3"));
		await act(() => flushUiState(backend.store));

		expect(backend.documents.get("backlog")).toEqual({ counter: 3 });
	});
});

describe("LanguageSync", () => {
	afterEach(cleanup);

	async function renderSync(stored: Record<string, unknown>, lng: string) {
		const backend = fakeUiStateBackend({ core: stored });
		const i18n = await initI18n({ lng });
		render(
			<I18nextProvider i18n={i18n}>
				<StoreProvider store={backend.store}>
					<LanguageSync />
				</StoreProvider>
			</I18nextProvider>,
		);
		return { backend, i18n };
	}

	it("applies the stored language once it is loaded", async () => {
		const { i18n } = await renderSync({ language: "en" }, "de");

		await waitFor(() => expect(i18n.resolvedLanguage).toBe("en"));
	});

	it("ignores a stored language that is not supported", async () => {
		const { i18n, backend } = await renderSync({ language: "fr" }, "de");

		await waitFor(() => expect(backend.requests.length).toBeGreaterThan(0));
		expect(i18n.resolvedLanguage).toBe("de");
	});

	it("stores a language the user chooses", async () => {
		const { i18n, backend } = await renderSync({ language: "de" }, "de");
		await waitFor(() => expect(selectUiDocument(backend.store.getState(), "core")).toEqual({ language: "de" }));
		await act(async () => {}); // the component has seen the loaded document

		await act(() => i18n.changeLanguage("en"));
		await waitFor(() => expect(selectUiDocument(backend.store.getState(), "core")).toEqual({ language: "en" }));
		await act(() => flushUiState(backend.store));

		expect(backend.documents.get("core")).toEqual({ language: "en" });
	});

	it("does not write anything when nothing is stored and the user did not choose", async () => {
		const { backend } = await renderSync({}, "en");

		await waitFor(() => expect(backend.requests.length).toBeGreaterThan(0));
		await act(() => flushUiState(backend.store));

		expect(backend.puts()).toEqual([]);
	});
});
