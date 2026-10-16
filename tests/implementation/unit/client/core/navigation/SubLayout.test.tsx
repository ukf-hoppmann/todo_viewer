import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useState, type ComponentType } from "react";
import { I18nextProvider } from "react-i18next";
import { afterEach, describe, expect, it } from "vitest";
import { coreTestIds, initI18n } from "../../../../../../client/src/core";
import { logging } from "../../../../../../client/src/core/logging/logging";
import { MemorySink } from "../../../../../../client/src/core/logging/MemorySink";
import { PageHost } from "../../../../../../client/src/core/navigation/PageHost";
import { SubLayout } from "../../../../../../client/src/core/navigation/SubLayout";
import { usePageHeader } from "../../../../../../client/src/core/navigation/usePageHeader";

function PageWithHeader({ title = "Kopfzeile" }: { title?: string }) {
	usePageHeader(<h2>{title}</h2>);
	return <p>Inhalt</p>;
}

async function renderLayout(ui: React.ReactNode) {
	const i18n = await initI18n({ lng: "en" });
	return render(<I18nextProvider i18n={i18n}>{ui}</I18nextProvider>);
}

describe("SubLayout", () => {
	afterEach(cleanup);

	it("shows the page in the content area", async () => {
		await renderLayout(
			<SubLayout header={false}>
				<p>Inhalt</p>
			</SubLayout>,
		);

		expect(screen.getByTestId(coreTestIds.content).textContent).toBe("Inhalt");
	});

	it("has no header area unless the main route asks for it", async () => {
		await renderLayout(
			<SubLayout header={false}>
				<p>Inhalt</p>
			</SubLayout>,
		);

		expect(screen.queryByTestId(coreTestIds.pageHeader)).toBeNull();
	});

	it("shows what the page puts into the header", async () => {
		await renderLayout(
			<SubLayout header>
				<PageWithHeader />
			</SubLayout>,
		);

		expect(screen.getByTestId(coreTestIds.pageHeader).textContent).toBe("Kopfzeile");
		expect(screen.getByTestId(coreTestIds.content).textContent).toBe("Inhalt");
	});

	it("reserves the header area before the page has loaded", async () => {
		await renderLayout(
			<SubLayout header>
				<PageHost ownerId="example" load={() => new Promise(() => undefined)} />
			</SubLayout>,
		);

		expect(screen.getByTestId(coreTestIds.pageHeader)).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.loading)).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.pageHeader).textContent).toBe("");
	});

	it("follows the page when its header changes", async () => {
		function Changing() {
			const [title, setTitle] = useState("eins");
			return (
				<>
					<button onClick={() => setTitle("zwei")}>ändern</button>
					<PageWithHeader title={title} />
				</>
			);
		}
		await renderLayout(
			<SubLayout header>
				<Changing />
			</SubLayout>,
		);
		expect(screen.getByTestId(coreTestIds.pageHeader).textContent).toBe("eins");

		fireEvent.click(screen.getByText("ändern"));

		expect(screen.getByTestId(coreTestIds.pageHeader).textContent).toBe("zwei");
	});

	it("removes the header content together with the page", async () => {
		function Switch() {
			const [shown, setShown] = useState(true);
			return (
				<>
					<button onClick={() => setShown(false)}>wechseln</button>
					{shown ? <PageWithHeader /> : <p>andere Seite</p>}
				</>
			);
		}
		await renderLayout(
			<SubLayout header>
				<Switch />
			</SubLayout>,
		);
		expect(screen.getByTestId(coreTestIds.pageHeader).textContent).toBe("Kopfzeile");

		fireEvent.click(screen.getByText("wechseln"));

		expect(screen.getByText("andere Seite")).toBeTruthy();
		expect(screen.getByTestId(coreTestIds.pageHeader).textContent).toBe("");
	});

	it("shows nothing and warns in development when a page sets a header the main route did not ask for", async () => {
		const sink = new MemorySink("sub-layout-warning-test");
		logging.addSink(sink, { level: "debug" });

		await renderLayout(
			<SubLayout header={false}>
				<PageHost ownerId="example" load={async () => ({ default: PageWithHeader as ComponentType })} />
			</SubLayout>,
		);
		await screen.findByText("Inhalt");

		expect(screen.queryByText("Kopfzeile")).toBeNull();
		expect(sink.entries.filter((entry) => entry.level === "warn")).toEqual([
			expect.objectContaining({ origin: "example", action: "page-header" }),
		]);
		logging.removeSink(sink.name);
	});

	it("does nothing when a page outside of a sub layout sets a header", async () => {
		await renderLayout(<PageWithHeader />);

		expect(screen.getByText("Inhalt")).toBeTruthy();
		expect(screen.queryByText("Kopfzeile")).toBeNull();
	});
});
