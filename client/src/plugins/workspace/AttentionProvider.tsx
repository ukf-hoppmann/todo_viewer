import { useCallback, useMemo, useState, type ReactNode } from "react";
import { useSlot } from "../../core";
import { sortAttention, type AttentionEntry } from "./attention";
import { AttentionContext, SourceContext } from "./attentionContext";

/**
 * Draws the sources of the slot `workspace.attention-sources` (components without output) and collects what they
 * report through `useReportAttention`. The entries are only a view: the data stays in the API of the contributing
 * plugin.
 */
export function AttentionProvider({ children }: { children: ReactNode }) {
	const sources = useSlot("workspace.attention-sources");
	const [bySource, setBySource] = useState<ReadonlyMap<string, AttentionEntry[]>>(new Map());
	const report = useCallback((source: string, entries: AttentionEntry[]) => {
		setBySource((current) => {
			if (current.get(source) === entries || (entries.length === 0 && !current.has(source))) return current;
			const next = new Map(current);
			if (entries.length === 0) next.delete(source);
			else next.set(source, entries);
			return next;
		});
	}, []);
	const value = useMemo(() => ({ entries: sortAttention([...bySource.values()].flat()), report }), [bySource, report]);

	return (
		<AttentionContext.Provider value={value}>
			{sources.map((source) => (
				<SourceContext.Provider key={`${source.ownerId}/${source.name}`} value={`${source.ownerId}/${source.name}`}>
					<source.component />
				</SourceContext.Provider>
			))}
			{children}
		</AttentionContext.Provider>
	);
}
