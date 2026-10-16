import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { useState } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
	ChoiceDialog,
	ConfirmDialog,
	DetailField,
	DetailPanel,
	DetailSection,
	EditForm,
	EntityPicker,
	FilterSection,
	InlineField,
	LargeView,
	MarkdownEditor,
	MarkdownView,
	ProgressRing,
	sharedTestIds,
} from "../../../../../client/src/shared";
import SaveIcon from "@mui/icons-material/Save";

afterEach(cleanup);

describe("ProgressRing", () => {
	it("names done and total and draws a pie for part of the work", () => {
		const { container } = render(<ProgressRing done={1} total={4} />);

		expect(screen.getByTestId(sharedTestIds.progressRing).getAttribute("aria-label")).toBe("1/4");
		expect(container.querySelector("path")).not.toBeNull();
	});

	it("draws a full disc when everything is done and no pie when nothing is", () => {
		const done = render(<ProgressRing done={3} total={3} />);
		expect(done.container.querySelector("path")).toBeNull();
		expect(done.container.querySelectorAll("circle")).toHaveLength(2);
		cleanup();
		const none = render(<ProgressRing done={0} total={3} />);
		expect(none.container.querySelector("path")).toBeNull();
		expect(none.container.querySelectorAll("circle")).toHaveLength(1);
	});

	it("draws nothing without a total", () => {
		const { container } = render(<ProgressRing done={0} total={0} />);
		expect(container.innerHTML).toBe("");
	});
});

describe("DetailPanel", () => {
	it("shows title, subtitle, fields and the actions as icon buttons that work", () => {
		const onClick = vi.fn();
		render(
			<DetailPanel title="Titel" subtitle="STORY-1" actions={[{ id: "save", label: "Speichern", icon: SaveIcon, onClick }]}>
				<DetailField id="status" label="Status">
					Open
				</DetailField>
			</DetailPanel>,
		);

		expect(screen.getByTestId(sharedTestIds.detailTitle).textContent).toBe("Titel");
		expect(screen.getByTestId(sharedTestIds.detailField("status")).textContent).toContain("Open");
		fireEvent.click(screen.getByRole("button", { name: "Speichern" }));
		expect(onClick).toHaveBeenCalledTimes(1);
	});

	it("does not call a disabled action", () => {
		const onClick = vi.fn();
		render(<DetailPanel title="T" actions={[{ id: "x", label: "X", icon: SaveIcon, onClick, disabled: true }]} />);

		fireEvent.click(screen.getByTestId(sharedTestIds.detailAction("x")));

		expect(onClick).not.toHaveBeenCalled();
	});

	it("folds a section in and out and keeps the others", async () => {
		render(
			<DetailPanel title="T">
				<DetailSection id="a" title="A">
					<p>Inhalt A</p>
				</DetailSection>
				<DetailSection id="b" title="B" defaultOpen={false}>
					<p>Inhalt B</p>
				</DetailSection>
			</DetailPanel>,
		);
		expect(screen.getByText("Inhalt A")).toBeTruthy();
		expect(screen.queryByText("Inhalt B")).toBeNull();

		fireEvent.click(screen.getByTestId(sharedTestIds.detailSectionToggle("b")));
		expect(await screen.findByText("Inhalt B")).toBeTruthy();
		fireEvent.click(screen.getByTestId(sharedTestIds.detailSectionToggle("a")));
		await waitFor(() => expect(screen.queryByText("Inhalt A")).toBeNull());
		expect(screen.getByTestId(sharedTestIds.detailSectionToggle("a")).getAttribute("aria-expanded")).toBe("false");
	});
});

