import { useMemo } from "react";
import { Sidebar } from "./components/Sidebar";
import { createI18n, describeError, I18nContext } from "./i18n/i18n";
import type { MessageKey } from "./i18n/messages";
import { useBacklogModel } from "./state/useBacklogModel";
import { UiStateContext, useUiStateStore } from "./state/useUiStateStore";
import { type View, VIEWS } from "./state/uiState";

const TAB_LABELS: Record<View, MessageKey> = { tree: "tab.tree", graph: "tab.graph", kanban: "tab.kanban" };

export function App() {
  const [state, dispatch] = useUiStateStore();
  const i18n = useMemo(() => createI18n(state.lang), [state.lang]);
  const uiContext = useMemo(() => ({ state, dispatch }), [state, dispatch]);
  const model = useBacklogModel(state);

  return (
    <I18nContext.Provider value={i18n}>
      <UiStateContext.Provider value={uiContext}>
        <div className="app" lang={state.lang}>
          <Sidebar
            options={model.options}
            sources={model.sources}
            onAddSource={() => undefined}
            onEditSource={() => undefined}
            onRemoveSource={() => undefined}
          />
          <main className="main">
            <nav className="tabs">
              {VIEWS.map((view) => (
                <button
                  key={view}
                  className={`tab-btn${state.currentView === view ? " active" : ""}`}
                  onClick={() => dispatch({ type: "view", view })}
                >
                  {i18n.t(TAB_LABELS[view])}
                </button>
              ))}
            </nav>
            <div className="content">
              {model.error ? (
                <div className="load-error">{i18n.t("err.load", { e: describeError(i18n, model.error) })}</div>
              ) : (
                <div className="view">
                  <p className="empty-hint">
                    {model.visible.length} / {model.items.length}
                  </p>
                </div>
              )}
            </div>
          </main>
        </div>
      </UiStateContext.Provider>
    </I18nContext.Provider>
  );
}
