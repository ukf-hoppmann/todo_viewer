export interface Entity {
	id: string;
	/** The label of the element (`STORY-012`). */
	label: string;
	title: string;
}

/** The text of an element in the lists: `STORY-012 — Title`. */
export function entityText(entity: Entity): string {
	return `${entity.label} — ${entity.title}`;
}
