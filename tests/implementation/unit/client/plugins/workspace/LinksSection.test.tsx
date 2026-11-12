import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { ElementOut } from "../../../../../../client/src/plugins/workspace/api";
import { LinksSection } from "../../../../../../client/src/plugins/workspace/LinksSection";
import { workspaceTestIds as ids } from "../../../../../../client/src/plugins/workspace/testIds";
import { fakeWorkspaceBackend } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const element = (uid: string, label: string, title: string, deleted = false): ElementOut => ({
	uid,
	project_uid: "p0",
	kind: "task",
	label,
	title,
	version: 1,
	deleted,
});

const elements = [element("a", "STORY-001", "Idee"), element("b", "TASK-001", "Umsetzen"), element("c", "TASK-002", "Alt", true), element("d", "MEMO-001", "Notiz")];

afterEach(cleanup);

async function renderLinks(links: Array<[string, string, string, "reference" | "origin" | "trigger"]> = [], readOnly = false) {
	const backend = fakeWorkspaceBackend({ elements, links });
	await renderWorkspace(<LinksSection elementUid="a" readOnly={readOnly} />, { backend });
	return backend;
}

describe("LinksSection", () => {
	it("lists outgoing and incoming links with their role", async () => {
		await renderLinks([
			["l1", "a", "b", "origin"],
			["l2", "d", "a", "reference"],
		]);

		const outgoing = await screen.findByTestId(ids.link("l1"));
		expect(outgoing.textContent).toContain("TASK-001 — Umsetzen");
		expect(outgoing.textContent).toContain("Herkunft");
		expect(within(screen.getByTestId(ids.linksIncoming)).getByTestId(ids.link("l2")).textContent).toContain("MEMO-001 — Notiz");
	});

	it("marks a link to an element in the trash", async () => {
		await renderLinks([["l1", "a", "c", "reference"]]);

		const entry = await screen.findByTestId(ids.link("l1"));

		expect(entry.textContent).toContain("gelöscht");
		expect(entry.querySelector("[data-deleted='true']")).not.toBeNull();
	});

	it("removes a link, but offers no removal for the role trigger", async () => {
		const backend = await renderLinks([
			["l1", "a", "b", "reference"],
			["l2", "a", "d", "trigger"],
		]);
		await screen.findByTestId(ids.link("l1"));

		expect(screen.queryByTestId(ids.linkRemove("l2"))).toBeNull();
		fireEvent.click(screen.getByTestId(ids.linkRemove("l1")));

		await waitFor(() => expect(screen.queryByTestId(ids.link("l1"))).toBeNull());
		expect(backend.calls("DELETE", "workspace/links/l1")).toHaveLength(1);
	});

	it("searches the server while typing, chooses a target and adds the link with the chosen role", async () => {
		const backend = await renderLinks();
		await screen.findByTestId(ids.linksOutgoing);

		fireEvent.change(screen.getByRole("combobox", { name: "Ziel suchen" }), { target: { value: "umset" } });
		fireEvent.click(await screen.findByRole("option", { name: "TASK-001 — Umsetzen" }));
		fireEvent.mouseDown(screen.getByRole("combobox", { name: "Rolle" }));
		fireEvent.click(await screen.findByRole("option", { name: "Herkunft" }));
		fireEvent.click(screen.getByTestId(ids.linkAdd));

		await waitFor(() => expect(screen.getByTestId(ids.link("l1")).textContent).toContain("TASK-001"));
		expect(backend.calls("POST", "workspace/links")[0]!.body).toEqual({ from_uid: "a", to_uid: "b", role: "origin" });
		expect(backend.calls("GET", "workspace/elements").some((call) => call.query.get("query") === "umset")).toBe(true);
	});

	it("cannot choose the element itself and shows the server's message on a duplicate", async () => {
		await renderLinks([["l1", "a", "b", "reference"]]);
		await screen.findByTestId(ids.link("l1"));

		fireEvent.change(screen.getByRole("combobox", { name: "Ziel suchen" }), { target: { value: "idee" } });
		expect((await screen.findByRole("option", { name: "STORY-001 — Idee" })).getAttribute("aria-disabled")).toBe("true");
		fireEvent.change(screen.getByRole("combobox", { name: "Ziel suchen" }), { target: { value: "umset" } });
		fireEvent.click(await screen.findByRole("option", { name: "TASK-001 — Umsetzen" }));
		await waitFor(() => expect((screen.getByTestId(ids.linkAdd) as HTMLButtonElement).disabled).toBe(false));
		fireEvent.click(screen.getByTestId(ids.linkAdd));

		await waitFor(() => expect(screen.getByTestId(ids.linkError).textContent).toBe("Diese Verknüpfung gibt es schon"));
	});

	it("has no controls to add or remove in read-only mode", async () => {
		await renderLinks([["l1", "a", "b", "reference"]], true);
		await screen.findByTestId(ids.link("l1"));

		expect(screen.queryByTestId(ids.linkAdd)).toBeNull();
		expect(screen.queryByTestId(ids.linkRemove("l1"))).toBeNull();
	});
});
