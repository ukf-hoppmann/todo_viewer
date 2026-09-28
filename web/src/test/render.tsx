import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { type ReactElement, useReducer } from "react";
import type { ApiItem } from "../api/client";
import { createI18n, I18nContext } from "../i18n/i18n";
import { UiStateContext } from "../state/useUiStateStore";
import { INITIAL_UI_STATE, type UiState, uiReducer } from "../state/uiState";

function Providers({ children, initial }: { children: ReactElement; initial: UiState }) {
  const [state, dispatch] = useReducer(uiReducer, initial);
  return (
    <I18nContext.Provider value={createI18n(state.lang)}>
      <UiStateContext.Provider value={{ state, dispatch }}>{children}</UiStateContext.Provider>
    </I18nContext.Provider>
  );
}

/** Renders with real UI state, German texts and a fresh query client. */
export function renderWithProviders(ui: ReactElement, initial: Partial<UiState> = {}) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <Providers initial={{ ...INITIAL_UI_STATE, ...initial }}>{ui}</Providers>
    </QueryClientProvider>,
  );
}

export function apiItem(id: string, overrides: Partial<ApiItem> = {}): ApiItem {
  return {
    key: `s/${id}`,
    source_id: "s",
    id,
    version: `v-${id}`,
    archived: false,
    project: "P",
    type: "Task",
    title: `Title ${id}`,
    status: "Open",
    parent: null,
    required_for_parent: null,
    dependencies: [],
    created: null,
    area: null,
    priority: null,
    goal: null,
    completion_criteria: null,
    summary: null,
    resolution: null,
    documents: [],
    deleted: null,
    extra_fields: {},
    archive_supported: true,
    ...overrides,
  };
}
