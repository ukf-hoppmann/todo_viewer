import { cleanup, render, screen } from "@testing-library/react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { coreTestIds, initI18n } from "../../../../../src/core";
import { SubLayout } from "../../../../../src/core/navigation/SubLayout";

async function renderLayout(ui: React.ReactNode) {
	const i18n = await initI18n({ lng: "en" });
	return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);
}

const sidebar = <nav data-testid={coreTestIds.sidebar}>Seitenleiste</nav>;

describe("SubLayout with a sidebar", () => {
	afterEach(cleanup);

	it("shows the sidebar next to the content", async () => {
		await renderLayout(
			<SubLayout header={false} sidebar={sidebar}>
				<p>Inhalt</p>
			</SubLayout>,
		);

		expect(screen.getByTestId(coreTestIds.sidebar).textContent).toBe("Seitenleiste");
		expect(screen.getByTestId(coreTestIds.content).textContent).toBe("Inhalt");
		const sidebarElement = screen.getByTestId(coreTestIds.sidebar);
		const content = screen.getByTestId(coreTestIds.content);
		expect(sidebarElement.compareDocumentPosition(content) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	});

	it("puts the header above the sidebar and the content", async () => {
		await renderLayout(
			<SubLayout header sidebar={sidebar}>
				<p>Inhalt</p>
			</SubLayout>,
		);

		const header = screen.getByTestId(coreTestIds.pageHeader);
		expect(header.compareDocumentPosition(screen.getByTestId(coreTestIds.sidebar)) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
		expect(header.compareDocumentPosition(screen.getByTestId(coreTestIds.content)) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	});

	it("separates the sidebar from the content with a vertical line", async () => {
		await renderLayout(
			<SubLayout header={false} sidebar={sidebar}>
				<p>Inhalt</p>
			</SubLayout>,
		);

		expect(screen.getByRole("separator").getAttribute("aria-orientation")).toBe("vertical");
	});

	it("has neither sidebar nor separator without one", async () => {
		await renderLayout(
			<SubLayout header={false}>
				<p>Inhalt</p>
			</SubLayout>,
		);

		expect(screen.queryByTestId(coreTestIds.sidebar)).toBeNull();
		expect(screen.queryByRole("separator")).toBeNull();
	});
});
