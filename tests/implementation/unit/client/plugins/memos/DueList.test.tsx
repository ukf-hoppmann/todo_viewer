import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { attentionOf } from "../../../../../../client/src/plugins/memos/model";
import { MemosAttention } from "../../../../../../client/src/plugins/memos/MemosAttention";
import { memosTestIds as ids } from "../../../../../../client/src/plugins/memos/testIds";
import { ProjectsSection } from "../../../../../../client/src/plugins/workspace/ProjectsSection";
import { workspaceTestIds } from "../../../../../../client/src/plugins/workspace/testIds";
import { fakeMemosBackend } from "../../../../../helpers/client/fakeMemosBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { dueMemo } from "../../../../../helpers/client/memosFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const projects = [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)];
const hint = { uid: "x1", kind: "item_completed", created_at: "2026-10-17T00:00:00Z", source: null, decisions: ["keep", "detach", "drop", "promote"] };
const due = {
	count: 2,
	memos: [
		dueMemo("a", { reason: "review_expired", version: 2, path: ["Oben", "Unten"], due_since: "2026-10-18T09:00:00Z" }),
		dueMemo("c", { reason: "hint", version: 5, hints: [hint], due_since: "2026-10-17T00:00:00Z" }),
	],
};

afterEach(() => {
	cleanup();
	document.title = "";
});

/** Opens the bell and unfolds every entry, so all actions can be clicked. */
async function renderOpen() {
	const backend = fakeMemosBackend({ projects, due });
	await renderWorkspace(<ProjectsSection />, {
		backend,
		widgets: [{ ownerId: "memos", slot: "workspace.attention-sources", name: "due", component: MemosAttention }],
	});
	fireEvent.click(await screen.findByTestId(workspaceTestIds.attentionBell));
	await screen.findByTestId(workspaceTestIds.attentionList);
	fireEvent.click(screen.getByTestId(workspaceTestIds.attentionToggle("memos:c")));
	return backend;
}

describe("attentionOf", () => {
	it("is due since the time of the server, or the review date, with the reason and the topic path", () => {
		expect(attentionOf(dueMemo("a", { label: "MEMO-001", summary: "Eins", path: ["Oben", "Unten"], due_since: "2026-10-18T09:00:00Z" }), "Prüfung")).toEqual({
			key: "memos:a",
			projectUid: "p1",
			dueSince: "2026-10-18T09:00:00Z",
			title: "MEMO-001 — Eins",
			caption: "Prüfung · Oben › Unten",
		});
		expect(attentionOf(dueMemo("b", { review_at: "2026-10-01T00:00:00Z" }), "Prüfung")).toMatchObject({ dueSince: "2026-10-01T00:00:00Z", caption: "Prüfung" });
	});
});

describe("the due memos in the bell", () => {
	it("names the reason and the topic path of a memo", async () => {
		await renderOpen();

		expect(screen.getByTestId(workspaceTestIds.attentionItem("memos:a")).textContent).toContain("Prüfung · Oben › Unten");
	});

	it.each([
		["keep", "keep", { version: 2 }],
		["snooze", "snooze", { version: 2 }],
		["done", "finish", { version: 2, status: "done" }],
		["dropped", "finish", { version: 2, status: "dropped" }],
	])("offers %s for a memo due by review and sends it with the version", async (action, path, body) => {
		const backend = await renderOpen();

		fireEvent.click(screen.getByTestId(ids.dueAction(action, "a")));

		await waitFor(() => expect(backend.calls("POST", `memos/memos/a/${path}`)).toHaveLength(1));
		expect(backend.calls("POST", `memos/memos/a/${path}`)[0]!.body).toEqual(body);
	});

	it("offers the decisions of the hint instead, except promote that needs fields", async () => {
		const backend = await renderOpen();

		expect(screen.queryByTestId(ids.dueAction("done", "c"))).toBeNull();
		expect(screen.queryByTestId(ids.dueAction("promote", "c"))).toBeNull();
		fireEvent.click(screen.getByTestId(ids.dueAction("detach", "c")));

		await waitFor(() => expect(backend.calls("POST", "memos/hints/x1/decide")).toHaveLength(1));
		expect(backend.calls("POST", "memos/hints/x1/decide")[0]!.body).toEqual({ decision: "detach", version: 5 });
	});
});
