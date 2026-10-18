import { cleanup, fireEvent, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { sharedTestIds } from "../../../../../../client/src/shared";
import type { ElementOut } from "../../../../../../client/src/plugins/workspace/api";
import { ElementDetail } from "../../../../../../client/src/plugins/workspace/ElementDetail";
import { useShownElement } from "../../../../../../client/src/plugins/workspace/shownElement";
import { workspaceTestIds as ids } from "../../../../../../client/src/plugins/workspace/testIds";
import { fakeWorkspaceBackend } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

const element = (uid: string, label: string, title: string, kind = "task"): ElementOut => ({ uid, project_uid: "p0", kind, label, title, version: 1, deleted: false });

/** A detail view of a test plugin: shows what it gets and offers its close and select. */
function StoryView() {
	const { uid, kind, onClose, onSelect } = useShownElement();
	return (
		<div data-testid="test.story-view">
			{`${kind}:${uid}`}
			<button onClick={onClose}>zu</button>
			<button onClick={() => onSelect?.("other")}>anderes</button>
		</div>
	);
}

afterEach(cleanup);

describe("ElementDetail", () => {
	it("shows the view that the owner of the kind hangs into workspace.element-detail, with the element", async () => {
		const onClose = vi.fn();
		const onSelect = vi.fn();
		await renderWorkspace(<ElementDetail uid="s1" kind="story" onClose={onClose} onSelect={onSelect} />, {
			widgets: [{ ownerId: "backlog", slot: "workspace.element-detail", name: "story", component: StoryView }],
		});

		expect(screen.getByTestId("test.story-view").textContent).toContain("story:s1");
		fireEvent.click(screen.getByText("zu"));
		fireEvent.click(screen.getByText("anderes"));
		expect(onClose).toHaveBeenCalledTimes(1);
		expect(onSelect).toHaveBeenCalledWith("other");
	});

	it("shows a plain view with label, title and links when no plugin shows the kind", async () => {
		const onClose = vi.fn();
		const backend = fakeWorkspaceBackend({ elements: [element("t1", "TOPIC-001", "Thema", "topic"), element("b", "TASK-001", "Umsetzen")], links: [["l1", "t1", "b", "reference"]] });
		await renderWorkspace(<ElementDetail uid="t1" kind="topic" label="TOPIC-001" title="Thema" onClose={onClose} />, {
			backend,
			widgets: [{ ownerId: "backlog", slot: "workspace.element-detail", name: "story", component: StoryView }],
		});

		const plain = screen.getByTestId(ids.elementDetailPlain);
		expect(screen.getByTestId(sharedTestIds.detailTitle).textContent).toBe("TOPIC-001 — Thema");
		expect(screen.queryByTestId("test.story-view")).toBeNull();
		expect((await screen.findByTestId(ids.link("l1"))).textContent).toContain("TASK-001 — Umsetzen");
		expect(plain.querySelector(`[data-testid="${ids.linkAdd}"]`)).toBeNull();
		fireEvent.click(screen.getByTestId(sharedTestIds.detailAction("close")));
		expect(onClose).toHaveBeenCalledTimes(1);
	});
});
