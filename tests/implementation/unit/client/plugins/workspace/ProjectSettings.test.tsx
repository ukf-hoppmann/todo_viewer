import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ProjectSettings } from "../../../../../../client/src/plugins/workspace/ProjectSettings";
import { ProjectsSection } from "../../../../../../client/src/plugins/workspace/ProjectsSection";
import { workspaceTestIds as ids } from "../../../../../../client/src/plugins/workspace/testIds";
import { fakeWorkspaceBackend, project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

const status = (project: string, state: string, extra: Record<string, unknown> = {}) => ({ project, state, conflicts: 0, to_database: 0, to_files: 0, files: [], reason: null, last_sync: null, ...extra });
const projects = [
	project("p0", "Allgemein", 0, { builtin: true }),
	project("p1", "Viewer", 1, { mirror_enabled: true, mirror_folder: "/work/viewer", auto_sync: true }),
	project("p2", "Docs", 2, { mirror_enabled: true, mirror_folder: "/work/docs" }),
];

async function renderSettings(options: Parameters<typeof fakeWorkspaceBackend>[0] = {}) {
	const backend = fakeWorkspaceBackend({
		projects,
		syncStatus: {
			p1: status("p1", "in_sync", { last_sync: "2026-10-16T12:00:00Z" }),
			p2: status("p2", "conflicts", { conflicts: 2 }),
		} as never,
		...options,
	});
	await renderWorkspace(<ProjectSettings />, { backend });
	await screen.findByTestId(ids.settingsProject("p1"));
	return backend;
}

describe("ProjectSettings", () => {
	it("shows a card per project with its state, folder, direction and last sync", async () => {
		await renderSettings();

		await waitFor(() => expect(screen.getByTestId(ids.settingsState("p1")).textContent).toBe("in Sync"));
		expect(screen.getByTestId(ids.settingsState("p2")).textContent).toBe("braucht dich");
		expect(screen.getByTestId(ids.settingsState("p0")).textContent).toBe("nicht gespiegelt");
		expect(screen.getByTestId(ids.settingsProject("p1")).textContent).toContain("/work/viewer");
		expect(screen.getByTestId(ids.settingsLast("p1")).textContent).toMatch(/^Letzter Sync: /);
		expect(screen.getByTestId(ids.settingsLast("p2")).textContent).toBe("Noch nie abgeglichen");
	});

	it("names the paused state with its reason", async () => {
		await renderSettings({ syncStatus: { p1: status("p1", "paused", { reason: "merge_markers" }), p2: status("p2", "in_sync") } as never });

		await waitFor(() => expect(screen.getByTestId(ids.settingsState("p1")).textContent).toBe("pausiert: Git-Merge-Konflikt in einer Datei"));
		expect(screen.getByTestId(ids.settingsMain("p1")).textContent).toBe("Prüfen …");
	});

	it("switches the mode: by hand, automatically, off — with the version of the project", async () => {
		const backend = await renderSettings();
		const choose = async (uid: string, option: string) => {
			fireEvent.mouseDown(screen.getByTestId(ids.settingsProject(uid)).querySelector("[role='combobox']")!);
			fireEvent.click(await screen.findByRole("option", { name: option }));
		};

		await choose("p1", "Sync von Hand");
		await waitFor(() => expect(backend.calls("PUT", "workspace/projects/p1")).toHaveLength(1));
		expect(backend.calls("PUT", "workspace/projects/p1")[0]!.body).toEqual({ version: 1, mirror_enabled: true, auto_sync: false });

		await choose("p2", "Sync automatisch");
		await waitFor(() => expect(backend.calls("PUT", "workspace/projects/p2")).toHaveLength(1));
		expect(backend.calls("PUT", "workspace/projects/p2")[0]!.body).toEqual({ version: 1, mirror_enabled: true, auto_sync: true });

		await choose("p2", "Aus");
		await waitFor(() => expect(backend.calls("PUT", "workspace/projects/p2")).toHaveLength(2));
		expect(backend.calls("PUT", "workspace/projects/p2")[1]!.body).toMatchObject({ mirror_enabled: false, auto_sync: false });
	});

	it("opens the project card instead when a mirror is switched on for a project without a folder", async () => {
		const backend = await renderSettings();

		fireEvent.mouseDown(screen.getByTestId(ids.settingsProject("p0")).querySelector("[role='combobox']")!);
		fireEvent.click(await screen.findByRole("option", { name: "Sync von Hand" }));

		expect(await screen.findByTestId(ids.projectCard)).toBeTruthy();
		expect(backend.calls("PUT", "workspace/projects/p0")).toHaveLength(0);
	});

	it("has one main action: set up the mirror, or sync", async () => {
		await renderSettings();

		expect(screen.getByTestId(ids.settingsMain("p0")).textContent).toBe("Spiegel einrichten");
		expect(screen.getByTestId(ids.settingsMain("p1")).textContent).toBe("Abgleichen …");
		fireEvent.click(screen.getByTestId(ids.settingsMain("p1")));
		expect(await screen.findByTestId(ids.syncDialog)).toBeTruthy();
		fireEvent.click(screen.getByTestId(ids.syncClose));
		await waitFor(() => expect(screen.queryByTestId(ids.syncDialog)).toBeNull());
		fireEvent.click(screen.getByTestId(ids.settingsMain("p0")));
		expect(await screen.findByTestId(ids.projectCard)).toBeTruthy();
	});

	it("edits the project in its card", async () => {
		await renderSettings();

		fireEvent.click(screen.getByTestId(ids.settingsEdit("p1")));

		expect((await screen.findByTestId(ids.cardName) as HTMLInputElement).value).toBe("Viewer");
	});
});

describe("sync indicators in the project list", () => {
	it("shows ⚠ for a project that needs the owner and ↻ for one that syncs by itself", async () => {
		const backend = fakeWorkspaceBackend({
			projects,
			syncStatus: { p1: status("p1", "in_sync"), p2: status("p2", "mirror_changed", { to_database: 1 }) } as never,
		});
		await renderWorkspace(<ProjectsSection />, { backend });

		await waitFor(() => expect(screen.getByTestId(ids.syncAttention("p2"))).toBeTruthy());
		expect(screen.getByTestId(ids.syncAuto("p1"))).toBeTruthy();
		expect(screen.queryByTestId(ids.syncAttention("p1"))).toBeNull();
		expect(screen.queryByTestId(ids.syncAuto("p2"))).toBeNull();
		expect(screen.queryByTestId(ids.syncAttention("p0"))).toBeNull();
		expect(backend.calls("GET", "core/sync/p0")).toHaveLength(0); // ein Projekt ohne Spiegel wird nicht gefragt
	});
});
