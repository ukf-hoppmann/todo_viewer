/**
 * URL form A (architecture rule 4): every part of a path starts with the id of
 * whoever contributes it. Paths are never put together by hand; views are
 * addressed with these functions.
 */

/** The path of a view: a main route is `/<owner id>/<name>`. */
export function viewPath(ownerId: string, name: string): string {
	return `/${ownerId}/${name}`;
}

/** A view written `<owner id>/<name>`, the form used in the app config. */
export function viewKey(ownerId: string, name: string): string {
	return `${ownerId}/${name}`;
}

export interface ParsedView {
	ownerId: string;
	name: string;
}

/** Reads `<owner id>/<name>`; nothing for anything else (leading slash, more or fewer parts). */
export function parseViewKey(key: string): ParsedView | undefined {
	const parts = key.split("/");
	const [ownerId, name] = parts;
	if (parts.length !== 2 || !ownerId || !name) return undefined;
	return { ownerId, name };
}

export interface ParsedPath {
	ownerId: string;
	/** Missing for a path of one part. */
	name: string | undefined;
	/** The parts after owner and name; a main route has none. */
	rest: string[];
}

/** Splits a location path into the owner of the view, its name and the remaining parts; nothing for `/`. */
export function parseViewPath(pathname: string): ParsedPath | undefined {
	const [ownerId, name, ...rest] = pathname.split("/").filter((part) => part !== "");
	if (!ownerId) return undefined;
	return { ownerId, name, rest };
}
