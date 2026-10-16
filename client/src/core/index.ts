// Public API of the core (architecture rule 2). Other layers import only from here.

export { failureKindOfStatus, type BackendFailureKind } from "./backend/classifyFailure";
export { BackendUnreachableError } from "./backend/types";
export { createConnectionMonitor, type ConnectionMonitor } from "./backend/createConnectionMonitor";
export type { ConnectionMonitorOptions, ConnectionSettings } from "./backend/types";
export { createConnection } from "./api/createConnection";
export { createPluginApi } from "./api/createPluginApi";
export type { Connection, ConnectionError, ConnectionFetch, CreateConnectionOptions, PluginApi, StoreExtra } from "./api/types";
export { initI18n, type InitI18nOptions } from "./i18n/initI18n";
export { AppRouter } from "./navigation/AppRouter";
export { createAppRouter, type AppRouterInstance, type AppRouterOptions, type DevRoute } from "./navigation/createAppRouter";
export type { NavigationConfig } from "./navigation/types";
export { RootLayout } from "./navigation/RootLayout";
export { viewPath } from "./navigation/paths";
export { usePageHeader } from "./navigation/usePageHeader";
export { createModals } from "./modals/createModals";
export { ModalHost } from "./modals/ModalHost";
export { modals } from "./modals/modals";
export type { Text } from "./modals/text";
export type {
	AlertRequest,
	ConfirmBodyProps,
	ConfirmRequest,
	ConfirmWithBodyRequest,
	ConfirmWithBodyResult,
	DetailRow,
	Modals,
	ModalSeverity,
	ModalWidth,
	PendingModal,
} from "./modals/types";
export { useModals } from "./modals/useModals";
export { banners } from "./banners/banners";
export { createBanners } from "./banners/createBanners";
export type {
	BannerAction,
	BannerHandle,
	BannerRequest,
	BannerSettings,
	BannerSeverity,
	Banners,
	VisibleBanner,
} from "./banners/types";
export { useBanners } from "./banners/useBanners";
export { createErrors } from "./errors/createErrors";
export { errors } from "./errors/errors";
export { ErrorBoundary, type ErrorBoundaryProps } from "./errors/ErrorBoundary";
export { installGlobalErrorHandlers } from "./errors/installGlobalErrorHandlers";
export { createRootErrorHandlers } from "./errors/rootErrorHandlers";
export type { Errors, ReportError, ReportErrorInput } from "./errors/types";
export { useReportError } from "./errors/useReportError";
export { ConsoleSink } from "./logging/ConsoleSink";
export { createLogging } from "./logging/createLogging";
export { logging } from "./logging/logging";
export { LoggerOriginProvider } from "./logging/LoggerOriginProvider";
export { MemorySink } from "./logging/MemorySink";
export { toLoggable, type LoggableLimits } from "./logging/toLoggable";
export type {
	Logger,
	LogEntry,
	LogInput,
	LogLevel,
	Logging,
	LoggingConfig,
	LogSink,
	SinkContext,
	SinkLevels,
} from "./logging/types";
export { useLogger } from "./logging/useLogger";
export { PluginSelectionError, type PluginSelectionErrorDetail } from "./plugins/PluginSelectionError";
export { useSlot, useActiveRoute, selectSlotEntries, type SlotEntry } from "./plugins/useSlot";
export { createPluginRegistry } from "./plugins/createPluginRegistry";
export { definePlugin } from "./plugins/definePlugin";
export { PluginErrorNotice } from "./plugins/PluginErrorNotice";
export { PluginRegistryProvider } from "./plugins/PluginRegistryProvider";
export type {
	ActivePlugin,
	Contribution,
	EventContext,
	EventHandler,
	FrameProps,
	SlotDeclaration,
	WidgetContribution,
	MainContribution,
	PluginCatalogue,
	PluginCatalogueEntry,
	PluginDefinition,
	PluginRegistry,
	PluginSelection,
	PluginStatus,
	PluginStatusCode,
} from "./plugins/types";
export { usePluginRegistry } from "./plugins/usePluginRegistry";
export { startEvents, type StartEventsOptions } from "./events/startEvents";
export { createEventStream, type EventSourceLike, type EventStream, type EventStreamOptions } from "./events/createEventStream";
export { createEventRouter, reconnectedTopic, type EventRouter } from "./events/createEventRouter";
export { coreApi, useGetUiStateQuery, type UiState, type UiStateDocument } from "./ui-state/coreApi";
export { usePersistentState, type PersistentSetter } from "./ui-state/usePersistentState";
export { flushUiState, selectUiDocument, setUiStateValue, uiStateWriteDelayMs, type UiStateStore } from "./ui-state/uiState";
export { LanguageSync } from "./ui-state/LanguageSync";
export { settingsContribution } from "./settings/settingsContribution";
export { createAppStore, type AppState, type AppStore } from "./store/createAppStore";
export { useAppDispatch, useAppSelector } from "./store/hooks";
export { StoreProvider } from "./store/StoreProvider";
export { coreTestIds } from "./testIds";
export { theme, viewerColors } from "./theme/theme";
