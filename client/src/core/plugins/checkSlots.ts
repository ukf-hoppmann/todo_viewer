import { coreSlotNames, hasSidebar, isMainContribution, isSidebarEntry, isWidgetContribution, parseSlot } from "./contributions";
import type { Contribution } from "./types";

/** What another plugin offers to hang into: its contributions and the slots it provides. */
export interface RegisteredPlugin {
	contributions: readonly Contribution[];
	/** Names of the slots the plugin provides (`PluginDefinition.slots`). */
	slots: readonly string[];
}

interface CheckSlotsInput {
	/** The plugin whose entries are checked. */
	id: string;
	/** Ids in the `requires` of that plugin. */
	requires: readonly string[];
	/** Its contributions (already valid in form, see `checkContributions`). */
	contributions: readonly Contribution[];
	/** The slots it provides itself. */
	slots?: readonly string[];
	/** Every plugin registered before it, by id. */
	registered: ReadonlyMap<string, RegisteredPlugin>;
	/** The contributions of the core. */
	core: readonly Contribution[];
}

/**
 * Checks the entries of a plugin against the slots they hang in. The host of a slot is the plugin itself, a
 * plugin it requires, or the core. A sidebar entry needs a main route of that name with a sidebar at the
 * host; a widget needs a slot of that name that the host provides (the core provides `settings-sections`).
 * Returns the problems, English, each naming the contribution; an empty list means they are valid.
 */
export function checkSlots({ id, requires, contributions, slots = [], registered, core }: CheckSlotsInput): string[] {
	const problems: string[] = [];

	for (const contribution of contributions) {
		if (!isSidebarEntry(contribution) && !isWidgetContribution(contribution)) continue;
		const { slot, name } = contribution;
		const parsed = parseSlot(slot);
		if (!parsed) continue;
		const { hostId, hostName } = parsed;
		const label = `contribution '${name}'`;

		if (hostId !== id && hostId !== "core" && !requires.includes(hostId)) {
			problems.push(`${label}: the host '${hostId}' of the slot '${slot}' is not required`);
			continue;
		}

		if (isWidgetContribution(contribution)) {
			const provided = hostId === id ? slots : hostId === "core" ? coreSlotNames : (registered.get(hostId)?.slots ?? []);
			if (!provided.includes(hostName)) problems.push(`${label}: the slot '${slot}' does not exist ('${hostId}' provides no slot '${hostName}')`);
			continue;
		}

		const hostContributions = hostId === id ? contributions : hostId === "core" ? core : registered.get(hostId)?.contributions;
		const hasHost = hostContributions?.some(
			(candidate) => isMainContribution(candidate) && candidate.name === hostName && hasSidebar(candidate),
		);
		if (!hasHost) problems.push(`${label}: the slot '${slot}' does not exist (no main route '${hostName}' with a sidebar at '${hostId}')`);
	}

	return problems;
}
