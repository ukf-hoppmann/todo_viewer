import DOMPurify from "dompurify";
import { marked } from "marked";
import { useMemo, useState } from "react";
import { useDocument } from "../api/queries";
import type { Item } from "../domain/model";
import { describeError, useI18n } from "../i18n/i18n";
import { documentLinks } from "./documentLinks";
import { Modal } from "./Modal";

interface DocumentDialogProps {
  item: Item;
  initialName: string;
  onClose: () => void;
}

export function DocumentDialog({ item, initialName, onClose }: DocumentDialogProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const [name, setName] = useState(initialName);
  const doc = useDocument(item.source_id, item.id, name);
  const links = documentLinks(item, t("doc.notes"), t("doc.spec"));

  const html = useMemo(
    () => (doc.data ? DOMPurify.sanitize(marked.parse(doc.data.content, { async: false })) : ""),
    [doc.data],
  );

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
            aria-selected={link.name === name}
            className={`doc-tab${link.name === name ? " active" : ""}`}
            title={link.name}
            onClick={() => setName(link.name)}
          >
            {link.label}
          </button>
        ))}
      </div>
      <div className="doc-body">
        {doc.isLoading && <div className="md">{t("doc.loading")}</div>}
        {doc.error && <div className="md">{t("err.generic", { e: `${describeError(i18n, doc.error)} (${name})` })}</div>}
        {doc.data && <div className="md" dangerouslySetInnerHTML={{ __html: html }} />}
      </div>
    </Modal>
  );
}
