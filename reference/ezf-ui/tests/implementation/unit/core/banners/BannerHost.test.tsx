import { ThemeProvider } from "@mui/material";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { BannerHost } from "../../../../../src/core/banners/BannerHost";
import { coreTestIds, createBanners, initI18n, theme, type BannerHandle, type BannerRequest } from "../../../../../src/core";

async function renderHost(lng = "de") {
	const i18n = await initI18n({ lng });
	i18n.addResourceBundle("de", "core", { test: { attempts: "Fehlgeschlagene Versuche: {{count}}" } }, true, true);
	const list = createBanners();
	render(
		<I18nextProvider i18n={i18n}>
			<ThemeProvider theme={theme}>
				<BannerHost banners={list} />
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
	return { list, show };
}

const texts = () => screen.getAllByTestId(coreTestIds.bannerMessage).map((element) => element.textContent);

describe("BannerHost: display", () => {
	afterEach(cleanup);

	it("renders nothing while there is no banner", async () => {
		await renderHost();

		expect(screen.queryByTestId(coreTestIds.bannerHost)).toBeNull();
	});

	it("shows the message of a banner in the host", async () => {
		const { show } = await renderHost();

		show({ message: "Hallo" });

		expect(screen.getByTestId(coreTestIds.bannerHost).contains(screen.getByTestId(coreTestIds.banner))).toBe(true);
		expect(screen.getByTestId(coreTestIds.bannerMessage).textContent).toBe("Hallo");
	});

	it("shows several banners one below the other, the oldest on top", async () => {
		const { show } = await renderHost();

		show({ message: "eins" });
		show({ message: "zwei" });

		expect(texts()).toEqual(["eins", "zwei"]);
		const [first, second] = screen.getAllByTestId(coreTestIds.banner);
		expect(Boolean(first!.compareDocumentPosition(second!) & Node.DOCUMENT_POSITION_FOLLOWING)).toBe(true);
	});

	it("shows the severity, `info` by default", async () => {
		const { show } = await renderHost();

		show({ message: "eins" });
		show({ message: "zwei", severity: "warning" });

		expect(screen.getAllByTestId(coreTestIds.banner).map((element) => element.getAttribute("data-severity"))).toEqual(["info", "warning"]);
	});

	it("shows a title only when the banner has one", async () => {
		const { show } = await renderHost();

		show({ message: "ohne" });
		expect(screen.queryByTestId(coreTestIds.bannerTitle)).toBeNull();

		show({ message: "mit", title: "Achtung" });
		expect(screen.getByTestId(coreTestIds.bannerTitle).textContent).toBe("Achtung");
	});

	it("translates a key with its parameters when it is shown, and follows an update of the text", async () => {
		const { show } = await renderHost("de");

		const handle = show({ message: { key: "test.attempts", params: { count: 3 } } });
		expect(texts()).toEqual(["Fehlgeschlagene Versuche: 3"]);

		act(() => handle.update({ message: { key: "test.attempts", params: { count: 4 } } }));
		expect(texts()).toEqual(["Fehlgeschlagene Versuche: 4"]);
	});
});

describe("BannerHost: the X", () => {
	afterEach(cleanup);

	it("shows a button to close the banner by default, named in the active language", async () => {
		const { show } = await renderHost("en");

		show({ message: "eins" });

		expect(screen.getByTestId(coreTestIds.bannerClose).getAttribute("aria-label")).toBe("Close");
	});

	it("closes the banner when the X is clicked, and the host disappears with the last banner", async () => {
		const { list, show } = await renderHost();
		show({ message: "eins" });
		show({ message: "zwei" });

		fireEvent.click(screen.getAllByTestId(coreTestIds.bannerClose)[0]!);
		expect(texts()).toEqual(["zwei"]);

		fireEvent.click(screen.getByTestId(coreTestIds.bannerClose));
		expect(list.getSnapshot()).toEqual([]);
		expect(screen.queryByTestId(coreTestIds.bannerHost)).toBeNull();
	});

	it("shows no X for a banner with `dismissible: false`", async () => {
		const { show } = await renderHost();

		show({ message: "eins", dismissible: false });

		expect(screen.queryByTestId(coreTestIds.bannerClose)).toBeNull();
	});
});
