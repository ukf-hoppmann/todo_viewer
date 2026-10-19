import AlarmIcon from "@mui/icons-material/Alarm";
import { cleanup, fireEvent, screen, waitFor, within } from "@testing-library/react";
import { useMemo } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { AttentionEntry } from "../../../../../../client/src/plugins/workspace/attention";
import { useReportAttention } from "../../../../../../client/src/plugins/workspace/attentionContext";
import { ProjectsSection } from "../../../../../../client/src/plugins/workspace/ProjectsSection";
import { workspaceTestIds as ids } from "../../../../../../client/src/plugins/workspace/testIds";
import { fakeWorkspaceBackend, project } from "../../../../../helpers/client/fakeWorkspaceBackend";
import { renderWorkspace } from "../../../../../helpers/client/renderWorkspace";

afterEach(cleanup);

const opened = vi.fn();
const done = vi.fn();

const entry = (uid: string, projectUid: string, dueSince: string): AttentionEntry => ({
	key: `test:${uid}`,
	projectUid,
	dueSince,
	icon: AlarmIcon,
	title: `Titel ${uid}`,
	caption: `Mehr zu ${uid}`,
	actions: [{ id: "done", label: "Erledigt", icon: AlarmIcon, run: () => done(uid), testId: `test.done.${uid}` }],
	open: () => opened(uid),
});

function sourceOf(entries: AttentionEntry[]) {
	return function Source() {
		useReportAttention(useMemo(() => entries, []));
		return null;
	};
}

async function renderWith(entries: AttentionEntry[]) {
	const backend = fakeWorkspaceBackend({ projects: [project("p0", "Allgemein", 0, { builtin: true }), project("p1", "Viewer", 1)] });
	await renderWorkspace(<ProjectsSection />, {
		backend,
		widgets: [{ ownerId: "test", slot: "workspace.attention-sources", name: "source", component: sourceOf(entries) }],
	});
	await screen.findByTestId(ids.project("p0"));
}

const three = () => [
	entry("old", "p1", "2026-10-19T07:00:00Z"),
	entry("new", "p1", "2026-10-19T09:00:00Z"),
	entry("other", "p0", "2026-10-19T08:00:00Z"),
];

describe("AttentionBell", () => {
	it("shows no bell while nothing is due", async () => {
		await renderWith([]);

		expect(screen.queryByTestId(ids.attentionBell)).toBeNull();
		expect(screen.queryByTestId(ids.attentionProjectBell("p1"))).toBeNull();
	});

	it("counts everything in the header and the entries of each project in its row", async () => {
		await renderWith(three());

		await waitFor(() => expect(screen.getByTestId(ids.attentionBell).textContent).toContain("3"));
		expect(screen.getByTestId(ids.attentionProjectBell("p1")).textContent).toContain("2");
		expect(screen.getByTestId(ids.attentionProjectBell("p0")).textContent).toContain("1");
		await waitFor(() => expect(document.title).toMatch(/^\(3\)/));
	});

	it("lists the newest first and unfolded, the others folded", async () => {
		await renderWith(three());

		fireEvent.click(await screen.findByTestId(ids.attentionBell));
		const list = await screen.findByTestId(ids.attentionList);
		const items = within(list).getAllByTestId(/^workspace\.attention-item\./);
		expect(items.map((item) => item.getAttribute("data-testid"))).toEqual([
			ids.attentionItem("test:new"),
			ids.attentionItem("test:other"),
			ids.attentionItem("test:old"),
		]);
		expect(within(items[0]!).getByText("Mehr zu new")).toBeTruthy();
		expect(within(items[1]!).queryByText("Mehr zu other")).toBeNull();

		fireEvent.click(screen.getByTestId(ids.attentionToggle("test:old")));
		expect(within(items[2]!).getByText("Mehr zu old")).toBeTruthy();
		fireEvent.click(screen.getByTestId("test.done.new"));
		expect(done).toHaveBeenCalledWith("new");
	});

	it("lists only the entries of the project from its row, even a single one", async () => {
		await renderWith(three());

		fireEvent.click(await screen.findByTestId(ids.attentionProjectBell("p0")));
		const list = await screen.findByTestId(ids.attentionList);

		expect(within(list).getAllByTestId(/^workspace\.attention-item\./).map((item) => item.getAttribute("data-testid"))).toEqual([ids.attentionItem("test:other")]);
	});

	it("opens the element and closes the list", async () => {
		await renderWith(three());

		fireEvent.click(await screen.findByTestId(ids.attentionBell));
		fireEvent.click(await screen.findByTestId(ids.attentionOpen("test:other")));

		expect(opened).toHaveBeenCalledWith("other");
		await waitFor(() => expect(screen.queryByTestId(ids.attentionList)).toBeNull());
	});
});
