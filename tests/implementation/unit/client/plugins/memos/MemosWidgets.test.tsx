import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { CreateMemo, CreateTopic } from "../../../../../../client/src/plugins/memos/CreateForms";
import { MemosAttention } from "../../../../../../client/src/plugins/memos/MemosAttention";
import { MemosSettings } from "../../../../../../client/src/plugins/memos/MemosSettings";
import { NewButton } from "../../../../../../client/src/plugins/workspace/NewButton";
import { ProjectsSection } from "../../../../../../client/src/plugins/workspace/ProjectsSection";
import { workspaceTestIds } from "../../../../../../client/src/plugins/workspace/testIds";
import { memosTestIds as ids } from "../../../../../../client/src/plugins/memos/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { fakeMemosBackend } from "../../../../../helpers/client/fakeMemosBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { dueMemo } from "../../../../../helpers/client/memosFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];

afterEach(() => {
	cleanup();
	document.title = "";
});

describe("MemosAttention in the bell of the projects section", () => {
	const due = {
		count: 2,
		memos: [
			dueMemo("n1", { label: "MEMO-001", summary: "Eins", reason: "trigger", due_since: "2026-10-18T07:00:00Z" }),
			dueMemo("n2", { label: "MEMO-002", summary: "Zwei", review_at: "2026-10-18T09:00:00Z", due_since: "2026-10-18T09:00:00Z" }),
		],
	};
	const widgets = [{ ownerId: "memos", slot: "workspace.attention-sources", name: "due", component: MemosAttention }];

	it("reports nothing when no memo is due", async () => {
		await renderWorkspace(<ProjectsSection />, { backend: fakeMemosBackend({ projects }), widgets });

		await screen.findByTestId(workspaceTestIds.project("p1"));
		await waitFor(() => expect(screen.queryByTestId(workspaceTestIds.attentionBell)).toBeNull());
	});

	it("counts the due memos, puts the number into the tab title, and lists them the latest first", async () => {
		document.title = "ToDo-Viewer";
		await renderWorkspace(<ProjectsSection />, { backend: fakeMemosBackend({ projects, due }), widgets });

		const bell = await screen.findByTestId(workspaceTestIds.attentionBell);
		expect(bell.getAttribute("aria-label")).toBe("2 fällig");
		await waitFor(() => expect(document.title).toBe("(2) ToDo-Viewer"));

		fireEvent.click(bell);
		const items = (await screen.findByTestId(workspaceTestIds.attentionList)).querySelectorAll("[data-testid^='workspace.attention-item.']");
		expect([...items].map((item) => item.textContent?.slice(0, 15))).toEqual(["MEMO-002 — Zwei", "MEMO-001 — Eins"]);
	});

	it("remembers the chosen memo as the selected one", async () => {
		const backend = fakeMemosBackend({ projects, due });
		await renderWorkspace(<ProjectsSection />, { backend, widgets });

		fireEvent.click(await screen.findByTestId(workspaceTestIds.attentionBell));
		fireEvent.click(await screen.findByTestId(workspaceTestIds.attentionOpen("memos:n2")));

		await waitFor(async () => {
			const { flushUiState } = await import("../../../../../../client/src/core/ui-state/uiState");
			await flushUiState(backend.store);
			expect((backend.documents.get("memos") as { selected?: string }).selected).toBe("n2");
		});
	});
});

describe("MemosSettings", () => {
	it("shows the settings and saves the changed values", async () => {
		const backend = fakeMemosBackend({ projects, settings: { max_topic_depth: 3, review_days: 30 } });
		await renderWorkspace(<MemosSettings />, { backend });

		const days = (await screen.findByTestId(ids.settingsField("review_days"))) as HTMLInputElement;
		expect(days.value).toBe("30");
		expect((screen.getByTestId(ids.settingsField("max_topic_depth")) as HTMLInputElement).value).toBe("3");
		fireEvent.change(days, { target: { value: "14" } });
		fireEvent.change(screen.getByTestId(ids.settingsField("max_topic_depth")), { target: { value: "5" } });
		fireEvent.click(screen.getByTestId(ids.settingsSave));

		await waitFor(() => expect(backend.calls("PUT", "memos/settings")).toHaveLength(1));
		expect(backend.calls("PUT", "memos/settings")[0]!.body).toEqual({ review_days: 14, max_topic_depth: 5 });
		expect(await screen.findByText("Gespeichert.")).toBeTruthy();
	});

	it("shows the message of the server when the values are refused", async () => {
		await renderWorkspace(<MemosSettings />, {
			backend: fakeMemosBackend({
				projects,
				respond: ({ method, path }) =>
					method === "PUT" && path === "memos/settings" ? Response.json({ code: "invalid_input", message: "review_days muss zwischen 1 und 3650 liegen", details: {} }, { status: 422 }) : undefined,
			}),
		});

		fireEvent.click(await screen.findByTestId(ids.settingsSave));

		expect(await screen.findByText("review_days muss zwischen 1 und 3650 liegen")).toBeTruthy();
	});
});

describe("create forms of the dialog '＋ New'", () => {
	const types = [
		{ ownerId: "memos", name: "memo", title: "Neues Memo", form: CreateMemo },
		{ ownerId: "memos", name: "topic", title: "Neues Topic", form: CreateTopic },
	];

	it("creates a memo in the marked project", async () => {
		const backend = fakeMemosBackend({ projects, documents: { workspace: { marked: "p1" } } });
		await renderWorkspace(<NewButton />, { backend, createTypes: types });

		fireEvent.click(screen.getByTestId(workspaceTestIds.newButton));
		fireEvent.click(await screen.findByTestId(workspaceTestIds.newMenuItem("memo")));
		fireEvent.change(await screen.findByTestId(ids.formField("summary")), { target: { value: "Aus dem Menü" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("POST", "memos/memos")).toHaveLength(1));
		expect(backend.calls("POST", "memos/memos")[0]!.body).toEqual({ project: "p1", fields: { summary: "Aus dem Menü" } });
		await waitFor(() => expect(screen.queryByTestId(workspaceTestIds.newDialog)).toBeNull());
	});

	it("creates a topic in the built-in project by default", async () => {
		const backend = fakeMemosBackend({ projects });
		await renderWorkspace(<NewButton />, { backend, createTypes: types });
		await waitFor(() => expect(screen.getByTestId(workspaceTestIds.newButton)).toBeTruthy());

		fireEvent.click(screen.getByTestId(workspaceTestIds.newButton));
		fireEvent.click(await screen.findByTestId(workspaceTestIds.newMenuItem("topic")));
		await waitFor(() => expect(screen.getByTestId(ids.topicField("name"))).toBeTruthy());
		fireEvent.change(screen.getByTestId(ids.topicField("name")), { target: { value: "Ideen" } });
		fireEvent.click(screen.getByTestId(sharedTestIds.editFormSave));

		await waitFor(() => expect(backend.calls("POST", "memos/topics")).toHaveLength(1));
		expect(backend.calls("POST", "memos/topics")[0]!.body).toEqual({ project: "p0", name: "Ideen", parent: null, due_at: null });
	});
});
