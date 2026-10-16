import { useNoteLinks, useNotesLinkedToItem } from "../api/queries";
import { type Item, uidOf } from "../domain/model";
import { useI18n } from "../i18n/i18n";
import { useUiState } from "../state/useUiStateStore";

/** At an item: "From note NOTE-001", a jump to the note it was promoted from. Nothing if it has no such origin. */
export function ItemOrigin({ item }: { item: Item }) {
  const { t } = useI18n();
  const { dispatch } = useUiState();
  const linked = useNotesLinkedToItem(item.project, item.id);
  const origin = linked.data?.find((n) => n.role === "origin");
  if (!origin) return null;
  return (
    <button className="link-btn origin-link" onClick={() => dispatch({ type: "openNote", note: { project: origin.project, label: origin.label } })}>
      {t("origin.fromNote", { note: `${origin.project} · ${origin.label}` })}
    </button>
  );
}

/** At a note: "Origin: item …" for a note that came from an item, "Became item …" for a promoted one. */
export function NoteOrigin({ project, label, promoted }: { project: string; label: string; promoted: boolean }) {
  const { t } = useI18n();
  const { dispatch } = useUiState();
  const links = useNoteLinks(project, label);
  const origin = links.data?.find((l) => l.role === "origin" && l.kind === "item");
  if (!origin) return null;
  const open = () => {
    dispatch({ type: "view", view: "tree" });
    dispatch({ type: "select", uid: uidOf(origin.target_project, origin.target) });
  };
  return (
    <button className="link-btn origin-link" onClick={open}>
      {t(promoted ? "origin.becameItem" : "origin.fromItem", { item: origin.target_display })}
    </button>
  );
}
