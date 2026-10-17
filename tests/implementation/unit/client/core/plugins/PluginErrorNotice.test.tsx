import { act, cleanup, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { StrictMode } from "react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { coreTestIds, initI18n, ModalHost } from "../../../../../../client/src/core";
import { createModals } from "../../../../../../client/src/core/modals/createModals";
import { PluginErrorNotice } from "../../../../../../client/src/core/plugins/PluginErrorNotice";
import { PluginRegistryProvider } from "../../../../../../client/src/core/plugins/PluginRegistryProvider";
import { usePluginRegistry } from "../../../../../../client/src/core/plugins/usePluginRegistry";
import type { LogEntry } from "../../../../../../client/src/core/logging/types";
import type { PluginRegistry, PluginStatus } from "../../../../../../client/src/core/plugins/types";

function registryWith(statuses: PluginStatus[]): PluginRegistry {
	return { active: () => [], statuses: () => statuses };
}

async function renderNotice(statuses: PluginStatus[], lng = "de") {
	const modals = createModals();
	const i18n = await initI18n({ lng });
	await act(async () => {
		render(
			<StrictMode>
				<I18nextProvider i18n={i18n}>
					<PluginRegistryProvider registry={registryWith(statuses)}>
						<ModalHost modals={modals} />
						<PluginErrorNotice modals={modals} />
					</PluginRegistryProvider>
				</I18nextProvider>
			</StrictMode>,
		);
	});
	return { modals };
}

const logEntry: LogEntry = {
	id: "ab12cd34",
	time: "2026-10-01T08:00:00.000Z",
	level: "error",
	origin: "core",
	sessionId: "f".repeat(32),
	route: "/",
};

const failed: PluginStatus = {
	id: "broken",
	status: "failed",
	code: "import-failed",
	message: "importing index.ts failed",
	logEntry,
};

describe("usePluginRegistry", () => {
	it("returns the registry of the provider", () => {
		const registry = registryWith([]);
		const { result } = renderHook(() => usePluginRegistry(), {
			wrapper: ({ children }) => <PluginRegistryProvider registry={registry}>{children}</PluginRegistryProvider>,
		});

		expect(result.current).toBe(registry);
	});

	it("throws outside of a provider", () => {
		expect(() => renderHook(() => usePluginRegistry())).toThrow("PluginRegistryProvider");
	});
});

describe("PluginErrorNotice", () => {
	afterEach(cleanup);

	it("shows nothing when no plugin failed", async () => {
		await renderNotice([
			{ id: "a", status: "active" },
			{ id: "b", status: "disabled" },
			{ id: "c", status: "blocked", code: "requires-disabled", cause: ["b"] },
		]);

		expect(screen.queryByTestId(coreTestIds.modal)).toBeNull();
	});

	it("names each failed plugin with the plugins it affects", async () => {
		await renderNotice([
			failed,
			{ id: "a", status: "blocked", code: "requires-failed", cause: ["broken"] },
			{ id: "b", status: "blocked", code: "requires-failed", cause: ["a", "broken"] },
			{ id: "other", status: "failed", code: "manifest-invalid", message: "plugin.json is missing" },
		]);

		const message = screen.getByTestId(coreTestIds.modalMessage).textContent ?? "";
		expect(message).toContain("Funktionen");
		expect(message).toContain("broken (betroffen: a, b)");
		expect(message).toContain("other");
		expect(message).not.toContain("other (betroffen");
	});

	it("shows code and reason of each failed plugin in the details", async () => {
		await renderNotice([failed]);

		fireEvent.click(screen.getByTestId(coreTestIds.modalDetailsToggle));
		expect(screen.getByTestId(coreTestIds.modalDetails).textContent).toContain("import-failed: importing index.ts failed");
	});

	it("shows error id and session id of the log entries in the details", async () => {
		await renderNotice([failed, { ...failed, id: "second", logEntry: { ...logEntry, id: "ef56ab78" } }]);

		fireEvent.click(screen.getByTestId(coreTestIds.modalDetailsToggle));
		const details = screen.getByTestId(coreTestIds.modalDetails).textContent ?? "";
		expect(details).toContain("Fehler-ID");
		expect(details).toContain("ab12cd34");
		expect(details).toContain("ef56ab78");
		expect(details.split(logEntry.sessionId)).toHaveLength(2);
	});

	it("shows one dialog only, also under StrictMode", async () => {
		await renderNotice([failed]);

		fireEvent.click(screen.getByTestId(coreTestIds.modalClose));
		expect(screen.queryByTestId(coreTestIds.modal)).toBeNull();
	});

	it("uses the language of the interface", async () => {
		await renderNotice([failed], "en");

		expect(screen.getByTestId(coreTestIds.modalMessage).textContent).toContain("broken");
		expect(screen.getByTestId(coreTestIds.modalMessage).textContent).toContain("features");
	});
});
