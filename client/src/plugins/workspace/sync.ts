import type { Project, SyncChoice, SyncConflict, SyncDirection, SyncStatus } from "./api";

/** How a project's mirror is doing, for the sidebar and the project card. */
export type SyncView =
	| { kind: "off" }
	| { kind: "loading" }
	| { kind: "in_sync" }
	/** Changes wait or a conflict needs a decision. */
	| { kind: "needs_you"; changes: boolean; conflicts: number }
	/** The mirror cannot be read or written now (`reason`: `missing`, `merge_markers`, `format_version` …). */
	| { kind: "paused"; reason: string | null };

export function syncView(project: Pick<Project, "mirror_enabled">, status: SyncStatus | undefined): SyncView {
	if (!project.mirror_enabled) return { kind: "off" };
	if (!status) return { kind: "loading" };
	if (status.state === "in_sync") return { kind: "in_sync" };
	if (status.state === "paused") return { kind: "paused", reason: status.reason ?? null };
	return { kind: "needs_you", changes: status.to_database + status.to_files > 0, conflicts: status.conflicts };
}

/** ⚠ in the sidebar: the owner has to do something. */
export function needsAttention(view: SyncView): boolean {
	return view.kind === "needs_you" || view.kind === "paused";
}

/** What a conflict is about: one side no longer has the entry. */
export function isDeletionConflict(conflict: SyncConflict): boolean {
	return conflict.conflict === "deleted_in_files" || conflict.conflict === "deleted_in_database";
}

/** Whether choosing `choice` for this conflict deletes an entry (in the database or in the files). */
export function choiceDeletes(conflict: SyncConflict, choice: SyncChoice): boolean {
	if (conflict.conflict === "deleted_in_files") return choice === "files";
	if (conflict.conflict === "deleted_in_database") return choice === "database";
	return false;
}

/** Whether the direction forbids `choice`: taking the database writes the files, taking the files writes the database. */
export function choiceBlocked(direction: SyncDirection, choice: SyncChoice): boolean {
	return (direction === "to_files" && choice === "files") || (direction === "to_database" && choice === "database");
}

/** What choosing `choice` does to the other side, as the key of the explanation shown next to the option. */
export function choiceEffect(conflict: SyncConflict, choice: SyncChoice): string {
	if (choice === "defer") return "defer";
	if (choiceDeletes(conflict, choice)) return `${choice}Deletes`;
	if (isDeletionConflict(conflict)) return `${choice}Recreates`;
	return choice;
}

export type Choices = Record<string, SyncChoice>;

/** The choice for every conflict that a bulk button may set: deletions are left out, they are chosen one by one. */
export function withBulkChoice(conflicts: readonly SyncConflict[], current: Choices, choice: SyncChoice, direction: SyncDirection = "both"): Choices {
	const next = { ...current };
	if (choiceBlocked(direction, choice)) return next;
	for (const conflict of conflicts) {
		if (!choiceDeletes(conflict, choice)) next[conflict.key] = choice;
	}
	return next;
}

/** The decisions to send, without the ones that defer, and whether one of them deletes (`delete_missing`). */
export function decisionsOf(conflicts: readonly SyncConflict[], choices: Choices) {
	const decisions = conflicts.flatMap((conflict) => {
		const choice = choices[conflict.key];
		return choice && choice !== "defer" ? [{ uid: conflict.key, choice }] : [];
	});
	const deleteMissing = conflicts.some((conflict) => {
		const choice = choices[conflict.key];
		return choice !== undefined && choiceDeletes(conflict, choice);
	});
	return { decisions, deleteMissing };
}

export interface FieldDifference {
	name: string;
	database: string;
	files: string;
}

type EntryView = { fields?: Record<string, unknown>; refs?: Record<string, string[]> } | null;

function text(value: unknown): string {
	if (value === null || value === undefined || value === "") return "—";
	if (Array.isArray(value)) return value.length === 0 ? "—" : value.join(", ");
	if (typeof value === "boolean") return value ? "Yes" : "No";
	return String(value);
}

