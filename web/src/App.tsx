import { lazy, Suspense, useCallback, useMemo, useState } from "react";
import type { SourceStatus } from "./api/client";
import { useRemoveSource } from "./api/queries";
import { DetailPanel } from "./components/DetailPanel";
import { Sidebar } from "./components/Sidebar";
import { SourceDialog } from "./components/SourceDialog";
import type { Uid } from "./domain/model";
import { createI18n, describeError, I18nContext } from "./i18n/i18n";
import type { MessageKey } from "./i18n/messages";
import { useBacklogModel } from "./state/useBacklogModel";
import { UiStateContext, useUiStateStore } from "./state/useUiStateStore";
import { type View, VIEWS } from "./state/uiState";
import { KanbanView } from "./views/KanbanView";
import { TreeView } from "./views/TreeView";

// React Flow + dagre are only loaded when the dependency view is opened.
const GraphView = lazy(() => import("./views/GraphView").then((m) => ({ default: m.GraphView })));

const TAB_LABELS: Record<View, MessageKey> = { tree: "tab.tree", graph: "tab.graph", kanban: "tab.kanban" };

type SourceDialogState = { source: SourceStatus | null } | null;

export function App() {
  const [state, dispatch] = useUiStateStore();
  const i18n = useMemo(() => createI18n(state.lang), [state.lang]);
  const uiContext = useMemo(() => ({ state, dispatch }), [state, dispatch]);
  const model = useBacklogModel(state);
  const removeSource = useRemoveSource();
  const [sourceDialog, setSourceDialog] = useState<SourceDialogState>(null);

  const select = useCallback((uid: Uid | null) => dispatch({ type: "select", uid }), [dispatch]);
  const selected = state.selectedId ? model.byUid.get(state.selectedId) : undefined;

  const onRemoveSource = (source: SourceStatus) => {
    if (!window.confirm(i18n.t("source.confirmRemove", { p: source.project, path: source.path }))) return;
    removeSource.mutate(source.id, {
      onError: (e) => window.alert(i18n.t("err.generic", { e: describeError(i18n, e) })),
    });
  };

  const views: Record<View, () => React.ReactNode> = {
    tree: () => <TreeView visible={model.visible} items={model.items} onSelect={select} />,
    kanban: () => <KanbanView visible={model.visible} items={model.items} onSelect={select} />,
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
            </nav>
            <div className="content">
              {model.error && !model.items.length ? (
                <div className="load-error">{i18n.t("err.load", { e: describeError(i18n, model.error) })}</div>
              ) : (
                views[state.currentView]()
              )}
              {selected && (
                <DetailPanel
                  key={selected.uid}
                  item={selected}
                  items={model.items}
                  byUid={model.byUid}
                  sourcePath={model.sources.find((s) => s.id === selected.ref.source_id)?.path}
                  onSelect={select}
                  onClose={() => select(null)}
                />
              )}
            </div>
          </main>
        </div>
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
      </UiStateContext.Provider>
    </I18nContext.Provider>
  );
}
