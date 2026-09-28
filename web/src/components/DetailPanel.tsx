import { lazy, type ReactNode, Suspense, useState } from "react";
import { childTypes } from "../domain/editing";
import type { Item, Uid } from "../domain/model";
import type { SourceStatus } from "../api/client";
import { CreateItemDialog } from "./CreateItemDialog";
import { DeleteDialog } from "./DeleteDialog";
import { useI18n } from "../i18n/i18n";
import { documentLinks } from "./documentLinks";

import type { DocumentMode } from "./DocumentDialog";

// marked + DOMPurify are only loaded when a document is opened.
const DocumentDialog = lazy(() => import("./DocumentDialog").then((m) => ({ default: m.DocumentDialog })));
import { ItemEditForm } from "./ItemEditForm";

interface DetailPanelProps {
  item: Item;
  items: Item[];
  byUid: Map<Uid, Item>;
  sourcePath: string | undefined;
  sources: SourceStatus[];
  onSelect: (uid: Uid) => void;
  onClose: () => void;
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="detail-field">
      <div className="k">{label}</div>
      <div className="v">{children}</div>
    </div>
  );
}

function TextField({ label, value }: { label: string; value: string | null | undefined }) {
  return value ? <Field label={label}>{value}</Field> : null;
}

export function DetailPanel({ item, items, byUid, sourcePath, sources, onSelect, onClose }: DetailPanelProps) {
  const { t, vocab } = useI18n();
  const [openDoc, setOpenDoc] = useState<{ name: string | null; mode: DocumentMode } | null>(null);
  const [editing, setEditing] = useState(false);
  const [creatingChild, setCreatingChild] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const L = (field: string) => vocab("field", field);
  const parent = item.parentUid ? byUid.get(item.parentUid) : undefined;
  const children = items.filter((i) => i.parentUid === item.uid);
  const docs = documentLinks(item, t("doc.notes"), t("doc.spec"));

  return (
    <aside className="detail-panel" aria-label={item.title}>
      <button className="close-btn" aria-label={t("close")} onClick={onClose}>
        ✕
      </button>
      <h2>{item.title}</h2>
      <div className="detail-id">
        {[item.id, vocab("type", item.type), item.project, item.archived ? t("detail.archived") : null]
          .filter(Boolean)
          .join(" · ")}
      </div>

      {editing ? (
        <ItemEditForm item={item} items={items} onDone={() => setEditing(false)} />
      ) : (
        <div className="detail-actions">
          <button className="btn small" onClick={() => setEditing(true)}>
            {t("edit.button")}
          </button>
          {childTypes(item).length > 0 && (
            <button className="btn small" onClick={() => setCreatingChild(true)}>
              {t("create.child")}
            </button>
          )}
          <button className="btn small danger" onClick={() => setDeleting(true)}>
            {t("delete.button")}
          </button>
        </div>
      )}
      {!editing && item.summary && <div className="detail-summary">{item.summary}</div>}

      {!editing && (
        <div className="doc-buttons">
          {docs.map((d) => (
            <button key={d.name} className="btn small" onClick={() => setOpenDoc({ name: d.name, mode: "view" })}>
              {d.kind === "notes" ? "📝" : "📐"} {d.label}
            </button>
          ))}
          <button className="btn small" onClick={() => setOpenDoc({ name: null, mode: "note" })}>
            {t("doc.addNote")}
          </button>
          {!docs.some((d) => d.kind === "spec") && (
            <button className="btn small" onClick={() => setOpenDoc({ name: null, mode: "newSpec" })}>
              {t("doc.addSpec")}
            </button>
          )}
        </div>
      )}

      {!editing && (
        <>
      <TextField label={L("Status")} value={vocab("status", item.status)} />
      <TextField label={L("Priority")} value={vocab("priority", item.priority)} />
      <TextField label={L("Resolution")} value={item.resolution} />
      <TextField label={L("Area")} value={item.area} />

      {item.parentUid && (
        <Field label={L("Parent")}>
          <button className="chip" onClick={() => onSelect(item.parentUid!)}>
            {item.parent}
            {parent ? ` — ${parent.title}` : ""}
          </button>
        </Field>
      )}
      {item.required_for_parent != null && (
        <TextField label={L("Required for parent")} value={t(item.required_for_parent ? "yes" : "no")} />
      )}

      {item.dependencyUids.length > 0 && (
        <Field label={L("Dependencies")}>
          <span className="chip-list">
            {item.dependencyUids.map((uid) => (
              <button key={uid} className="chip" onClick={() => onSelect(uid)}>
                {byUid.get(uid)?.id ?? uid}
              </button>
            ))}
          </span>
        </Field>
      )}

      {children.length > 0 && (
        <Field label={t("detail.children")}>
          <span className="chip-list">
            {children.map((c) => (
              <button key={c.key} className="chip" onClick={() => onSelect(c.uid)}>
                {c.id}
                {c.required_for_parent === false ? ` (${t("optional")})` : ""}
              </button>
            ))}
          </span>
        </Field>
      )}

      <TextField label={L("Goal")} value={item.goal} />
      <TextField label={L("Completion criteria")} value={item.completion_criteria} />
      <TextField label={L("Created")} value={item.created} />
      {Object.entries(item.extra_fields).map(([k, v]) => (
        <TextField key={k} label={L(k)} value={v} />
      ))}
      <TextField
        label={t("detail.source")}
        value={`${sourcePath ?? item.project}\n${t(item.archived ? "detail.archived" : "detail.active")}`}
      />
        </>
      )}

      {deleting && (
        <DeleteDialog
          item={item}
          onClose={() => setDeleting(false)}
          onDeleted={() => {
            setDeleting(false);
            onClose();
          }}
        />
      )}
      {creatingChild && (
        <CreateItemDialog
          sources={sources}
          sourceId={item.source_id}
          parent={item}
          onClose={() => setCreatingChild(false)}
          onCreated={(uid) => {
            setCreatingChild(false);
            onSelect(uid);
          }}
        />
      )}
      {openDoc && (
        <Suspense fallback={null}>
          <DocumentDialog item={item} initialName={openDoc.name} initialMode={openDoc.mode} onClose={() => setOpenDoc(null)} />
        </Suspense>
      )}
    </aside>
  );
}