describe("InlineField: text", () => {
	const input = () => screen.getByTestId(sharedTestIds.inlineFieldInput("title")) as HTMLInputElement;

	it("saves on leaving the field, only when the text changed", async () => {
		const onSave = vi.fn().mockResolvedValue(undefined);
		render(<InlineField id="title" kind="text" label="Titel" value="alt" onSave={onSave} />);

		fireEvent.blur(input());
		expect(onSave).not.toHaveBeenCalled();
		fireEvent.change(input(), { target: { value: "neu" } });
		fireEvent.blur(input());

		await waitFor(() => expect(onSave).toHaveBeenCalledExactlyOnceWith("neu"));
	});

	it("saves on Enter and drops the edit on Escape", async () => {
		const onSave = vi.fn().mockResolvedValue(undefined);
		render(<InlineField id="title" kind="text" label="Titel" value="alt" onSave={onSave} />);

		fireEvent.change(input(), { target: { value: "x" } });
		fireEvent.keyDown(input(), { key: "Escape" });
		expect(input().value).toBe("alt");
		fireEvent.change(input(), { target: { value: "y" } });
		fireEvent.keyDown(input(), { key: "Enter" });

		await waitFor(() => expect(onSave).toHaveBeenCalledExactlyOnceWith("y"));
	});

	it("shows the error of a failed save at the field and keeps what was typed", async () => {
		const onSave = vi.fn().mockRejectedValue(new Error("Zu kurz"));
		render(<InlineField id="title" kind="text" label="Titel" value="alt" onSave={onSave} />);

		fireEvent.change(input(), { target: { value: "ab" } });
		fireEvent.blur(input());

		expect((await screen.findByTestId(sharedTestIds.inlineFieldError("title"))).textContent).toBe("Zu kurz");
		expect(input().value).toBe("ab");
	});

	it("follows the stored value after a successful save", async () => {
		function Parent() {
			const [value, setValue] = useState("alt");
			return <InlineField id="title" kind="text" label="Titel" value={value} onSave={async (next) => setValue(next.toUpperCase())} />;
		}
		render(<Parent />);

		fireEvent.change(input(), { target: { value: "neu" } });
		fireEvent.blur(input());

		await waitFor(() => expect(input().value).toBe("NEU"));
	});
});

describe("InlineField: choices", () => {
	const options = [
		{ value: "a", label: "Alpha" },
		{ value: "b", label: "Beta" },
	];

	it("saves a choice as soon as it is made", async () => {
		const onSave = vi.fn().mockResolvedValue(undefined);
		render(<InlineField id="status" kind="select" label="Status" value="a" options={options} onSave={onSave} />);

		fireEvent.mouseDown(screen.getByTestId(sharedTestIds.inlineFieldInput("status")));
		fireEvent.click(screen.getByTestId(`${sharedTestIds.inlineFieldInput("status")}.b`));

		await waitFor(() => expect(onSave).toHaveBeenCalledExactlyOnceWith("b"));
		expect(screen.getByTestId(sharedTestIds.inlineFieldInput("status")).textContent).toBe("Alpha");
	});

	it("saves the list of choices of a multiple choice", async () => {
		const onSave = vi.fn().mockResolvedValue(undefined);
		render(<InlineField id="tags" kind="multiselect" label="Tags" value={["a"]} options={options} onSave={onSave} />);

		fireEvent.mouseDown(screen.getByTestId(sharedTestIds.inlineFieldInput("tags")));
		fireEvent.click(screen.getByTestId(`${sharedTestIds.inlineFieldInput("tags")}.b`));

		await waitFor(() => expect(onSave).toHaveBeenCalledExactlyOnceWith(["a", "b"]));
		expect(screen.getByTestId(sharedTestIds.inlineFieldInput("tags")).textContent).toBe("Alpha");
	});

	it("shows an error of a failed choice", async () => {
		render(<InlineField id="status" kind="select" label="Status" value="a" options={options} onSave={() => Promise.reject({ message: "Nicht erlaubt" })} />);

		fireEvent.mouseDown(screen.getByTestId(sharedTestIds.inlineFieldInput("status")));
		fireEvent.click(screen.getByTestId(`${sharedTestIds.inlineFieldInput("status")}.b`));

		expect((await screen.findByTestId(sharedTestIds.inlineFieldError("status"))).textContent).toBe("Nicht erlaubt");
	});
});

describe("EditForm", () => {
	it("saves on submit and cancels", async () => {
		const onSave = vi.fn().mockResolvedValue(undefined);
		const onCancel = vi.fn();
		render(
			<EditForm onSave={onSave} onCancel={onCancel} onReload={vi.fn()}>
				<input aria-label="x" />
			</EditForm>,
		);

		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));
		await waitFor(() => expect(onSave).toHaveBeenCalledTimes(1));
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormCancel));
		expect(onCancel).toHaveBeenCalledTimes(1);
	});

	it("offers to load the current state on a version conflict, and takes the offer back afterwards", async () => {
		const onSave = vi.fn().mockRejectedValue({ code: "version_conflict" });
		const onReload = vi.fn().mockResolvedValue(undefined);
		render(
			<EditForm onSave={onSave} onCancel={vi.fn()} onReload={onReload} labels={{ reload: "Aktuellen Stand laden" }}>
				<input aria-label="x" />
			</EditForm>,
		);

		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));
		expect(await screen.findByTestId(sharedTestIds.editFormConflict)).toBeTruthy();
		expect(screen.getByTestId(sharedTestIds.editFormSave).hasAttribute("disabled")).toBe(true);
		expect(screen.getByTestId(sharedTestIds.editFormReload).textContent).toBe("Aktuellen Stand laden");

		fireEvent.click(screen.getByTestId(sharedTestIds.editFormReload));
		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.editFormConflict)).toBeNull());
		expect(onReload).toHaveBeenCalledTimes(1);
	});

	it("shows any other error", async () => {
		render(
			<EditForm onSave={() => Promise.reject(new Error("Kaputt"))} onCancel={vi.fn()} onReload={vi.fn()}>
				<input aria-label="x" />
			</EditForm>,
		);

		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		expect((await screen.findByTestId(sharedTestIds.editFormError)).textContent).toBe("Kaputt");
		expect(screen.queryByTestId(sharedTestIds.editFormConflict)).toBeNull();
	});
});

