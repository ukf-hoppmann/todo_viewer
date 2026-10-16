import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { useCreateDialog } from "../../../../../../client/src/plugins/workspace/createDialog";
import { NewButton } from "../../../../../../client/src/plugins/workspace/NewButton";
import { workspaceTestIds as ids } from "../../../../../../client/src/plugins/workspace/testIds";
import { fakeWorkspaceBackend, project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

function TaskForm() {
	const { close, projectUid } = useCreateDialog();
	return (
		<div>
			<span data-testid="form-project">{projectUid}</span>
			<button onClick={close}>fertig</button>
		</div>
	);
}

const taskType = { ownerId: "kinds", name: "task", title: "Aufgabe", form: TaskForm };

describe("NewButton", () => {
	it("offers a project and the create types of other plugins", async () => {
		await renderWorkspace(<NewButton />, { createTypes: [taskType] });

		fireEvent.click(screen.getByTestId(ids.newButton));

		expect((await screen.findByTestId(ids.newMenuItem("task"))).textContent).toBe("Aufgabe");
		expect(screen.getByTestId(ids.newMenuItem("project")).textContent).toBe("Projekt");
	});

	it("opens the form of a type in a dialog with the built-in project as default, and closes it from the form", async () => {
		await renderWorkspace(<NewButton />, { createTypes: [taskType] });
		await waitFor(() => expect(screen.getByTestId(ids.newButton)).toBeTruthy());

		fireEvent.click(screen.getByTestId(ids.newButton));
		fireEvent.click(await screen.findByTestId(ids.newMenuItem("task")));

		expect(screen.getByTestId(ids.newDialog).textContent).toContain("Aufgabe");
		await waitFor(() => expect(screen.getByTestId("form-project").textContent).toBe("p0"));
		fireEvent.click(screen.getByText("fertig"));
		await waitFor(() => expect(screen.queryByTestId(ids.newDialog)).toBeNull());
	});

	it("gives the marked project to the form as the default", async () => {
		const backend = fakeWorkspaceBackend({
			projects: [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)],
			documents: { workspace: { marked: "p1" } },
		});
		await renderWorkspace(<NewButton />, { backend, createTypes: [taskType] });

		fireEvent.click(screen.getByTestId(ids.newButton));
		fireEvent.click(await screen.findByTestId(ids.newMenuItem("task")));

		await waitFor(() => expect(screen.getByTestId("form-project").textContent).toBe("p1"));
	});

	it("creates a project from the menu", async () => {
		await renderWorkspace(<NewButton />);

		fireEvent.click(screen.getByTestId(ids.newButton));
		fireEvent.click(await screen.findByTestId(ids.newMenuItem("project")));

		expect(screen.getByTestId(ids.projectCard)).toBeTruthy();
	});
});
