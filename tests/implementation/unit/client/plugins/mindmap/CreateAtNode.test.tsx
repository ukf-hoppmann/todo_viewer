import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { NodeContentSection } from "../../../../../../client/src/plugins/mindmap/NodeContentSection";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { node } from "../../../../../helpers/client/mindmapFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

// Ein Knoten im Papierkorb hat kein Detail: die Seite öffnet das Detail nur für Knoten des lebenden Baums, und
// `NodeOut` trägt kein Merkmal „gelöscht“. Darum gibt es dort keine Aktion, die ein Test prüfen könnte.
const shown = node("a", null, 0, { title: "Backup planen", text: "Täglich sichern, Wiederherstellung testen" });

async function renderSection(options: Parameters<typeof fakeMindmapBackend>[0] = {}) {
	const backend = fakeMindmapBackend({ projects: [project("p1", "Viewer", 1)], nodes: [shown], ...options });
	await renderWorkspace(<NodeContentSection node={shown} />, { backend });
	return backend;
}
const input = (kind: "item" | "memo", field: string) => screen.getByTestId(ids.createField(kind, field)) as HTMLInputElement;
const type = (kind: "item" | "memo", field: string, value: string) => fireEvent.change(input(kind, field), { target: { value } });
const chooseType = (label: string) => {
	fireEvent.mouseDown(screen.getByRole("combobox", { name: /Typ/ }));
	fireEvent.click(screen.getByRole("option", { name: label }));
};
const confirm = (kind: "item" | "memo") => screen.getByTestId(ids.createConfirm(kind)) as HTMLButtonElement;

describe("Item aus einem Knoten anlegen", () => {
	it("schlägt Titel und Text des Knotens vor, lässt den Typ offen und verlangt Typ und Abschlusskriterien", async () => {
		await renderSection();

		fireEvent.click(await screen.findByTestId(ids.createItem));
		await screen.findByTestId(ids.createDialog("item"));

		expect(input("item", "title").value).toBe("Backup planen");
		expect(input("item", "goal").value).toBe("Täglich sichern, Wiederherstellung testen");
		expect(input("item", "completion_criteria").value).toBe("");
		expect(screen.getByRole("combobox", { name: /Typ/ }).textContent?.replace(/\u200b/g, "").trim()).toBe("");
		expect(confirm("item").disabled).toBe(true);

		chooseType("Task");
		expect(confirm("item").disabled).toBe(true);
		type("item", "completion_criteria", "   ");
		expect(confirm("item").disabled).toBe(true);
		type("item", "completion_criteria", "1. Backup läuft");
		expect(confirm("item").disabled).toBe(false);
	});

	it("ruft die Operation mit Typ und den Feldern auf, schließt den Dialog und zeigt das Ergebnis am Knoten", async () => {
		const backend = await renderSection();
		fireEvent.click(await screen.findByTestId(ids.createItem));
		await screen.findByTestId(ids.createDialog("item"));

		chooseType("Story");
		type("item", "title", "Backups");
		type("item", "completion_criteria", "1. Backup läuft");
		fireEvent.click(confirm("item"));

		await waitFor(() => expect(screen.queryByTestId(ids.createDialog("item"))).toBeNull());
		const call = backend.calls("POST", "mindmap/nodes/a/create-item");
		expect(call).toHaveLength(1);
		expect(call[0]!.body).toEqual({
			type: "Story",
			fields: { title: "Backups", goal: "Täglich sichern, Wiederherstellung testen", completion_criteria: "1. Backup läuft", priority: "Normal" },
		});
		await waitFor(() => expect(screen.getByTestId(ids.content).textContent).toContain("Backups"));
	});

	it("nimmt die gewählte Priorität mit", async () => {
		const backend = await renderSection();
		fireEvent.click(await screen.findByTestId(ids.createItem));
		await screen.findByTestId(ids.createDialog("item"));

		chooseType("Epic");
		fireEvent.mouseDown(screen.getByRole("combobox", { name: /Priorität/ }));
		fireEvent.click(screen.getByRole("option", { name: "Dringend" }));
		type("item", "completion_criteria", "1. Fertig");
		fireEvent.click(confirm("item"));

		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes/a/create-item")).toHaveLength(1));
		const body = backend.calls("POST", "mindmap/nodes/a/create-item")[0]!.body as { type: string; fields: Record<string, unknown> };
		expect(body.type).toBe("Epic");
		expect(body.fields.priority).toBe("Urgent");
	});

	it("lässt das Ziel weg, wenn es leer ist", async () => {
		const backend = await renderSection();
		fireEvent.click(await screen.findByTestId(ids.createItem));
		await screen.findByTestId(ids.createDialog("item"));

		chooseType("Task");
		type("item", "goal", "");
		type("item", "completion_criteria", "1. Fertig");
		fireEvent.click(confirm("item"));

		await waitFor(() => expect(backend.calls("POST", "mindmap/nodes/a/create-item")).toHaveLength(1));
		const body = backend.calls("POST", "mindmap/nodes/a/create-item")[0]!.body as { fields: Record<string, unknown> };
		expect("goal" in body.fields).toBe(false);
	});

	it("zeigt einen Fehler des Servers im Dialog, lässt ihn offen und behält die Eingaben", async () => {
		const backend = await renderSection({
			respond: ({ method, path }) =>
				method === "POST" && path === "mindmap/nodes/a/create-item"
					? Response.json({ code: "mindmap_assign_failed", message: "Das Item TASK-9 ist angelegt, hängt aber an keinem Knoten", details: {} }, { status: 400 })
					: undefined,
		});
		fireEvent.click(await screen.findByTestId(ids.createItem));
		await screen.findByTestId(ids.createDialog("item"));

		chooseType("Task");
		type("item", "title", "Eigener Titel");
		type("item", "completion_criteria", "1. Fertig");
		fireEvent.click(confirm("item"));

		expect((await screen.findByTestId(ids.createError("item"))).textContent).toContain("TASK-9 ist angelegt");
		expect(screen.getByTestId(ids.createDialog("item"))).toBeTruthy();
		expect(input("item", "title").value).toBe("Eigener Titel");
		expect(input("item", "completion_criteria").value).toBe("1. Fertig");
		expect(backend.calls("POST", "mindmap/nodes/a/create-item")).toHaveLength(1);
	});

	it("bricht ab, ohne etwas aufzurufen", async () => {
		const backend = await renderSection();
		fireEvent.click(await screen.findByTestId(ids.createItem));
		await screen.findByTestId(ids.createDialog("item"));

		fireEvent.click(screen.getByTestId(ids.createCancel("item")));

		await waitFor(() => expect(screen.queryByTestId(ids.createDialog("item"))).toBeNull());
		expect(backend.calls("POST", "mindmap/nodes/a/create-item")).toHaveLength(0);
	});
});

