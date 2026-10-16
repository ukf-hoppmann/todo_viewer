import type { Contribution } from "../core";

/**
 * What the core itself contributes to slots (tabs and sidebar entries); none
 * yet. Both the plugin registry and the router read this list, so the
 * entries that plugins hang into a sidebar of the core are checked against it.
 */
export const coreContributions: readonly Contribution[] = [];
