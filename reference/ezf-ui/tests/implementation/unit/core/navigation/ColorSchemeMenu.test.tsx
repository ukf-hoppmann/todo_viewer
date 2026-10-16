import { ThemeProvider, useColorScheme } from "@mui/material";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { coreTestIds, initI18n, theme } from "../../../../../src/core";
import { ColorSchemeMenu } from "../../../../../src/core/navigation/ColorSchemeMenu";
import { fakeStorage } from "../../../../helpers/fakeBrowser";
import { fakeSystemColorScheme } from "../../../../helpers/fakeSystemColorScheme";

/** Shows the color scheme that is in effect, so the tests can see what the interface does. */
function Probe() {
	const { colorScheme } = useColorScheme();
	return <p data-testid="test.color-scheme-probe">{colorScheme}</p>;
}

type Mode = "light" | "dark" | "system";

/** MUI keeps the choice under this key. */
const storageKey = "mui-mode";

describe("ColorSchemeMenu", () => {
	let storage: ReturnType<typeof fakeStorage>;
	let system: ReturnType<typeof fakeSystemColorScheme>;

	async function renderMenu({ lng = "de", stored, systemScheme = "light" }: { lng?: string; stored?: Mode; systemScheme?: "light" | "dark" } = {}) {
		storage = fakeStorage(stored ? { [storageKey]: stored } : {});
		vi.stubGlobal("localStorage", storage);
		system = fakeSystemColorScheme(systemScheme);
		const i18n = await initI18n({ lng });
		render(
			<I18nextProvider i18n={i18n}>
				<ThemeProvider theme={theme}>
					<ColorSchemeMenu />
					<Probe />
				</ThemeProvider>
			</I18nextProvider>,
		);
	}

	const open = () => fireEvent.click(screen.getByTestId(coreTestIds.colorSchemeButton));
	const choose = (mode: Mode) => {
		open();
		fireEvent.click(screen.getByTestId(coreTestIds.colorSchemeOption(mode)));
	};
	const scheme = () => screen.getByTestId("test.color-scheme-probe").textContent;
	const checked = (mode: Mode) => screen.getByTestId(coreTestIds.colorSchemeOption(mode)).getAttribute("aria-checked");

	beforeEach(() => {
		vi.unstubAllGlobals();
	});
	afterEach(() => {
		cleanup();
		vi.unstubAllGlobals();
	});

	it("follows the system without a choice and shows the symbol for the system", async () => {
		await renderMenu({ systemScheme: "dark" });

		expect(scheme()).toBe("dark");
		expect(screen.getByTestId(coreTestIds.colorSchemeIcon("system"))).toBeTruthy();
	});

	it("labels the button in the active language", async () => {
		await renderMenu({ lng: "fr" });

		expect(screen.getByTestId(coreTestIds.colorSchemeButton).getAttribute("aria-label")).toBe("Thème");
	});

	it("offers light, dark and system in the active language and marks the one in effect", async () => {
		await renderMenu({ lng: "de" });

		open();

		expect(screen.getByTestId(coreTestIds.colorSchemeOption("light")).textContent).toBe("Hell");
		expect(screen.getByTestId(coreTestIds.colorSchemeOption("dark")).textContent).toBe("Dunkel");
		expect(screen.getByTestId(coreTestIds.colorSchemeOption("system")).textContent).toBe("System");
		expect(checked("system")).toBe("true");
		expect(checked("light")).toBe("false");
		expect(checked("dark")).toBe("false");
	});

	it("switches to dark, shows its symbol and remembers the choice", async () => {
		await renderMenu({ systemScheme: "light" });

		choose("dark");

		expect(scheme()).toBe("dark");
		expect(screen.getByTestId(coreTestIds.colorSchemeIcon("dark"))).toBeTruthy();
		expect(storage.getItem(storageKey)).toBe("dark");
		open();
		expect(checked("dark")).toBe("true");
		expect(checked("system")).toBe("false");
	});

	it("switches to light, shows its symbol and remembers the choice", async () => {
		await renderMenu({ systemScheme: "dark" });

		choose("light");

		expect(scheme()).toBe("light");
		expect(screen.getByTestId(coreTestIds.colorSchemeIcon("light"))).toBeTruthy();
		expect(storage.getItem(storageKey)).toBe("light");
	});

	it("keeps a chosen scheme when the system setting changes", async () => {
		await renderMenu({ systemScheme: "light" });
		choose("light");

		act(() => system.set("dark"));

		expect(scheme()).toBe("light");
	});

	it("follows the system setting again after the choice system, also when it changes", async () => {
		await renderMenu({ systemScheme: "light" });
		choose("dark");

		choose("system");
		expect(scheme()).toBe("light");
		expect(storage.getItem(storageKey)).toBe("system");

		act(() => system.set("dark"));
		expect(scheme()).toBe("dark");
	});

	it.each<[Mode, "light" | "dark"]>([
		["dark", "dark"],
		["light", "light"],
	])("shows the remembered choice %s again on the next visit", async (stored, expected) => {
		await renderMenu({ stored, systemScheme: stored === "dark" ? "light" : "dark" });

		expect(scheme()).toBe(expected);
		expect(screen.getByTestId(coreTestIds.colorSchemeIcon(stored))).toBeTruthy();
		open();
		expect(checked(stored)).toBe("true");
	});
});
