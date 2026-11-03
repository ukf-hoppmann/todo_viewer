import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { AutoSyncSettings } from "../../../../../../client/src/plugins/workspace/AutoSyncSettings";
import { workspaceTestIds as ids } from "../../../../../../client/src/plugins/workspace/testIds";
import { fakeWorkspaceBackend } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

async function renderSection(syncSettings?: { seconds: number; locked?: boolean }) {
	const backend = fakeWorkspaceBackend({ syncSettings });
	await renderWorkspace(<AutoSyncSettings />, { backend });
	const field = (await screen.findByTestId(ids.autoSyncField)) as HTMLInputElement;
	return { backend, field };
}

describe("AutoSyncSettings", () => {
	it("shows the interval the server uses", async () => {
		const { field } = await renderSection({ seconds: 45 });

		expect(field.value).toBe("45");
		expect(screen.getByTestId(ids.autoSync).textContent).toContain("Auto-Sync");
		expect(screen.queryByTestId(ids.autoSyncLocked)).toBeNull();
	});

	it("saves a new interval and says so", async () => {
		const { backend, field } = await renderSection({ seconds: 30 });

		fireEvent.change(field, { target: { value: "10" } });
		fireEvent.click(screen.getByTestId(ids.autoSyncSave));

		await waitFor(() => expect(backend.calls("PUT", "core/settings/sync")).toHaveLength(1));
		expect(backend.calls("PUT", "core/settings/sync")[0]!.body).toEqual({ auto_sync_interval_seconds: 10 });
		expect(await screen.findByTestId(ids.autoSyncSaved)).toBeTruthy();
	});

	it("accepts 0 to switch the auto sync off", async () => {
		const { backend, field } = await renderSection({ seconds: 30 });

		fireEvent.change(field, { target: { value: "0" } });
		fireEvent.click(screen.getByTestId(ids.autoSyncSave));

		await waitFor(() => expect(backend.calls("PUT", "core/settings/sync")[0]?.body).toEqual({ auto_sync_interval_seconds: 0 }));
	});

	it("shows the message of the server when the value is refused", async () => {
		const { field } = await renderSection({ seconds: 30 });

		fireEvent.change(field, { target: { value: "0.2" } });
		fireEvent.click(screen.getByTestId(ids.autoSyncSave));

		expect((await screen.findByTestId(ids.autoSyncError)).textContent).toContain("zwischen 1 und 86400");
		expect(screen.queryByTestId(ids.autoSyncSaved)).toBeNull();
	});

	it("locks the field and the button and names the reason when the environment sets the interval", async () => {
		const { backend, field } = await renderSection({ seconds: 5, locked: true });

		expect(field.disabled).toBe(true);
		expect((screen.getByTestId(ids.autoSyncSave) as HTMLButtonElement).disabled).toBe(true);
		expect(screen.getByTestId(ids.autoSyncLocked).textContent).toContain("AUTO_SYNC_INTERVAL");
		expect(field.value).toBe("5");
		expect(backend.calls("PUT", "core/settings/sync")).toHaveLength(0);
	});
});
