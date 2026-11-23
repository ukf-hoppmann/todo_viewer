import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ItemDetail } from "../../../../../../client/src/plugins/backlog/ItemDetail";
import { backlogTestIds as ids } from "../../../../../../client/src/plugins/backlog/testIds";
import { sharedTestIds } from "../../../../../../client/src/shared";
import { detail } from "../../../../../helpers/client/backlogFixtures";
import { fakeWorkspaceBackend } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

const summary = (uid: string, extra: Record<string, unknown> = {}) => ({
	uid,
	label: uid.toUpperCase(),
	type: "Task",
	title: `Titel ${uid}`,
	status: "Open",
	required_for_parent: null,
	deleted: false,
	...extra,
});

async function renderDetail(uid: string, details: Record<string, ReturnType<typeof detail>>, onSelect = vi.fn()) {
	const backend = fakeWorkspaceBackend({ details });
	await renderWorkspace(<ItemDetail uid={uid} onSelect={onSelect} />, { backend });
	await screen.findByTestId(ids.detail);
	return { backend, onSelect };
}

describe("ItemDetail", () => {
	it("shows all fields of the item, translated, with the text fields as formatted markdown", async () => {
		await renderDetail("t1", {
			t1: detail("t1", {
				status: "Awaiting confirmation",
				priority: "Important",
				goal: "Das **Ziel**",
				completion_criteria: "1. Eins",
				summary: "Kurz",
				resolution: "Bestätigt",
				progress: { done: 1, total: 2 },
			}),
		});

		expect(screen.getByTestId(sharedTestIds.detailTitle).textContent).toBe("T1 — Titel t1");
		expect(screen.getByTestId(sharedTestIds.inlineFieldInput("status")).textContent).toBe("Wartet auf Bestätigung");
		expect(screen.getByTestId(sharedTestIds.inlineFieldInput("priority")).textContent).toBe("Wichtig");
		expect(screen.queryByTestId(sharedTestIds.inlineField("area"))).toBeNull();
		expect(screen.getByTestId(ids.field("created")).textContent).toBe("2026-10-16");
		expect(screen.getByTestId(ids.field("goal")).querySelector("strong")?.textContent).toBe("Ziel");
		expect(screen.getByTestId(ids.field("completion_criteria")).textContent).toContain("Eins");
		expect(screen.getByTestId(ids.field("summary")).textContent).toContain("Kurz");
		expect(screen.getByTestId(ids.field("resolution")).textContent).toContain("Bestätigt");
		expect(screen.getByTestId(ids.field("progress")).textContent).toBe("1/2");
	});

	it("does not show fields that are empty", async () => {
		await renderDetail("t1", { t1: detail("t1") });

		expect(screen.queryByTestId(ids.field("goal"))).toBeNull();
		expect(screen.queryByTestId(ids.field("progress"))).toBeNull();
	});

	it("lists children with the ones in the trash struck through, and selects one on click", async () => {
		const { onSelect } = await renderDetail("e1", {
			e1: detail("e1", {
				type: "Epic",
				children: [summary("a"), summary("b", { deleted: true }), summary("c", { required_for_parent: false })],
			}),
		});

		expect(screen.getByTestId(ids.child("b")).getAttribute("data-deleted")).toBe("true");
		expect(screen.getByTestId(ids.child("b")).textContent).toContain("gelöscht");
		expect(screen.getByTestId(ids.child("c")).getAttribute("data-optional")).toBe("true");
		expect(screen.getByTestId(ids.child("a")).getAttribute("data-deleted")).toBe("false");
		fireEvent.click(screen.getByTestId(ids.child("a")));
		expect(onSelect).toHaveBeenCalledWith("a");
	});

	it("shows the parent (with a note when optional) and the dependencies as links", async () => {
		const { onSelect } = await renderDetail("t1", {
			t1: detail("t1", { parent: summary("s1", { type: "Story" }), required_for_parent: false, dependencies: [summary("t0")] }),
		});

		expect(screen.getByTestId(sharedTestIds.detailField("parent")).textContent).toContain("optional");
		fireEvent.click(screen.getByTestId(ids.parent));
		fireEvent.click(screen.getByTestId(ids.dependency("t0")));
		expect(onSelect.mock.calls).toEqual([["s1"], ["t0"]]);
	});

	it("marks an item in the trash and offers no editing for it", async () => {
		await renderDetail("t1", { t1: detail("t1", { deleted: true }) });

		expect(screen.getByTestId(ids.detail).textContent).toContain("im Papierkorb");
		expect(screen.queryByTestId(sharedTestIds.inlineField("status"))).toBeNull();
		expect(screen.queryByTestId(sharedTestIds.detailAction("edit"))).toBeNull();
	});

	it("says so when the item cannot be loaded", async () => {
		const backend = fakeWorkspaceBackend({ details: {} });
		await renderWorkspace(<ItemDetail uid="weg" onSelect={() => {}} />, { backend });

		await waitFor(() => expect(screen.getByText("Das Item lässt sich nicht laden.")).toBeTruthy());
	});

	it("builds the section of links into the panel", async () => {
		await renderDetail("t1", { t1: detail("t1") });

		fireEvent.click(screen.getByTestId(sharedTestIds.detailSectionToggle("links")));

		expect(await screen.findByTestId("workspace.links")).toBeTruthy();
	});
});
