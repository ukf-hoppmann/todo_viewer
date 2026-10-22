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
