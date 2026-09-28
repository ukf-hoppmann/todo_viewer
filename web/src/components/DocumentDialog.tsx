import DOMPurify from "dompurify";
import { marked } from "marked";
import { useMemo, useState } from "react";
import { ApiError } from "../api/client";
import { fetchDocument, useAppendNotes, useDocument, useWriteDocument } from "../api/queries";
import { type NotesForm, notesRequest, specName } from "../domain/editing";
import type { Item } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import { documentLinks } from "./documentLinks";
import { Modal } from "./Modal";

export type DocumentMode = "view" | "note" | "newSpec";

interface DocumentDialogProps {
  item: Item;
  /** Document shown first; null when the dialog opens to write a note or a new spec. */
  initialName: string | null;
  initialMode?: DocumentMode;
  onClose: () => void;
}

function Markdown({ text }: { text: string }) {
  const html = useMemo(() => DOMPurify.sanitize(marked.parse(text, { async: false })), [text]);
  return <div className="md" dangerouslySetInnerHTML={{ __html: html }} />;
}

/** Reads notes/specs; appends notes entries and edits or creates specs. */
export function DocumentDialog({ item, initialName, initialMode = "view", onClose }: DocumentDialogProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const [name, setName] = useState(initialName);
  const [mode, setMode] = useState<DocumentMode | "edit">(initialMode);
  const doc = useDocument(item.source_id, item.id, mode === "view" || mode === "edit" ? name : null);
  const links = documentLinks(item, t("doc.notes"), t("doc.spec"));
  const current = links.find((l) => l.name === name);
  const show = (next: string) => {
    setName(next);
    setMode("view");
  };

  return (
    <Modal labelledBy="doc-title" onDismiss={onClose} className="doc">
      <div className="doc-head">
        <h3 id="doc-title">{`${item.id} — ${item.title}`}</h3>
        <button className="btn small" onClick={onClose}>
          {t("close")}
        </button>
      </div>
      <div className="doc-tabs" role="tablist">
        {links.map((link) => (
          <button
            key={link.name}
            role="tab"
            aria-selected={mode === "view" && link.name === name}
            className={`doc-tab${link.name === name && mode !== "note" && mode !== "newSpec" ? " active" : ""}`}
            title={link.name}
            onClick={() => show(link.name)}
          >
            {link.label}
          </button>
        ))}
        <span className="doc-tab-actions">
          <button className="btn small" onClick={() => setMode("note")}>
            {t("doc.addNote")}
          </button>
          <button className="btn small" onClick={() => setMode("newSpec")}>
            {t("doc.addSpec")}
          </button>
          {mode === "view" && current && doc.data && (
            <button className="btn small" onClick={() => setMode("edit")}>
              {t("edit.button")}
            </button>
          )}
        </span>
      </div>
      <div className="doc-body">
        {mode === "view" && name && (
          <>
            {doc.isLoading && <div className="md">{t("doc.loading")}</div>}
            {doc.error && <div className="md">{t("err.generic", { e: `${describeError(i18n, doc.error)} (${name})` })}</div>}
            {doc.data && <Markdown text={doc.data.content} />}
          </>
        )}
        {mode === "view" && !name && <p className="empty-hint">{t("doc.none")}</p>}
        {mode === "note" && <NoteForm item={item} onDone={show} onCancel={() => setMode("view")} />}
        {mode === "newSpec" && <DocumentEditor item={item} name={null} content="" version={null} onDone={show} onCancel={() => setMode("view")} />}
        {mode === "edit" && name && doc.data && (
          <DocumentEditor item={item} name={name} content={doc.data.content} version={doc.data.version} onDone={show} onCancel={() => setMode("view")} />
        )}
      </div>
    </Modal>
  );
}