/** The fields and references that differ between the two sides of a conflict (all of them if a side is missing). */
export function differences(conflict: SyncConflict): FieldDifference[] {
	const database = conflict.database as EntryView;
	const files = conflict.files as EntryView;
	const names = new Set<string>();
	for (const side of [database, files]) {
		for (const name of Object.keys(side?.fields ?? {})) names.add(name);
		for (const name of Object.keys(side?.refs ?? {})) names.add(`ref:${name}`);
	}
	const read = (side: EntryView, name: string): unknown =>
		name.startsWith("ref:") ? (side?.refs?.[name.slice(4)] ?? []) : side?.fields?.[name];
	return [...names]
		.map((name) => ({ name: name.replace(/^ref:/, ""), database: text(read(database, name)), files: text(read(files, name)), raw: [read(database, name), read(files, name)] }))
		.filter((entry) => database === null || files === null || JSON.stringify(entry.raw[0] ?? null) !== JSON.stringify(entry.raw[1] ?? null))
		.map(({ name, database: db, files: fl }) => ({ name, database: db, files: fl }));
}

/** The key of the sentence that says where a conflict comes from; a deletion depends on whether the other side changed since the last sync. */
export function originKey(conflict: SyncConflict): string {
	const otherChanged = conflict.conflict === "deleted_in_files" ? conflict.database_changed : conflict.conflict === "deleted_in_database" ? conflict.files_changed : null;
	if (otherChanged === true || otherChanged === false) return `${conflict.conflict}_${otherChanged ? "changed" : "unchanged"}`;
	return conflict.conflict;
}

/** What a document conflict is about (spec or notes of an item), shown in the header instead of the rows `kind` and `item`. */
export function documentContext(conflict: SyncConflict): { kind: string; item: string | null } | null {
	if (conflict.kind !== "document") return null;
	const side = (conflict.database ?? conflict.files) as EntryView;
	const kind = side?.fields?.kind;
	if (typeof kind !== "string") return null;
	return { kind, item: side?.refs?.item?.[0] ?? null };
}

export type DiffLine = { op: "same" | "add" | "del"; text: string } | { op: "skip"; count: number };

const MAX_DIFF_CELLS = 1_000_000;

/** A line diff of two texts with `context` unchanged lines around each change; `null` if the texts are too long to compare. */
export function lineDiff(before: string, after: string, context = 2): DiffLine[] | null {
	const a = before.split("\n");
	const b = after.split("\n");
	if (a.length * b.length > MAX_DIFF_CELLS) return null;
	const lengths = Array.from({ length: a.length + 1 }, () => new Array<number>(b.length + 1).fill(0));
	for (let i = a.length - 1; i >= 0; i--) {
		for (let j = b.length - 1; j >= 0; j--) {
			lengths[i][j] = a[i] === b[j] ? lengths[i + 1][j + 1] + 1 : Math.max(lengths[i + 1][j], lengths[i][j + 1]);
		}
	}
	const lines: DiffLine[] = [];
	let i = 0;
	let j = 0;
	while (i < a.length || j < b.length) {
		if (i < a.length && j < b.length && a[i] === b[j]) {
			lines.push({ op: "same", text: a[i] });
			i++;
			j++;
		} else if (i < a.length && (j === b.length || lengths[i + 1][j] >= lengths[i][j + 1])) lines.push({ op: "del", text: a[i++] });
		else lines.push({ op: "add", text: b[j++] });
	}
	return collapse(lines, context);
}

/** `true` if two texts differ only in whitespace: line endings, indentation, trailing spaces, and empty lines. */
export function onlyWhitespaceDiffers(before: string, after: string): boolean {
	const normalize = (text: string) =>
		text
			.split(/\r?\n/)
			.map((line) => line.trim())
			.filter((line) => line !== "")
			.join("\n");
	return before !== after && normalize(before) === normalize(after);
}

/** A line as it is shown in a diff: an empty line becomes `null`; tabs, trailing spaces, and a carriage return are made visible. */
export function visibleWhitespace(line: string): string | null {
	if (line === "") return null;
	return line
		.replace(/\t/g, "→   ")
		.replace(/\r$/, "␍")
		.replace(/ +(?=␍?$)/, (spaces) => "·".repeat(spaces.length));
}

function collapse(lines: DiffLine[], context: number): DiffLine[] {
	const near = lines.map((line, index) => line.op !== "same" || lines.slice(Math.max(0, index - context), index + context + 1).some((other) => other.op !== "same"));
	const result: DiffLine[] = [];
	let hidden = 0;
	lines.forEach((line, index) => {
		if (near[index]) {
			if (hidden > 0) result.push({ op: "skip", count: hidden });
			hidden = 0;
			result.push(line);
		} else hidden++;
	});
	if (hidden > 0) result.push({ op: "skip", count: hidden });
	return result;
}