describe("MarkdownView and MarkdownEditor", () => {
	it("shows formatted, clean text", () => {
		render(<MarkdownView source={"# Titel\n\n**fett** <script>alert(1)</script>"} />);

		const view = screen.getByTestId(sharedTestIds.markdownView);
		expect(view.querySelector("h1")?.textContent).toBe("Titel");
		expect(view.querySelector("strong")?.textContent).toBe("fett");
		expect(view.querySelector("script")).toBeNull();
	});

	it("shows the preview of what is typed next to the text area", () => {
		function Parent() {
			const [value, setValue] = useState("alt");
			return <MarkdownEditor value={value} onChange={setValue} onSave={async () => {}} onShowCurrent={() => {}} ariaLabel="Notiz" />;
		}
		render(<Parent />);

		fireEvent.change(screen.getByTestId(sharedTestIds.markdownInput), { target: { value: "## Neu" } });

		expect(screen.getByTestId(sharedTestIds.markdownPreview).querySelector("h2")?.textContent).toBe("Neu");
		expect(screen.getByLabelText("Notiz")).toBe(screen.getByTestId(sharedTestIds.markdownInput));
	});

	it("saves, and on a conflict offers to show the current state or to save anyway", async () => {
		const onSave = vi.fn().mockRejectedValueOnce({ code: "version_conflict" }).mockResolvedValue(undefined);
		const onShowCurrent = vi.fn();
		render(<MarkdownEditor value="x" onChange={() => {}} onSave={onSave} onShowCurrent={onShowCurrent} ariaLabel="Notiz" />);

		fireEvent.click(screen.getByTestId(sharedTestIds.markdownSave));
		expect(await screen.findByTestId(sharedTestIds.markdownConflict)).toBeTruthy();
		expect(onSave).toHaveBeenLastCalledWith(false);
		expect(screen.getByTestId(sharedTestIds.markdownSave).hasAttribute("disabled")).toBe(true);

		fireEvent.click(screen.getByTestId(sharedTestIds.markdownShowCurrent));
		expect(onShowCurrent).toHaveBeenCalledTimes(1);
		fireEvent.click(screen.getByTestId(sharedTestIds.markdownSaveAnyway));

		await waitFor(() => expect(onSave).toHaveBeenLastCalledWith(true));
		await waitFor(() => expect(screen.queryByTestId(sharedTestIds.markdownConflict)).toBeNull());
	});
});

describe("LargeView", () => {
	it("shows the document with a table of contents from its headings and jumps to a heading", () => {
		const scroll = vi.fn();
		render(<LargeView open onClose={() => {}} title="Spec" markdown={"# Eins\n\ntext\n\n## Zwei\n\nmehr"} closeLabel="Schließen" tocLabel="Inhalt" />);
		const target = document.getElementById("zwei")!;
		target.scrollIntoView = scroll;

		expect(screen.getByRole("navigation", { name: "Inhalt" })).toBeTruthy();
		expect(screen.getByTestId(sharedTestIds.largeViewTocItem("eins")).textContent).toBe("Eins");
		fireEvent.click(screen.getByTestId(sharedTestIds.largeViewTocItem("zwei")));

		expect(scroll).toHaveBeenCalledTimes(1);
	});

	it("has no table of contents without headings, and closes", () => {
		const onClose = vi.fn();
		render(<LargeView open onClose={onClose} title="Spec" markdown="nur Text" closeLabel="Schließen" tocLabel="Inhalt" />);

		expect(screen.queryByTestId(sharedTestIds.largeViewToc)).toBeNull();
		fireEvent.click(screen.getByRole("button", { name: "Schließen" }));
		expect(onClose).toHaveBeenCalledTimes(1);
	});

	it("renders nothing while closed", () => {
		render(<LargeView open={false} onClose={() => {}} title="Spec" markdown="x" closeLabel="c" tocLabel="t" />);
		expect(screen.queryByTestId(sharedTestIds.largeView)).toBeNull();
	});
});