function NoteForm({ item, onDone, onCancel }: { item: Item; onDone: (name: string) => void; onCancel: () => void }) {
  const i18n = useI18n();
  const { t, vocab } = i18n;
  const append = useAppendNotes();
  const [form, setForm] = useState<NotesForm>({ topic: "", discussed: "", decided: "", open: "", summary: "" });
  const set = (key: keyof NotesForm, value: string) => setForm((f) => ({ ...f, [key]: value }));
  const hasSummary = Boolean(item.summary);

  return (
    <form
      className="edit-form"
      aria-label={t("doc.addNote")}
      onSubmit={(e) => {
        e.preventDefault();
        append.mutate({ sourceId: item.source_id, itemId: item.id, body: notesRequest(form, hasSummary) }, { onSuccess: (doc) => onDone(doc.name) });
      }}
    >
      <label className="field">
        {t("doc.topic")}
        <input autoFocus value={form.topic} onChange={(e) => set("topic", e.target.value)} />
      </label>
      {(["discussed", "decided", "open"] as const).map((key) => (
        <label key={key} className="field">
          {t(`doc.${key}`)}
          <textarea value={form[key]} onChange={(e) => set(key, e.target.value)} />
        </label>
      ))}
      {!hasSummary && (
        <label className="field">
          {vocab("field", "Summary")}
          <textarea value={form.summary} onChange={(e) => set("summary", e.target.value)} />
        </label>
      )}
      <div className="hint">{t("doc.noteHint")}</div>
      {append.error && (
        <div className="field-error" role="alert">
          {t("err.save", { e: describeError(i18n, append.error) })}
        </div>
      )}
      <div className="modal-actions">
        <button type="button" className="btn" onClick={onCancel}>
          {t("cancel")}
        </button>
        <button type="submit" className="btn primary" disabled={append.isPending}>
          {append.isPending ? t("saving") : t("doc.appendNote")}
        </button>
      </div>
    </form>
  );
}

interface DocumentEditorProps {
  item: Item;
  /** Null for a new spec; its name then comes from the topic. */
  name: string | null;
  content: string;
  version: string | null;
  onDone: (name: string) => void;
  onCancel: () => void;
}

/** Edits the whole text of a notes or spec document (or a new spec) with a markdown preview.
 *  A version conflict keeps the text and can show the current state before saving anyway. */
function DocumentEditor({ item, name, content, version, onDone, onCancel }: DocumentEditorProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const write = useWriteDocument();
  const [text, setText] = useState(content);
  const [topic, setTopic] = useState("");
  const [base, setBase] = useState(version);
  const [theirs, setTheirs] = useState<string | null>(null);
  const target = name ?? specName(item.id, topic);
  const conflict = write.error instanceof ApiError && write.error.code === "version_conflict";

  const loadTheirs = async () => {
    const current = await fetchDocument(item.source_id, item.id, target);
    write.reset();
    setTheirs(current.content);
    setBase(current.version);
  };

  return (
    <form
      className="edit-form"
      aria-label={t("doc.edit")}
      onSubmit={(e) => {
        e.preventDefault();
        write.mutate({ sourceId: item.source_id, itemId: item.id, name: target, content: text, version: base }, { onSuccess: (doc) => onDone(doc.name) });
      }}
    >
      {name === null && (
        <label className="field">
          {t("doc.specTopic")}
          <input value={topic} onChange={(e) => setTopic(e.target.value)} />
          <span className="hint">{target}</span>
        </label>
      )}
      <div className="spec-editor">
        <label className="field">
          {t("doc.specText")}
          <textarea autoFocus={name !== null} value={text} onChange={(e) => setText(e.target.value)} />
        </label>
        <div className="spec-preview" aria-label={t("doc.preview")}>
          <Markdown text={text} />
        </div>
      </div>
      {theirs !== null && (
        <div className="warn-box">
          <div className="hint">{t("doc.theirs")}</div>
          <Markdown text={theirs} />
        </div>
      )}
      {write.error && (
        <div className="field-error" role="alert">
          {t("err.save", { e: describeError(i18n, write.error) })}
          {conflict && (
            <button type="button" className="btn small" onClick={loadTheirs}>
              {t("doc.showTheirs")}
            </button>
          )}
        </div>
      )}
      <div className="modal-actions">
        <button type="button" className="btn" onClick={onCancel}>
          {t("cancel")}
        </button>
        <button type="submit" className="btn primary" disabled={write.isPending || (name !== null && text === content && theirs === null)}>
          {write.isPending ? t("saving") : theirs !== null ? t("doc.overwrite") : t("save")}
        </button>
      </div>
    </form>
  );
}
