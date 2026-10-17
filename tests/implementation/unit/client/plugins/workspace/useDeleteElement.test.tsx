import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import type { ElementOut } from "../../../../../../client/src/plugins/workspace/api";
import { useDeleteElement } from "../../../../../../client/src/plugins/workspace/useDeleteElement";
import { fakeWorkspaceBackend } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const element = (uid: string): ElementOut => ({ uid, project_uid: "p0", kind: "task", label: `TASK-${uid}`, title: uid, version: 1, deleted: false });

function Button({ uid }: { uid: string }) {
	const { requestDelete, dialog, failed } = useDeleteElement();
	return (
		<>
			<button onClick={() => void requestDelete(uid, 3)}>löschen</button>
			<span data-testid="failed">{failed}</span>
			{dialog}
		</>
	);
}

afterEach(cleanup);

describe("useDeleteElement", () => {
	it("deletes an element without children at once", async () => {
		const backend = fakeWorkspaceBackend({ elements: [element("a")] });
		await renderWorkspace(<Button uid="a" />, { backend });

		fireEvent.click(screen.getByText("löschen"));

		await waitFor(() => expect(backend.calls("DELETE", "workspace/elements/a")).toHaveLength(1));
		expect(backend.calls("DELETE", "workspace/elements/a")[0]!.query.get("version")).toBe("3");
		expect(screen.queryByTestId("shared.confirm-dialog")).toBeNull();
	});

	it("asks when the element has children, and deletes with cascade after the confirmation", async () => {
		const backend = fakeWorkspaceBackend({ elements: [element("a")], children: { a: 2 } });
		await renderWorkspace(<Button uid="a" />, { backend });

		fireEvent.click(screen.getByText("löschen"));
		expect((await screen.findByTestId("shared.confirm-dialog")).textContent).toContain("2 Kinder");
		expect(backend.calls("DELETE", "workspace/elements/a").map((call) => call.query.get("cascade"))).toEqual([null]);
		fireEvent.click(screen.getByTestId("shared.confirm-dialog-confirm"));

		await waitFor(() => expect(backend.calls("DELETE", "workspace/elements/a")).toHaveLength(2));
		expect(backend.calls("DELETE", "workspace/elements/a")[1]!.query.get("cascade")).toBe("true");
	});

	it("deletes nothing when the question is declined", async () => {
		const backend = fakeWorkspaceBackend({ elements: [element("a")], children: { a: 1 } });
		await renderWorkspace(<Button uid="a" />, { backend });

		fireEvent.click(screen.getByText("löschen"));
		fireEvent.click(await screen.findByTestId("shared.confirm-dialog-cancel"));

		expect(backend.calls("DELETE", "workspace/elements/a")).toHaveLength(1);
	});

	it("reports a failure", async () => {
		const backend = fakeWorkspaceBackend({ elements: [] });
		await renderWorkspace(<Button uid="gibt-es-nicht" />, { backend });

		fireEvent.click(screen.getByText("löschen"));

		await waitFor(() => expect(screen.getByTestId("failed").textContent).toBe("Element gibt es nicht"));
	});
});
