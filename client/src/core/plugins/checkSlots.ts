import { hasSidebar, isMainContribution, isSidebarEntry, parseSlot } from "./contributions";
import type { Contribution } from "./types";

interface CheckSlotsInput {
	/** The plugin whose entries are checked. */
	id: string;
	/** Ids in the `requires` of that plugin. */
	requires: readonly string[];
	/** Its contributions (already valid in form, see `checkContributions`). */
	contributions: readonly Contribution[];
	/** The contributions of every plugin registered before it, by id. */
	registered: ReadonlyMap<string, readonly Contribution[]>;
	/** The contributions of the core. */
	core: readonly Contribution[];
}

/**
 * Checks the entries of a plugin against the sidebars they hang in: the host
 * of the slot is the plugin itself, a plugin it requires, or the core, and the
 * host has a main route of that name with a sidebar. Returns the problems,
 * English, each naming the contribution; an empty list means they are valid.
 */
export function checkSlots({ id, requires, contributions, registered, core }: CheckSlotsInput): string[] {
	const problems: string[] = [];

	for (const contribution of contributions.filter(isSidebarEntry)) {
		const { slot, name } = contribution;
		const parsed = parseSlot(slot);
		if (!parsed) continue;
		const { hostId, hostName } = parsed;
		const label = `contribution '${name}'`;

		if (hostId !== id && hostId !== "core" && !requires.includes(hostId)) {
			problems.push(`${label}: the host '${hostId}' of the slot '${slot}' is not required`);
			continue;
		}

		const hostContributions = hostId === id ? contributions : hostId === "core" ? core : registered.get(hostId);
		const hasHost = hostContributions?.some(
			(candidate) => isMainContribution(candidate) && candidate.name === hostName && hasSidebar(candidate),
		);
		if (!hasHost) problems.push(`${label}: the slot '${slot}' does not exist (no main route '${hostName}' with a sidebar at '${hostId}')`);
	}

	return problems;
}
