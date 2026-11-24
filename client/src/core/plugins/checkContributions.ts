import { mainSlot, parseSlot, settingsSlot } from "./contributions";

const kebabCase = /^[a-z0-9]+(-[a-z0-9]+)*$/;

const layoutSwitches = ["header", "sidebar", "detail"];

function isObject(value: unknown): value is Record<string, unknown> {
	return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** A component is a function or an object such as `memo(...)` or `forwardRef(...)` (MUI icons). */
function isComponent(value: unknown): boolean {
	return typeof value === "function" || isObject(value);
}

/** A slot is `core.main` or `<host id>.<host name>`, both parts kebab-case. */
function isSlot(value: unknown): value is string {
	if (typeof value !== "string") return false;
	const parts = parseSlot(value);
	return parts !== undefined && kebabCase.test(parts.hostId) && kebabCase.test(parts.hostName);
}

export interface CheckContributionsOptions {
	/** Names the owner must not use, e.g. `link` and `login` for the core. */
	reservedNames?: readonly string[];
}

/** A widget: a component in a slot, with an optional order and the main routes it belongs to. */
function checkWidget(
	contribution: Record<string, unknown>,
	label: string,
	problems: string[],
	seen: Set<string>,
	reservedNames: readonly string[],
): void {
	const { slot, name, component, order, when, group, title, icon, page, layout } = contribution;
	const problem = (message: string) => problems.push(`${label}: ${message}`);
	if (!isSlot(slot)) problem(`the slot '${String(slot)}' is not of the form <owner id>.<name>`);
	else if (slot === mainSlot) problem("a widget cannot hang into 'core.main'");
	if (typeof name !== "string" || name === "") problem("`name` is missing");
	else if (!kebabCase.test(name)) problem("`name` is not kebab-case");
	else if (reservedNames.includes(name)) problem("the name is reserved");
	if (!isComponent(component)) problem("`component` is no component");
	if (order !== undefined && (typeof order !== "number" || !Number.isFinite(order))) problem("`order` is no number");
	if (when !== undefined) {
		if (!Array.isArray(when) || when.some((route) => typeof route !== "string" || !/^[a-z0-9-]+\/[a-z0-9-]+$/.test(route))) {
			problem("`when` is no list of main routes (`<owner id>/<name>`)");
		}
	}
	if (group !== undefined) {
		if (slot !== settingsSlot) problem(`\`group\` is only allowed in '${settingsSlot}'`);
		else if (typeof group !== "string" || !kebabCase.test(group)) problem("`group` is not kebab-case");
	}
	for (const [key, value] of Object.entries({ title, icon, page, layout })) {
		if (value !== undefined) problem(`\`${key}\` is not allowed in a widget`);
	}
	if (typeof slot === "string" && typeof name === "string") {
		const key = `${slot}/${name}`;
		if (seen.has(key)) problem(`the name is used twice in '${slot}'`);
		seen.add(key);
	}
}

/**
 * Checks the contributions of a plugin definition (or of the core) at
 * runtime; the types of `definePlugin` do not reach a plugin that was built
 * wrong. Returns the problems, English, each naming the contribution; an empty
 * list means the contributions are valid. Whether the host of an entry exists
 * and is required is checked by the registry, which knows the other plugins.
 */
export function checkContributions(contributions: unknown, { reservedNames = [] }: CheckContributionsOptions = {}): string[] {
	if (contributions === undefined) return [];
	if (!Array.isArray(contributions)) return ["`contributions` is no list"];

	const problems: string[] = [];
	const seen = new Set<string>();

	contributions.forEach((contribution: unknown, index) => {
		if (!isObject(contribution)) {
			problems.push(`contribution #${index} is no object`);
			return;
		}
		const { slot, name, title, icon, page, layout, component } = contribution;
		const label = typeof name === "string" && name !== "" ? `contribution '${name}'` : `contribution #${index}`;
		const problem = (message: string) => problems.push(`${label}: ${message}`);

		if (component !== undefined) {
			checkWidget(contribution, label, problems, seen, reservedNames);
			return;
		}

		const validSlot = isSlot(slot);
		if (!validSlot) problem(`the slot '${String(slot)}' is not of the form <owner id>.<name>`);
		if (typeof name !== "string" || name === "") problem("`name` is missing");
		else if (!kebabCase.test(name)) problem("`name` is not kebab-case");
		else if (reservedNames.includes(name)) problem("the name is reserved");
		if (typeof title !== "string" || title === "") problem("`title` is missing");
		if (!isComponent(icon)) problem("`icon` is no component");

		// Without a `component` a contribution is a main route; anything else hangs a component into a slot.
		if (validSlot && slot !== mainSlot) problem(`a contribution to '${String(slot)}' needs a \`component\``);

		if (layout !== undefined) {
			if (!isObject(layout)) problem("`layout` is no object");
			else {
				for (const [key, value] of Object.entries(layout)) {
					if (key === "detailWidth") {
						if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) problem("`layout.detailWidth` is no positive number");
					} else if (!layoutSwitches.includes(key)) problem(`\`layout.${key}\` is unknown`);
					else if (typeof value !== "boolean") problem(`\`layout.${key}\` is no boolean`);
				}
			}
		}

		if (typeof page !== "function") problem("`page` is no function");

		if (typeof slot === "string" && typeof name === "string") {
			const key = `${slot}/${name}`;
			if (seen.has(key)) problem(`the name is used twice in '${slot}'`);
			seen.add(key);
		}
	});

	return problems;
}