describe("Memo aus einem Knoten anlegen", () => {
	it("schlägt Titel als Zusammenfassung und Text des Knotens vor und ruft die Operation auf", async () => {
		const backend = await renderSection();

		fireEvent.click(await screen.findByTestId(ids.createMemo));
		const dialog = await screen.findByTestId(ids.createDialog("memo"));
		expect(input("memo", "summary").value).toBe("Backup planen");
		expect(input("memo", "body").value).toBe("Täglich sichern, Wiederherstellung testen");

		type("memo", "summary", "Backup klären");
		fireEvent.click(within(dialog).getByTestId(ids.createConfirm("memo")));

		await waitFor(() => expect(screen.queryByTestId(ids.createDialog("memo"))).toBeNull());
		expect(backend.calls("POST", "mindmap/nodes/a/create-memo")[0]!.body).toEqual({
			fields: { summary: "Backup klären", body: "Täglich sichern, Wiederherstellung testen" },
		});
		await waitFor(() => expect(screen.getByTestId(ids.content).textContent).toContain("Backup klären"));
	});

	it("verlangt eine Zusammenfassung", async () => {
		await renderSection();
		fireEvent.click(await screen.findByTestId(ids.createMemo));
		await screen.findByTestId(ids.createDialog("memo"));

		type("memo", "summary", " ");

		expect(confirm("memo").disabled).toBe(true);
	});

	it("zeigt einen Fehler des Servers im Dialog und behält die Eingaben", async () => {
		await renderSection({
			respond: ({ method, path }) =>
				method === "POST" && path === "mindmap/nodes/a/create-memo" ? Response.json({ code: "not_found", message: "Der Knoten liegt im Papierkorb", details: {} }, { status: 404 }) : undefined,
		});
		fireEvent.click(await screen.findByTestId(ids.createMemo));
		await screen.findByTestId(ids.createDialog("memo"));

		type("memo", "body", "Neuer Text");
		fireEvent.click(confirm("memo"));

		expect((await screen.findByTestId(ids.createError("memo"))).textContent).toContain("Papierkorb");
		expect(input("memo", "body").value).toBe("Neuer Text");
	});
});
