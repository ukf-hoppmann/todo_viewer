import type { SlotEntry } from "../plugins/useSlot";

/** The groups of the settings page, in the order of the navigation. Texts: `settings.groups.<group>`. */
export const settingsGroups = ["projects", "system"] as const;

export type SettingsGroup = (typeof settingsGroups)[number];

/** The group of a section without a group or with a group the core does not know. */
const fallbackGroup: SettingsGroup = "system";

/** Whether a text (e.g. from the URL) names a group of the core. */
export function isSettingsGroup(value: string | null | undefined): value is SettingsGroup {
	return (settingsGroups as readonly string[]).includes(value ?? "");
}

/** Sorts the sections of the settings slot into their groups; the order within a group stays that of the slot. */
export function groupSettingsSections(entries: readonly SlotEntry[]): Record<SettingsGroup, SlotEntry[]> {
	const grouped: Record<SettingsGroup, SlotEntry[]> = { projects: [], system: [] };
	for (const entry of entries) grouped[isSettingsGroup(entry.group) ? entry.group : fallbackGroup].push(entry);
	return grouped;
}

/** The group shown without a valid request: the first one that has sections, otherwise the first. */
export function defaultSettingsGroup(grouped: Record<SettingsGroup, readonly SlotEntry[]>): SettingsGroup {
	return settingsGroups.find((group) => grouped[group].length > 0) ?? settingsGroups[0];
}