describe("FilterSection", () => {
	const options = [
		{ value: "open", label: "Open", color: "#6b7280", count: 3 },
		{ value: "done", label: "Done" },
	];

	it("shows the options with their count, and reports the new selection", () => {
		const onChange = vi.fn();
		render(<FilterSection title="Status" options={options} selected={["open"]} onChange={onChange} />);

		expect(screen.getByTestId(sharedTestIds.filterSection).textContent).toContain("3");
		expect((screen.getByTestId(sharedTestIds.filterOption("open")) as HTMLInputElement).checked).toBe(true);
		fireEvent.click(screen.getByTestId(sharedTestIds.filterOption("done")));
		expect(onChange).toHaveBeenLastCalledWith(["open", "done"]);
		fireEvent.click(screen.getByTestId(sharedTestIds.filterOption("open")));
		expect(onChange).toHaveBeenLastCalledWith([]);
	});
});

describe("ConfirmDialog and ChoiceDialog", () => {
	it("confirms and cancels with the texts of the caller", () => {
		const onConfirm = vi.fn();
		const onCancel = vi.fn();
		render(<ConfirmDialog open title="Löschen?" message="Wirklich?" confirmLabel="Ja" cancelLabel="Nein" onConfirm={onConfirm} onCancel={onCancel} />);

		expect(screen.getByRole("dialog").textContent).toContain("Wirklich?");
		fireEvent.click(screen.getByTestId(sharedTestIds.confirmDialogConfirm));
		fireEvent.click(screen.getByTestId(sharedTestIds.confirmDialogCancel));
		expect([onConfirm.mock.calls.length, onCancel.mock.calls.length]).toEqual([1, 1]);
		expect(screen.getByTestId(sharedTestIds.confirmDialogConfirm).textContent).toBe("Ja");
	});

	it("reports the chosen way", () => {
		const onChoose = vi.fn();
		render(
			<ChoiceDialog
				open
				title="Konflikt"
				choices={[
					{ value: "database", label: "Datenbank", description: "Die DB gewinnt" },
					{ value: "files", label: "Datei" },
				]}
				cancelLabel="Später"
				onChoose={onChoose}
				onCancel={() => {}}
			/>,
		);

		fireEvent.click(screen.getByTestId(sharedTestIds.choiceDialogOption("files")));

		expect(onChoose).toHaveBeenCalledExactlyOnceWith("files");
		expect(screen.getByTestId(sharedTestIds.choiceDialogOption("database")).textContent).toContain("Die DB gewinnt");
	});

	it("renders nothing while closed", () => {
		render(<ConfirmDialog open={false} title="t" message="m" confirmLabel="a" cancelLabel="b" onConfirm={() => {}} onCancel={() => {}} />);
		expect(screen.queryByRole("dialog")).toBeNull();
	});
});

describe("EntityPicker", () => {
	const options = [
		{ id: "u1", label: "STORY-001", title: "Erste" },
		{ id: "u2", label: "TASK-002", title: "Zweite" },
	];
	const open = () => fireEvent.keyDown(screen.getByRole("combobox"), { key: "ArrowDown" });

	it("shows the chosen element as 'label — title' and chooses one", () => {
		const onChange = vi.fn();
		render(<EntityPicker label="Parent" options={options} value="u1" onChange={onChange} />);

		expect((screen.getByRole("combobox") as HTMLInputElement).value).toBe("STORY-001 — Erste");
		open();
		fireEvent.click(screen.getByText("TASK-002 — Zweite"));
		expect(onChange).toHaveBeenCalledExactlyOnceWith("u2");
	});

	it("chooses several and reports their ids", () => {
		const onChange = vi.fn();
		render(<EntityPicker multiple label="Abhängigkeiten" options={options} value={["u1"]} onChange={onChange} />);

		open();
		fireEvent.click(screen.getByText("TASK-002 — Zweite"));

		expect(onChange).toHaveBeenCalledExactlyOnceWith(["u1", "u2"]);
	});

	it("cannot choose a disabled element", () => {
		const onChange = vi.fn();
		render(<EntityPicker label="Parent" options={options} value={null} disabledIds={["u2"]} onChange={onChange} />);

		open();

		expect(screen.getByText("TASK-002 — Zweite").getAttribute("aria-disabled")).toBe("true");
		expect(screen.getByText("STORY-001 — Erste").getAttribute("aria-disabled")).toBe("false");
		expect(onChange).not.toHaveBeenCalled();
	});

	it("clears the choice", () => {
		const onChange = vi.fn();
		render(<EntityPicker label="Parent" options={options} value="u1" onChange={onChange} />);

		fireEvent.click(screen.getByLabelText("Clear"));

		expect(onChange).toHaveBeenCalledExactlyOnceWith(null);
	});
});
