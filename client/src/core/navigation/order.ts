import { isMainContribution, isSidebarEntry, parseSlot } from "../plugins/contributions";
import type { ActivePlugin, Contribution } from "../plugins/types";
import { viewKey, viewPath } from "./paths";
import type { NavEntry, SidebarEntry } from "./types";

function mainEntries(ownerId: string, contributions: readonly Contribution[] | undefined): NavEntry[] {
	return (contributions ?? []).filter(isMainContribution).map((contribution) => ({ ownerId, name: contribution.name, contribution }));
}

/**
 * The tabs in the fixed order: the plugins by id, each in the order of its definition, then the
 * core (its settings tab belongs at the right end, behind the work of the plugins).
 */
export function collectMainEntries(plugins: readonly ActivePlugin[], coreContributions: readonly Contribution[]): NavEntry[] {
	const byId = [...plugins].sort((left, right) => left.id.localeCompare(right.id));
	return [...byId.flatMap(({ id, definition }) => mainEntries(id, definition.contributions)), ...mainEntries("core", coreContributions)];
}

function sidebarEntries(ownerId: string, contributions: readonly Contribution[] | undefined): SidebarEntry[] {
	return (contributions ?? []).filter(isSidebarEntry).flatMap((contribution) => {
		const parsed = parseSlot(contribution.slot);
		if (!parsed) return [];
		const { hostId, hostName } = parsed;
		return [{ ownerId, name: contribution.name, slot: contribution.slot, hostId, hostName, contribution }];
	});
}

/**
 * The entries of every sidebar, by slot, each in the fixed order: the entries
 * of the host itself first, then those of other plugins by id, each in the
 * order of its definition.
 */
export function collectSidebarEntries(plugins: readonly ActivePlugin[], coreContributions: readonly Contribution[]): Map<string, SidebarEntry[]> {
	const byId = [...plugins].sort((left, right) => left.id.localeCompare(right.id));
	const all = [...sidebarEntries("core", coreContributions), ...byId.flatMap(({ id, definition }) => sidebarEntries(id, definition.contributions))];

	const slots = new Map<string, SidebarEntry[]>();
	for (const entry of all) slots.set(entry.slot, [...(slots.get(entry.slot) ?? []), entry]);
	for (const [slot, entries] of slots) {
		slots.set(slot, [...entries.filter((entry) => entry.ownerId === entry.hostId), ...entries.filter((entry) => entry.ownerId !== entry.hostId)]);
	}
	return slots;
}

/**
 * Puts the entries named in `listed` (`<owner id>/<name>`) first, in the
 * order of the list; the others follow in their given order. Names that match
 * no entry are skipped and returned, so the caller can warn about them.
 */
export function orderEntries<T extends { ownerId: string; name: string }>(
	entries: readonly T[],
	listed: readonly string[] | undefined,
): { ordered: T[]; skipped: string[] } {
	const byKey = new Map(entries.map((entry) => [viewKey(entry.ownerId, entry.name), entry]));
	const first: T[] = [];
	const skipped: string[] = [];
	const used = new Set<string>();

	for (const key of listed ?? []) {
		const entry = byKey.get(key);
		if (!entry) skipped.push(key);
		else if (!used.has(key)) {
			used.add(key);
			first.push(entry);
		}
	}

	return { ordered: [...first, ...entries.filter((entry) => !used.has(viewKey(entry.ownerId, entry.name)))], skipped };
}

export interface StartResolution {
	/** The path `/` leads to; missing when there is no view to show. */
	to: string | undefined;
	/** The configured start view, if it could not be used. */
	unavailableStart?: string;
}

/**
 * Where `/` leads: to the configured start view (a tab or a sidebar entry),
 * else to the first tab. `isAvailable` tells whether a path can be shown.
 */
export function resolveStart(tabs: readonly NavEntry[], start: string | undefined, isAvailable: (path: string) => boolean): StartResolution {
	const first = tabs[0] ? viewPath(tabs[0].ownerId, tabs[0].name) : undefined;
	if (start === undefined) return { to: first };

	// The config writes a view as its path without the leading slash.
	const target = `/${start}`;
	return isAvailable(target) ? { to: target } : { to: first, unavailableStart: start };
}
