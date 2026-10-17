import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AlarmSettings } from "../../../../../../client/src/plugins/alarms/AlarmSettings";
import { alarmsTestIds as ids } from "../../../../../../client/src/plugins/alarms/testIds";
import { fakeAlarmsBackend } from "../../../../../helpers/client/fakeAlarmsBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(() => {
	cleanup();
	vi.unstubAllGlobals();
});

function stub(permission: string, onRequest?: () => void) {
	class FakeNotification {
		static permission = permission;
		static requestPermission = () => {
			onRequest?.();
			FakeNotification.permission = "granted";
			return Promise.resolve("granted");
		};
	}
	vi.stubGlobal("Notification", FakeNotification);
}

describe("AlarmSettings", () => {
	it("says whether notifications are allowed", async () => {
		stub("granted");
		await renderWorkspace(<AlarmSettings />, { backend: fakeAlarmsBackend() });

		expect(screen.getByTestId(ids.permission).textContent).toBe("Benachrichtigungen sind erlaubt.");
		expect(screen.queryByTestId(ids.enableNotifications)).toBeNull();
	});

	it("says when the browser blocks them", async () => {
		stub("denied");
		await renderWorkspace(<AlarmSettings />, { backend: fakeAlarmsBackend() });

		expect(screen.getByTestId(ids.permission).textContent).toContain("gesperrt");
		expect(screen.queryByTestId(ids.enableNotifications)).toBeNull();
	});

	it("asks for the permission with a button and then shows it as allowed", async () => {
		const asked = vi.fn();
		stub("default", asked);
		await renderWorkspace(<AlarmSettings />, { backend: fakeAlarmsBackend() });

		fireEvent.click(screen.getByTestId(ids.enableNotifications));

		await waitFor(() => expect(screen.getByTestId(ids.permission).textContent).toBe("Benachrichtigungen sind erlaubt."));
		expect(asked).toHaveBeenCalledTimes(1);
	});

	it("says so when the browser has no notifications", async () => {
		vi.stubGlobal("Notification", undefined);
		await renderWorkspace(<AlarmSettings />, { backend: fakeAlarmsBackend() });

		expect(screen.getByTestId(ids.permission).textContent).toContain("keine Benachrichtigungen");
	});
});
