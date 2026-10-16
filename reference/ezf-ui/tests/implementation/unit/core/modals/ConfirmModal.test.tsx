import { act, cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { coreTestIds } from "../../../../../src/core";
import type { ConfirmBodyProps } from "../../../../../src/core/modals/types";
import { renderHost } from "../../../../helpers/renderHost";

afterEach(() => {
	cleanup();
	vi.restoreAllMocks();
});

describe("confirm", () => {
	it("shows title, message and the default button texts", async () => {
		const { modals } = await renderHost();

		act(() => {
			void modals.confirm({ title: "Leave?", message: "Changes are lost" });
		});

		expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("Leave?");
		expect(screen.getByTestId(coreTestIds.modalMessage).textContent).toBe("Changes are lost");
		expect(screen.getByTestId(coreTestIds.modalConfirm).textContent).toBe("Confirm");
		expect(screen.getByTestId(coreTestIds.modalCancel).textContent).toBe("Cancel");
		expect(screen.queryByTestId(coreTestIds.modalBody)).toBeNull();
	});

	it("uses the default title and texts in the language of the app", async () => {
		const { modals } = await renderHost("de");

		act(() => {
			void modals.confirm({});
		});

		expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("Bestätigung erforderlich");
		expect(screen.getByTestId(coreTestIds.modalConfirm).textContent).toBe("Bestätigen");
		expect(screen.getByTestId(coreTestIds.modalCancel).textContent).toBe("Abbrechen");
		expect(screen.queryByTestId(coreTestIds.modalMessage)).toBeNull();
	});

	it("shows custom button texts, as keys or finished texts", async () => {
		const { modals } = await renderHost();

		act(() => {
			void modals.confirm({ confirmText: "Continue", cancelText: { key: "modals.close" } });
		});

		expect(screen.getByTestId(coreTestIds.modalConfirm).textContent).toBe("Continue");
		expect(screen.getByTestId(coreTestIds.modalCancel).textContent).toBe("Close");
	});

	it("puts Cancel before Confirm", async () => {
		const { modals } = await renderHost();
		act(() => {
			void modals.confirm({});
		});

		const cancel = screen.getByTestId(coreTestIds.modalCancel);
		const confirm = screen.getByTestId(coreTestIds.modalConfirm);

		expect(cancel.compareDocumentPosition(confirm) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
	});

	it("resolves true when confirmed", async () => {
		const { modals } = await renderHost();
		let result: Promise<boolean> | undefined;
		act(() => {
			result = modals.confirm({});
		});

		fireEvent.click(screen.getByTestId(coreTestIds.modalConfirm));

		expect(await result).toBe(true);
		await waitFor(() => expect(screen.queryByTestId(coreTestIds.modal)).toBeNull());
	});

	it("resolves false when cancelled", async () => {
		const { modals } = await renderHost();
		let result: Promise<boolean> | undefined;
		act(() => {
			result = modals.confirm({});
		});

		fireEvent.click(screen.getByTestId(coreTestIds.modalCancel));

		expect(await result).toBe(false);
	});

	it("neither Escape nor a click outside closes it", async () => {
		const { modals } = await renderHost();
		const done = vi.fn();
		act(() => {
			void modals.confirm({}).then(done);
		});

		fireEvent.keyDown(screen.getByTestId(coreTestIds.modal), { key: "Escape" });
		await new Promise((resolve) => setTimeout(resolve, 20));

		expect(done).not.toHaveBeenCalled();
		expect(screen.getByTestId(coreTestIds.modal)).toBeDefined();
	});

	it("shows queued confirmations and alerts one after another", async () => {
		const { modals } = await renderHost();
		act(() => {
			void modals.confirm({ title: "first" });
			void modals.alert({ title: "second" });
		});
		expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("first");

		fireEvent.click(screen.getByTestId(coreTestIds.modalConfirm));

		await waitFor(() => expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("second"));
	});
});

interface FormData {
	selected: string;
	count: number;
}

function Body({ data, setData, updateData }: ConfirmBodyProps<FormData>) {
	return (
		<div>
			<span data-testid="test.selected">{data.selected}</span>
			<span data-testid="test.count">{data.count}</span>
			<button data-testid="test.set" onClick={() => setData({ selected: "set", count: 10 })} />
			<button data-testid="test.update" onClick={() => updateData({ selected: "updated" })} />
			<button
				data-testid="test.update-twice"
				onClick={() => {
					updateData({ selected: "twice" });
					updateData({ count: 7 });
				}}
			/>
		</div>
	);
}

const initialData: FormData = { selected: "", count: 0 };

describe("confirmWithBody", () => {
	it("shows message and body with the initial data", async () => {
		const { modals } = await renderHost();

		act(() => {
			void modals.confirmWithBody<FormData>({
				message: "Choose",
				initialData: { selected: "a", count: 1 },
				body: (props) => <Body {...props} />,
			});
		});

		expect(screen.getByTestId(coreTestIds.modalMessage).textContent).toBe("Choose");
		expect(screen.getByTestId(coreTestIds.modalBody)).toBeDefined();
		expect(screen.getByTestId("test.selected").textContent).toBe("a");
		expect(screen.getByTestId("test.count").textContent).toBe("1");
	});

	it("replaces the data with setData", async () => {
		const { modals } = await renderHost();
		act(() => {
			void modals.confirmWithBody<FormData>({ initialData, body: (props) => <Body {...props} /> });
		});

		fireEvent.click(screen.getByTestId("test.set"));

		expect(screen.getByTestId("test.selected").textContent).toBe("set");
		expect(screen.getByTestId("test.count").textContent).toBe("10");
	});

	it("merges a partial object with updateData", async () => {
		const { modals } = await renderHost();
		act(() => {
			void modals.confirmWithBody<FormData>({
				initialData: { selected: "a", count: 3 },
				body: (props) => <Body {...props} />,
			});
		});

		fireEvent.click(screen.getByTestId("test.update"));

		expect(screen.getByTestId("test.selected").textContent).toBe("updated");
		expect(screen.getByTestId("test.count").textContent).toBe("3");
	});

	it("returns the last data when confirmed", async () => {
		const { modals } = await renderHost();
		let result: ReturnType<typeof modals.confirmWithBody<FormData>> | undefined;
		act(() => {
			result = modals.confirmWithBody<FormData>({ initialData, body: (props) => <Body {...props} /> });
		});
		fireEvent.click(screen.getByTestId("test.update"));

		fireEvent.click(screen.getByTestId(coreTestIds.modalConfirm));

		expect(await result).toEqual({ confirmed: true, data: { selected: "updated", count: 0 } });
	});

	it("returns the last data when cancelled", async () => {
		const { modals } = await renderHost();
		let result: ReturnType<typeof modals.confirmWithBody<FormData>> | undefined;
		act(() => {
			result = modals.confirmWithBody<FormData>({ initialData, body: (props) => <Body {...props} /> });
		});
		fireEvent.click(screen.getByTestId("test.set"));

		fireEvent.click(screen.getByTestId(coreTestIds.modalCancel));

		expect(await result).toEqual({ confirmed: false, data: { selected: "set", count: 10 } });
	});

	it("keeps several updates made in one event", async () => {
		const { modals } = await renderHost();
		let result: ReturnType<typeof modals.confirmWithBody<FormData>> | undefined;
		act(() => {
			result = modals.confirmWithBody<FormData>({ initialData, body: (props) => <Body {...props} /> });
		});

		fireEvent.click(screen.getByTestId("test.update-twice"));
		fireEvent.click(screen.getByTestId(coreTestIds.modalConfirm));

		expect(await result).toEqual({ confirmed: true, data: { selected: "twice", count: 7 } });
	});

	it("starts every request with its own initial data", async () => {
		const { modals } = await renderHost();
		act(() => {
			void modals.confirmWithBody<FormData>({
				initialData: { selected: "first", count: 1 },
				body: (props) => <Body {...props} />,
			});
			void modals.confirmWithBody<FormData>({
				initialData: { selected: "second", count: 2 },
				body: (props) => <Body {...props} />,
			});
		});
		fireEvent.click(screen.getByTestId("test.set"));

		fireEvent.click(screen.getByTestId(coreTestIds.modalConfirm));

		await waitFor(() => expect(screen.getByTestId("test.selected").textContent).toBe("second"));
		expect(screen.getByTestId("test.count").textContent).toBe("2");
	});

	it("neither Escape nor a click outside closes it", async () => {
		const { modals } = await renderHost();
		const done = vi.fn();
		act(() => {
			void modals.confirmWithBody<FormData>({ initialData, body: (props) => <Body {...props} /> }).then(done);
		});

		fireEvent.keyDown(screen.getByTestId(coreTestIds.modal), { key: "Escape" });
		await new Promise((resolve) => setTimeout(resolve, 20));

		expect(done).not.toHaveBeenCalled();
	});

	it("answers with confirmed false and the last data when the body throws, and goes on", async () => {
		vi.spyOn(console, "error").mockImplementation(() => {});
		const { modals } = await renderHost();
		let broken: ReturnType<typeof modals.confirmWithBody<FormData>> | undefined;
		let next: Promise<boolean> | undefined;
		act(() => {
			broken = modals.confirmWithBody<FormData>({
				initialData: { selected: "start", count: 0 },
				body: () => {
					throw new Error("render failed");
				},
			});
			next = modals.confirm({ title: "still works" });
		});

		expect(await broken).toEqual({ confirmed: false, data: { selected: "start", count: 0 } });
		await waitFor(() => expect(screen.getByTestId(coreTestIds.modalTitle).textContent).toBe("still works"));
		fireEvent.click(screen.getByTestId(coreTestIds.modalConfirm));
		expect(await next).toBe(true);
	});
});
