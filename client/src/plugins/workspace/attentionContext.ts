import { createContext, useContext, useEffect, useMemo } from "react";
import { attentionFor, type AttentionEntry } from "./attention";

export interface AttentionState {
	entries: AttentionEntry[];
	report(source: string, entries: AttentionEntry[]): void;
}

export const AttentionContext = createContext<AttentionState>({ entries: [], report: () => {} });
/** The source being drawn (`<owner id>/<name>` of its slot entry). */
export const SourceContext = createContext<string | undefined>(undefined);

/** A source in `workspace.attention-sources` reports its due entries with this (keep the array stable, e.g. `useMemo`). */
export function useReportAttention(entries: AttentionEntry[]): void {
	const source = useContext(SourceContext);
	const { report } = useContext(AttentionContext);
	useEffect(() => {
		if (source === undefined) return;
		report(source, entries);
	}, [source, entries, report]);
	useEffect(() => {
		if (source === undefined) return;
		return () => report(source, []);
	}, [source, report]);
}

/** The due entries, the newest first; only those of one project if `projectUid` is given. */
export function useAttention(projectUid?: string): AttentionEntry[] {
	const { entries } = useContext(AttentionContext);
	return useMemo(() => attentionFor(entries, projectUid), [entries, projectUid]);
}
