import { lazy, type ReactNode, Suspense, useState } from "react";
import { type Item, priorityOptions, statusOptions, type Uid, YES_NO } from "../domain/model";
import { useI18n } from "../i18n/i18n";
import { documentLinks } from "./documentLinks";

// marked + DOMPurify are only loaded when a document is opened.
const DocumentDialog = lazy(() => import("./DocumentDialog").then((m) => ({ default: m.DocumentDialog })));
import { EditableField } from "./EditableField";

interface DetailPanelProps {
  item: Item;
  items: Item[];
  byUid: Map<Uid, Item>;
  sourcePath: string | undefined;
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

export function DetailPanel({ item, items, byUid, sourcePath, onSelect, onClose }: DetailPanelProps) {
  const { t, vocab } = useI18n();
  const [openDoc, setOpenDoc] = useState<string | null>(null);
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
        {[item.ref.id, vocab("type", item.type), item.project, item.ref.location === "archive" ? t("detail.archived") : null]
          .filter(Boolean)
          .join(" · ")}
      </div>

      {item.summary && <div className="detail-summary">{item.summary}</div>}

      {docs.length > 0 && (
        <div className="doc-buttons">
          {docs.map((d, n) => (
            <button key={d.path} className="btn small" onClick={() => setOpenDoc(d.path)}>
              {n < item.notes.length ? "📝" : "📐"} {d.label}
            </button>
          ))}
        </div>
      )}

      <Field label={L("Status")}>
        <EditableField item={item} field="status" ariaLabel={L("Status")} options={statusOptions(item)} label={(v) => vocab("status", v)} />
      </Field>
      {item.format === "checkbox" ? (
        <TextField label={L("Priority")} value={vocab("priority", item.priority)} />
      ) : (
        <Field label={L("Priority")}>
          <EditableField item={item} field="priority" ariaLabel={L("Priority")} options={priorityOptions(item)} label={(v) => vocab("priority", v)} />
        </Field>
      )}
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
      {item.format === "checkbox" ? null : item.parent || item.required_for_parent != null ? (
        <Field label={L("Required for parent")}>
          <EditableField
            item={item}
            field="required_for_parent"
            ariaLabel={L("Required for parent")}
            options={[...YES_NO]}
            label={(v) => t(v === "Yes" ? "yes" : "no")}
          />
        </Field>
      ) : null}

      {item.dependencyUids.length > 0 && (
        <Field label={L("Dependencies")}>
          <span className="chip-list">
            {item.dependencyUids.map((uid) => (
              <button key={uid} className="chip" onClick={() => onSelect(uid)}>
                {byUid.get(uid)?.ref.id ?? uid}
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
                {c.ref.id}
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
        value={`${sourcePath ?? item.project}\n${t(item.ref.location === "archive" ? "detail.archived" : "detail.active")}, ${t("detail.line")} ${item.ref.line}`}
      />

      {openDoc && (
        <Suspense fallback={null}>
          <DocumentDialog item={item} initialPath={openDoc} onClose={() => setOpenDoc(null)} />
        </Suspense>
      )}
    </aside>
  );
}
