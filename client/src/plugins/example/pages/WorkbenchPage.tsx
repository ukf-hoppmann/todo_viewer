import SaveIcon from "@mui/icons-material/Save";
import { Box } from "@mui/material";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { usePersistentState } from "../../../core";
import { buildTree, DetailField, DetailPanel, DetailSection, InlineField, MarkdownEditor, TreeView, type FlatNode } from "../../../shared";
import { exampleTestIds } from "../testIds";

interface Entry extends FlatNode {
	note: string;
}

const initial: Entry[] = [
	{ id: "e1", parentId: null, label: "Epic", badge: "EPIC-1", statusColor: "#d59a3a", progress: { done: 1, total: 2 }, note: "# Epic\n\nEin **Beispiel**-Epic." },
	{ id: "s1", parentId: "e1", label: "Story eins", badge: "STORY-1", statusColor: "#3ab26b", note: "Fertig." },
	{ id: "s2", parentId: "e1", label: "Story zwei", badge: "STORY-2", statusColor: "#6b7280", note: "## Offen\n\n- a\n- b" },
];

/**
 * A page that uses the shared building blocks together: the tree (open nodes kept in the UI state of the
 * server), the detail panel with an inline field and a section with the markdown editor. The data is local
 * demo data; real plugins read it from their own API.
 */
export default function WorkbenchPage() {
	const { t } = useTranslation("example");
	const [entries, setEntries] = useState(initial);
	const [selectedId, setSelectedId] = useState<string | null>("e1");
	const [expandedIds, setExpandedIds] = usePersistentState<string[]>("example", "expanded", ["e1"]);
	const expanded = useMemo(() => new Set(expandedIds), [expandedIds]);
	const nodes = useMemo(() => buildTree(entries.map((entry) => ({ id: entry.id, parentId: entry.parentId, label: entry.label, badge: entry.badge, statusColor: entry.statusColor, progress: entry.progress }))), [entries]);
	const selected = entries.find((entry) => entry.id === selectedId);
	const update = (id: string, change: Partial<Entry>) => setEntries((current) => current.map((entry) => (entry.id === id ? { ...entry, ...change } : entry)));

	return (
		<Box sx={{ display: "flex", gap: 2, p: 2, alignItems: "flex-start" }}>
			<Box sx={{ width: 320, flexShrink: 0 }}>
				<TreeView
					ariaLabel={t("workbench.tree")}
					nodes={nodes}
					expanded={expanded}
					onToggle={(id) => setExpandedIds((current) => (current.includes(id) ? current.filter((entry) => entry !== id) : [...current, id]))}
					selectedId={selectedId}
					onSelect={setSelectedId}
					canDrop={(source, target, position) => position !== "inside" || target.parentId !== source.id}
					onDrop={({ sourceId, targetId, position }) => {
						const target = entries.find((entry) => entry.id === targetId);
						update(sourceId, { parentId: position === "inside" ? targetId : (target?.parentId ?? null) });
					}}
				/>
			</Box>
			{selected && (
				<Box sx={{ flexGrow: 1, minWidth: 0 }}>
					<DetailPanel
						title={selected.label}
						subtitle={selected.badge}
						actions={[{ id: "save", label: t("workbench.save"), icon: SaveIcon, onClick: () => {} }]}
					>
						<InlineField id="title" kind="text" label={t("workbench.title")} value={selected.label} onSave={(label) => update(selected.id, { label })} />
						<DetailField id="id" label={t("workbench.id")}>
							<span data-testid={exampleTestIds.workbenchSelected}>{selected.id}</span>
						</DetailField>
						<DetailSection id="note" title={t("workbench.note")}>
							<MarkdownEditor
								key={selected.id}
								ariaLabel={t("workbench.note")}
								value={selected.note}
								onChange={(note) => update(selected.id, { note })}
								onSave={async () => {}}
								onShowCurrent={() => {}}
							/>
						</DetailSection>
					</DetailPanel>
				</Box>
			)}
		</Box>
	);
}
