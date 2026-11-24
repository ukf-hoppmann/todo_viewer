import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { TransferBranchDialog } from "../../../../../../client/src/plugins/mindmap/TransferBranchDialog";
import { mindmapTestIds as ids } from "../../../../../../client/src/plugins/mindmap/testIds";
import { item } from "../../../../../helpers/client/backlogFixtures";
import { fakeMindmapBackend } from "../../../../../helpers/client/fakeMindmapBackend";
import { project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { node } from "../../../../../helpers/client/mindmapFixtures";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

// Ast: a (Wurzel) mit b und c; b hat d. `c` hängt schon an einem Item und ist „geplant“.
const nodes = [node("a"), node("b", "a", 0), node("c", "a", 1, { state: "planned" }), node("d", "b", 0)];
const source = { uid: "a", version: 1, title: "Thema a", project_uid: "p1", tree_uid: "t1" };

type Entry = { node: string; kind: string; parent?: string; depends_on?: string[]; type?: string };
const previewBody = (body: unknown) => (body as { entries: Entry[] }).entries;

/** Der Server prüft hier so, wie die Vorschau es tut: ein Item ohne Typ ist ein Problem am Knoten. */
function respondLikeServer(transferred: Array<Record<string, unknown>> = []) {
	return (request: { method: string; path: string; body?: unknown }) => {
		const preview = /^mindmap\/nodes\/a\/preview-branch-transfer$/.test(request.path);
		if (preview) {
			const entries = previewBody(request.body);
			const missing = entries.filter((entry) => entry.kind === "item" && !entry.type);
			return Response.json({
				root: "a",
				ok: missing.length === 0,
				order: entries.map((entry) => entry.node),
				problems: [],
				entries: entries.map((entry) => ({
					node: entry.node,
					ok: !missing.includes(entry),
					problems: missing.includes(entry) ? [{ code: "invalid_type", message: "Unbekannter Typ", details: {} }] : [],
				})),
			});
		}
		if (request.path === "mindmap/nodes/a/transfer-branch") {
			transferred.push(request.body as Record<string, unknown>);
			const entries = previewBody(request.body);
			return Response.json({
				root: "a",
				entries: entries.map((entry, index) =>
					index === 0
						? { node: entry.node, status: "created", created: { uid: "n1", label: "STORY-200", title: "Neu", type: "Story" } }
						: index === 1
							? { node: entry.node, status: "failed", error: { code: "x", message: "kaputt", details: {} } }
							: { node: entry.node, status: "not_attempted" },
				),
			});
		}
		return undefined;
	};
}

async function renderDialog(transferred: Array<Record<string, unknown>> = [], backlog = [item("i1", { label: "STORY-001", title: "Vorhanden", type: "Story" })]) {
	const backend = fakeMindmapBackend({ projects: [project("p1", "Viewer", 1)], nodes, backlog, respond: respondLikeServer(transferred) });
	await renderWorkspace(<TransferBranchDialog source={source} onClose={() => undefined} />, { backend });
	await screen.findByTestId(ids.transferRow("d"));
	return backend;
}
const row = (uid: string) => within(screen.getByTestId(ids.transferRow(uid)));
const choose = (uid: string, label: string) => {
	fireEvent.mouseDown(row(uid).getByRole("combobox", { name: /Wird zu/ }));
	fireEvent.click(screen.getByRole("option", { name: label }));
};
const setType = (uid: string, label: string) => {
	fireEvent.mouseDown(row(uid).getByRole("combobox", { name: /Typ/ }));
	fireEvent.click(screen.getByRole("option", { name: label }));
};
const write = (uid: string, name: string, value: string) => fireEvent.change(screen.getByTestId(ids.transferField(uid, name)), { target: { value } });
const confirm = () => screen.getByTestId(ids.transferConfirm) as HTMLButtonElement;
const kindOf = (uid: string) => row(uid).getByRole("combobox", { name: /Wird zu/ }).textContent?.replace(/\u200b/g, "").trim();

describe("Ast überführen", () => {
	it("zeigt den Ast als Baum mit dem Zustand der Knoten und ohne Vorbelegung der Wahl", async () => {
		await renderDialog();

		const order = [...document.querySelectorAll("[data-testid^='mindmap.transfer-row.']")].map((element) => element.getAttribute("data-testid"));
		expect(order).toEqual(["a", "b", "d", "c"].map(ids.transferRow));
		for (const uid of ["a", "b", "c", "d"]) expect(kindOf(uid)).toBe("Nichts");
		expect(screen.getByTestId(ids.transferState("c")).textContent).toBe("Geplant");
		expect(screen.getByTestId(ids.transferState("d")).textContent).toBe("Idee");
		expect(confirm().disabled).toBe(true);
	});

	it("bietet je Item Typ, Titel, Ziel und Abschlusskriterien an; das Memo nur Zusammenfassung und Text", async () => {
		await renderDialog();
		choose("b", "Item");
		expect((screen.getByTestId(ids.transferField("b", "title")) as HTMLInputElement).value).toBe("Thema b");
		expect(screen.getByTestId(ids.transferField("b", "completion_criteria"))).toBeTruthy();
		choose("c", "Memo");
		expect(screen.queryByTestId(ids.transferField("c", "completion_criteria"))).toBeNull();
		expect(screen.getByTestId(ids.transferField("c", "title"))).toBeTruthy();
	});

	it("prüft live, zeigt das Problem am Knoten und sperrt „Überführen“, bis es behoben ist", async () => {
		const backend = await renderDialog();
		choose("b", "Item");

		await waitFor(() => expect(screen.getByTestId(ids.transferProblems("b")).textContent).toContain("Wähle einen Typ."));
		expect(confirm().disabled).toBe(true);
		expect(backend.calls("POST", "mindmap/nodes/a/preview-branch-transfer").length).toBeGreaterThan(0);

		setType("b", "Task");
		write("b", "completion_criteria", "1. Fertig");
		await waitFor(() => expect(screen.queryByTestId(ids.transferProblems("b"))).toBeNull());
		await waitFor(() => expect(confirm().disabled).toBe(false));
	});

	it("schickt die Wahl als Plan: Beziehung je Knoten (Kind von, hängt ab von), ein vorhandenes Item als Ziel", async () => {
		const transferred: Array<Record<string, unknown>> = [];
		await renderDialog(transferred);
		choose("a", "Item");
		setType("a", "Story");
		write("a", "completion_criteria", "1. Läuft");
		choose("b", "Item");
		setType("b", "Task");
		write("b", "completion_criteria", "1. Fertig");

		// b ist Kind von a (ein Knoten des Plans); c hängt von b und einem vorhandenen Item ab, ohne Parent.
		fireEvent.mouseDown(within(screen.getByTestId(ids.transferParent("b"))).getByRole("combobox"));
		fireEvent.click(screen.getByRole("option", { name: /NODE-a — Thema a/ }));
		choose("c", "Item");
		setType("c", "Task");
		write("c", "completion_criteria", "1. Auch fertig");
		const depends = within(screen.getByTestId(ids.transferDepends("c"))).getByRole("combobox");
		fireEvent.mouseDown(depends);
		fireEvent.click(screen.getByRole("option", { name: /NODE-b — Thema b/ }));
		fireEvent.mouseDown(depends);
		fireEvent.click(screen.getByRole("option", { name: /STORY-001 — Vorhanden/ }));

		await waitFor(() => expect(confirm().disabled).toBe(false));
		fireEvent.click(confirm());
		await waitFor(() => expect(transferred).toHaveLength(1));
		expect(transferred[0]).toEqual({
			tree: "t1",
			entries: [
				{ node: "a", kind: "item", type: "Story", title: "Thema a", completion_criteria: "1. Läuft" },
				{ node: "b", kind: "item", type: "Task", title: "Thema b", completion_criteria: "1. Fertig", parent: "a" },
				{ node: "c", kind: "item", type: "Task", title: "Thema c", completion_criteria: "1. Auch fertig", depends_on: ["b", "i1"] },
			],
		});
	});

	it("zeigt nach dem Überführen das Ergebnis je Knoten (angelegt, Fehler, nicht versucht) und bleibt offen", async () => {
		await renderDialog();
		for (const uid of ["a", "b", "d"]) {
			choose(uid, "Item");
			setType(uid, "Task");
			write(uid, "completion_criteria", "1. Fertig");
		}
		await waitFor(() => expect(confirm().disabled).toBe(false));
		fireEvent.click(confirm());

		await waitFor(() => expect(screen.getByTestId(ids.transferResult("a")).textContent).toBe("Angelegt: STORY-200"));
		expect(screen.getByTestId(ids.transferResult("b")).textContent).toBe("Fehlgeschlagen: kaputt");
		expect(screen.getByTestId(ids.transferResult("d")).getAttribute("data-status")).toBe("not_attempted");
		expect(screen.getByTestId(ids.transferDialog)).toBeTruthy();
		expect(confirm().disabled).toBe(true);
		expect(screen.getByTestId(ids.transferClose).textContent).toBe("Schließen");
	});
});
