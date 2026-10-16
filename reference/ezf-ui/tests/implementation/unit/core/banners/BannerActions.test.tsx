import { ThemeProvider } from "@mui/material";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BannerHost } from "../../../../../src/core/banners/BannerHost";
import { coreTestIds, createBanners, initI18n, theme, type BannerHandle, type BannerRequest } from "../../../../../src/core";
import type { UnhandledErrors } from "../../../../../src/core/errors/createUnhandledErrors";

async function renderHost(lng = "de") {
	const i18n = await initI18n({ lng });
	const list = createBanners();
	const unhandled: UnhandledErrors = { report: vi.fn(), warn: vi.fn(), fatal: vi.fn() };
	render(
		<I18nextProvider i18n={i18n}>
			<ThemeProvider theme={theme}>
				<BannerHost banners={list} unhandled={unhandled} />
			</ThemeProvider>
		</I18nextProvider>,
	);
	const show = (request: BannerRequest) => {
		let handle: BannerHandle | undefined;
		act(() => {
			handle = list.show(request);
		});
		return handle!;
	};
	return { list, show, unhandled };
}

const button = (index: number) => screen.getByTestId(coreTestIds.bannerAction(index)) as HTMLButtonElement;

describe("BannerHost: buttons", () => {
	afterEach(cleanup);

	it("shows a button for each action with its text in the active language, in the order of the actions", async () => {
		const { show } = await renderHost("de");

		show({
			message: "Frage",
			actions: [
				{ label: "Rückgängig", onClick: () => {} },
				{ label: { key: "banners.close" }, onClick: () => {} },
			],
		});

		expect(button(0).textContent).toBe("Rückgängig");
		expect(button(1).textContent).toBe("Schließen");
		expect(Boolean(button(0).compareDocumentPosition(button(1)) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
	});

	it("shows no button for a banner without actions", async () => {
		const { show } = await renderHost();

		show({ message: "ohne" });

		expect(screen.queryByTestId(coreTestIds.bannerAction(0))).toBeNull();
	});

	it("calls the function of the button with the handle of its banner", async () => {
		const { show } = await renderHost();
		const onClick = vi.fn();
		const handle = show({ message: "Frage", actions: [{ label: "Ja", onClick }] });

		fireEvent.click(button(0));
		await act(async () => {});

		expect(onClick).toHaveBeenCalledExactlyOnceWith(handle);
	});

	it("closes the banner after the function has run", async () => {
		const { list, show } = await renderHost();
		show({ message: "Frage", actions: [{ label: "Ja", onClick: () => {} }] });

		fireEvent.click(button(0));
		await act(async () => {});

		expect(list.getSnapshot()).toEqual([]);
	});

	it("keeps the banner open after the click when the button has `keepOpen`", async () => {
		const { list, show } = await renderHost();
		show({ message: "Details", actions: [{ label: "Anzeigen", onClick: () => {}, keepOpen: true }] });

		fireEvent.click(button(0));
		await act(async () => {});

		expect(list.getSnapshot()).toHaveLength(1);
		expect(screen.getByTestId(coreTestIds.banner)).toBeTruthy();
	});

	it("disables the button while an asynchronous function runs, calls it only once, and closes the banner afterwards", async () => {
		const { list, show } = await renderHost();
		let finish!: () => void;
		const onClick = vi.fn(() => new Promise<void>((resolve) => (finish = resolve)));
		show({ message: "Senden", actions: [{ label: "Senden", onClick }] });

		fireEvent.click(button(0));
		expect(button(0).disabled).toBe(true);
		fireEvent.click(button(0));
		expect(onClick).toHaveBeenCalledTimes(1);
		expect(list.getSnapshot()).toHaveLength(1);

		await act(async () => finish());
		expect(list.getSnapshot()).toEqual([]);
	});

	it("keeps the banner and reports the error to the central handling when the function throws", async () => {
		const { list, show, unhandled } = await renderHost();
		const error = new Error("kaputt");
		show({
			message: "Frage",
			actions: [
				{
					label: "Ja",
					onClick: () => {
						throw error;
					},
				},
			],
		});

		fireEvent.click(button(0));
		await act(async () => {});

		expect(unhandled.report).toHaveBeenCalledExactlyOnceWith(error, { action: "banner-action" });
		expect(list.getSnapshot()).toHaveLength(1);
		expect(button(0).disabled).toBe(false);
	});

	it("keeps the banner and reports the error when the promise of the function is rejected", async () => {
		const { list, show, unhandled } = await renderHost();
		const error = new Error("abgelehnt");
		show({ message: "Frage", actions: [{ label: "Ja", onClick: () => Promise.reject(error) }] });

		fireEvent.click(button(0));
		await act(async () => {});

		expect(unhandled.report).toHaveBeenCalledExactlyOnceWith(error, { action: "banner-action" });
		expect(list.getSnapshot()).toHaveLength(1);
		expect(button(0).disabled).toBe(false);
	});

	it("keeps the X next to the buttons", async () => {
		const { show } = await renderHost();

		show({ message: "Frage", actions: [{ label: "Ja", onClick: () => {} }] });

		expect(screen.getByTestId(coreTestIds.bannerClose)).toBeTruthy();
	});
});
