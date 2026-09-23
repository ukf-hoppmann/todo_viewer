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
  initialPath: string;
  onClose: () => void;
}

export function DocumentDialog({ item, initialPath, onClose }: DocumentDialogProps) {
  const i18n = useI18n();
  const { t } = i18n;
  const [path, setPath] = useState(initialPath);
  const doc = useDocument(item.ref.source_id, path);
  const links = documentLinks(item, t("doc.notes"), t("doc.spec"));

  const html = useMemo(
    () => (doc.data ? DOMPurify.sanitize(marked.parse(doc.data.content, { async: false })) : ""),
    [doc.data],
  );

  return (
    <Modal labelledBy="doc-title" onDismiss={onClose} className="doc">
      <div className="doc-head">
        <h3 id="doc-title">{`${item.ref.id} — ${item.title}`}</h3>
        <button className="btn small" onClick={onClose}>
          {t("close")}
        </button>
      </div>
      <div className="doc-tabs" role="tablist">
        {links.map((link) => (
          <button
            key={link.path}
            role="tab"
            aria-selected={link.path === path}
            className={`doc-tab${link.path === path ? " active" : ""}`}
            title={link.path}
            onClick={() => setPath(link.path)}
          >
            {link.label}
          </button>
        ))}
      </div>
      <div className="doc-body">
        {doc.isLoading && <div className="md">{t("doc.loading")}</div>}
        {doc.error && <div className="md">{t("err.generic", { e: `${describeError(i18n, doc.error)} (${path})` })}</div>}
        {doc.data && <div className="md" dangerouslySetInnerHTML={{ __html: html }} />}
      </div>
    </Modal>
  );
}
