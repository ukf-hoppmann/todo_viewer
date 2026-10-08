import { useState } from "react";
import { useAddLink, useNoteLinks, useRemoveLink } from "../api/queries";
import type { Schemas } from "../api/client";
import type { IndexNote, IndexTopic } from "../domain/notes";
import { type Item, uidOf } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import type { MessageKey } from "../i18n/messages";
import type { NoteRef } from "../state/uiState";
import { ItemPicker } from "./ItemPicker";

interface NoteLinksProps {
  project: string;
  label: string;
  /** Closed or deleted notes can be read but not changed. */
  readOnly: boolean;
  projects: readonly string[];
  topics: readonly IndexTopic[];
  notes: readonly IndexNote[];
  items: readonly Item[];
  onOpenNote: (note: NoteRef) => void;
}

type Kind = Schemas["LinkIn"]["kind"];

/** The links of a note: shown with project and label, set to an item (also of another project), a topic or a note. */
export function NoteLinks({ project, label, readOnly, projects, topics, notes, items, onOpenNote }: NoteLinksProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const links = useNoteLinks(project, label);
  const add = useAddLink();
  const remove = useRemoveLink();
  const [adding, setAdding] = useState(false);
  const [kind, setKind] = useState<Kind>("item");
  const [targetProject, setTargetProject] = useState(project);
  const [search, setSearch] = useState("");
  const [target, setTarget] = useState("");

  const otherNotes = notes.filter((n) => !(n.project === project && n.label === label));
  const choices: { value: string; text: string }[] =
    kind === "topic"
      ? topics.filter((x) => x.project === project).map((x) => ({ value: x.label, text: x.path.join(" › ") }))
      : otherNotes.map((n) => ({ value: `${n.project}/${n.label}`, text: `${n.project} · ${n.label} — ${n.summary}` }));

  const submit = () => {
    const [noteProject, noteLabel] = target.split("/");
    const request =
      kind === "note"
        ? { kind, target: noteLabel ?? "", target_project: noteProject ?? project }
        : kind === "item"
          ? { kind, target, target_project: targetProject }
          : { kind, target, target_project: project };
    add.mutate({ project, label, role: "reference", ...request }, { onSuccess: () => { setAdding(false); setTarget(""); setSearch(""); } });
  };

  const titleOf = (link: Schemas["LinkOut"]) => {
    if (link.kind !== "item") return null;
    return items.find((i) => i.uid === uidOf(link.target_project, link.target)) ?? null;
  };

  return (
    <section className="note-section">
      <h3>{t("note.links.title")}</h3>
      {links.data?.length === 0 && <div className="hint">{t("note.links.empty")}</div>}
      <ul className="note-links">
        {(links.data ?? []).map((link) => {
          const item = titleOf(link);
          return (
            <li key={link.id} className="note-link">
              <span className={`badge link-${link.role}`}>{t(`note.link.role.${link.role}` as MessageKey)}</span>
              {link.kind === "note" ? (
                <button className="link-btn" onClick={() => onOpenNote({ project: link.target_project, label: link.target })}>
                  {link.target_display}
                </button>
              ) : (
                <span className="mono">{link.target_display}</span>
              )}
              {item && <span className="note-link-title">{item.title}</span>}
              {item && <span className="hint">{i18n.vocab("status", item.status)}</span>}
              {!link.reachable && <span className="badge unreachable" title={link.unreachable_reason ?? ""}>{t("note.links.unreachable")}</span>}
              {!readOnly && link.role === "reference" && (
                <button className="btn small" disabled={remove.isPending} onClick={() => remove.mutate({ project, label, linkId: link.id })}>
                  {t("note.links.remove")}
                </button>
              )}
            </li>
          );
        })}
      </ul>
      {(links.error || remove.error) && (
        <div className="field-error" role="alert">
          {describeError(i18n, links.error ?? remove.error)}
        </div>
      )}
      {!readOnly && !adding && (
        <button className="btn small" onClick={() => setAdding(true)}>
          {t("note.links.add")}
        </button>
      )}
      {!readOnly && adding && (
        <form
          className="edit-form note-link-form"
          aria-label={t("note.links.add")}
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <label className="field">
            {t("note.links.kind")}
            <select
              value={kind}
              onChange={(e) => {
                setKind(e.target.value as Kind);
                setTarget("");
              }}
            >
              {(["item", "topic", "note"] as const).map((k) => (
                <option key={k} value={k}>
                  {t(`note.links.kind.${k}` as MessageKey)}
                </option>
              ))}
            </select>
          </label>
          {kind === "item" ? (
            <ItemPicker
              projects={projects}
              items={items}
              project={targetProject}
              onProject={setTargetProject}
              value={target}
              onChange={setTarget}
              search={search}
              onSearch={setSearch}
            />
          ) : (
            <label className="field">
              {t("note.links.target")}
              <select value={target} onChange={(e) => setTarget(e.target.value)}>
                <option value="" />
                {choices.map((c) => (
                  <option key={c.value} value={c.value}>
                    {c.text}
                  </option>
                ))}
              </select>
            </label>
          )}
          {add.error && (
            <div className="field-error" role="alert">
              {t("err.save", { e: describeError(i18n, add.error) })}
            </div>
          )}
          <div className="modal-actions">
            <button type="button" className="btn" onClick={() => setAdding(false)}>
              {t("cancel")}
            </button>
            <button type="submit" className="btn primary" disabled={add.isPending || target === ""}>
              {add.isPending ? t("saving") : t("note.links.submit")}
            </button>
          </div>
        </form>
      )}
    </section>
  );
}
