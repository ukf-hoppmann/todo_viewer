import { lazy, Suspense, useCallback, useMemo, useState } from "react";
import type { Schemas, SourceStatus } from "./api/client";
import { useRemoveSource, useSyncStatuses } from "./api/queries";
import { CreateItemDialog } from "./components/CreateItemDialog";
import { DetailPanel } from "./components/DetailPanel";
import { RetypeNotice } from "./components/RetypeNotice";
import { SettingsDialog } from "./components/settings/SettingsDialog";
import { Sidebar } from "./components/Sidebar";
import { SourceDialog } from "./components/SourceDialog";
import { SyncDialog } from "./components/SyncDialog";
import type { SyncMode, SyncState } from "./domain/sync";
import { type Uid, uidOf } from "./domain/model";
import { createI18n, describeError, I18nContext } from "./i18n/i18n";
import type { MessageKey } from "./i18n/messages";
import { useBacklogModel } from "./state/useBacklogModel";
import { UiStateContext, useUiStateStore } from "./state/useUiStateStore";
import { type View, VIEWS } from "./state/uiState";
import { KanbanView } from "./views/KanbanView";
import { NotesView } from "./views/NotesView";
import { TrashView } from "./views/TrashView";
import { TreeView } from "./views/TreeView";

// React Flow + dagre are only loaded when the dependency view is opened.
const GraphView = lazy(() => import("./views/GraphView").then((m) => ({ default: m.GraphView })));

const TAB_LABELS: Record<View, MessageKey> = { tree: "tab.tree", graph: "tab.graph", kanban: "tab.kanban", notes: "tab.notes", trash: "tab.trash" };

type SourceDialogState = { source: SourceStatus | null } | null;
type SyncDialogState = { source: SourceStatus; mode: SyncMode } | null;

export function App() {
  const [state, dispatch] = useUiStateStore();
  const i18n = useMemo(() => createI18n(state.lang), [state.lang]);
  const uiContext = useMemo(() => ({ state, dispatch }), [state, dispatch]);
  const model = useBacklogModel(state);
  const removeSource = useRemoveSource();
  const [sourceDialog, setSourceDialog] = useState<SourceDialogState>(null);
  const [syncDialog, setSyncDialog] = useState<SyncDialogState>(null);
  const [creating, setCreating] = useState(false);
  // null = closed; focusId is the project the menu was opened for (from its badge), if any.
  const [settings, setSettings] = useState<{ focusId?: string } | null>(null);
  const syncStatuses = useSyncStatuses();
  const syncStates = useMemo(() => new Map<string, SyncState>(syncStatuses.data?.map((s) => [s.source_id, s.state])), [syncStatuses.data]);
  // Kept here, not in the detail panel: the panel is rebuilt when the selection moves to the new id.
  const [retyped, setRetyped] = useState<Schemas["RetypeOut"] | null>(null);

  const select = useCallback((uid: Uid | null) => dispatch({ type: "select", uid }), [dispatch]);
  const selected = state.selectedId ? model.byUid.get(state.selectedId) : undefined;

  const onRemoveSource = (source: SourceStatus) => {
    const text = source.backend === "database"
      ? i18n.t("source.confirmRemoveDb", { p: source.project })
      : i18n.t("source.confirmRemove", { p: source.project, path: source.path });
    if (!window.confirm(text)) return;
    removeSource.mutate(source.id, {
      onError: (e) => window.alert(i18n.t("err.generic", { e: describeError(i18n, e) })),
    });
  };

  const views: Record<View, () => React.ReactNode> = {
    tree: () => <TreeView visible={model.visible} items={model.items} onSelect={select} />,
    kanban: () => <KanbanView visible={model.visible} items={model.items} onSelect={select} />,
    notes: () => <NotesView items={model.items} />,
    trash: () => <TrashView sources={model.sources} />,
    graph: () => (
      <Suspense fallback={<div className="view" />}>
        <GraphView visible={model.visible} items={model.items} onSelect={select} />
      </Suspense>
    ),
  };

  return (
    <I18nContext.Provider value={i18n}>
      <UiStateContext.Provider value={uiContext}>
        <div className="app" lang={state.lang}>
          <Sidebar
            options={model.options}
            sources={model.sources}
            onAddSource={() => setSourceDialog({ source: null })}
            onEditSource={(source) => setSourceDialog({ source })}
            onRemoveSource={onRemoveSource}
            onSyncSource={(source) => setSyncDialog({ source, mode: "sync" })}
            onOpenSettings={() => setSettings({})}
            syncStates={syncStates}
            onOpenProject={(source) => setSettings({ focusId: source.id })}
          />
          <main className="main">
            <nav className="tabs">
              {VIEWS.map((view) => (
                <button
                  key={view}
                  className={`tab-btn${state.currentView === view ? " active" : ""}`}
                  aria-pressed={state.currentView === view}
                  onClick={() => dispatch({ type: "view", view })}
                >
                  {i18n.t(TAB_LABELS[view])}
                </button>
              ))}
              <button className="btn small new-btn" disabled={!model.sources.some((s) => !s.problem)} onClick={() => setCreating(true)}>
                {i18n.t("create.new")}
              </button>
            </nav>
            <div className="content">
              {model.error && !model.items.length ? (
                <div className="load-error">{i18n.t("err.load", { e: describeError(i18n, model.error) })}</div>
              ) : (
                views[state.currentView]()
              )}
              {selected && state.currentView !== "trash" && state.currentView !== "notes" && (
                <DetailPanel
                  key={selected.uid}
                  item={selected}
                  items={model.items}
                  byUid={model.byUid}
                  sourcePath={model.sources.find((s) => s.id === selected.source_id)?.path}
                  sources={model.sources}
                  onSelect={select}
                  onRetyped={(result) => {
                    select(uidOf(result.item.project, result.item.id));
                    setRetyped(result);
                  }}
                  onClose={() => select(null)}
                />
              )}
            </div>
          </main>
        </div>
        {creating && (
          <CreateItemDialog
            sources={model.sources}
            sourceId={selected?.source_id ?? model.sources.find((s) => !s.problem)?.id ?? ""}
            parent={null}
            onClose={() => setCreating(false)}
            onCreated={(uid) => {
              setCreating(false);
              select(uid);
            }}
          />
        )}
        {settings && (
          <SettingsDialog
            initialSection={settings.focusId ? "projects" : undefined}
            focusId={settings.focusId}
            onClose={() => setSettings(null)}
          />
        )}
        {retyped && <RetypeNotice result={retyped} onClose={() => setRetyped(null)} />}
        {sourceDialog && (
          <SourceDialog
            source={sourceDialog.source}
            onClose={() => setSourceDialog(null)}
            onSaved={(project) => {
              dispatch({ type: "showProject", project });
              setSourceDialog(null);
            }}
          />
        )}
        {syncDialog && (
          <SyncDialog
            source={syncDialog.source}
            mode={syncDialog.mode}
            onClose={() => setSyncDialog(null)}
            onSwitched={(project) => {
              dispatch({ type: "showProject", project });
              setSyncDialog(null);
            }}
          />
        )}
      </UiStateContext.Provider>
    </I18nContext.Provider>
  );
}
