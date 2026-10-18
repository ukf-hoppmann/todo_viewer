import { coreSlotNames, isWidgetContribution, parseSlot } from "./contributions";
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
}

/**
 * Checks the widgets of a plugin against the slots they hang in. The host of a slot is the plugin itself, a
 * plugin it requires, or the core; it must provide a slot of that name (the core provides `settings-sections`
 * and `sidebar-sections`). Returns the problems, English, each naming the contribution; an empty list means
 * they are valid.
 */
export function checkSlots({ id, requires, contributions, slots = [], registered }: CheckSlotsInput): string[] {
	const problems: string[] = [];

	for (const contribution of contributions) {
		if (!isWidgetContribution(contribution)) continue;
		const { slot, name } = contribution;
		const parsed = parseSlot(slot);
		if (!parsed) continue;
		const { hostId, hostName } = parsed;
		const label = `contribution '${name}'`;

		if (hostId !== id && hostId !== "core" && !requires.includes(hostId)) {
			problems.push(`${label}: the host '${hostId}' of the slot '${slot}' is not required`);
			continue;
		}

		const provided = hostId === id ? slots : hostId === "core" ? coreSlotNames : (registered.get(hostId)?.slots ?? []);
		if (!provided.includes(hostName)) problems.push(`${label}: the slot '${slot}' does not exist ('${hostId}' provides no slot '${hostName}')`);
	}

	return problems;
}
