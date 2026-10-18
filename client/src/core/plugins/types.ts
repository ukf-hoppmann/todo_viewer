import type { Reducer, UnknownAction } from "@reduxjs/toolkit";
import type { ComponentType, ReactNode } from "react";
import type { PluginApi } from "../api/types";
import type { SupportedLanguage } from "../i18n/initI18n";
import type { LogEntry } from "../logging/types";

/** The switch of one plugin. */
export interface PluginConfig {
	enabled: boolean;
}

/** Which plugins are switched on; `src/app` builds it from its fixed list. */
export interface PluginSelection {
	/** Keyed by plugin id; a plugin that is missing is switched off. */
	plugins: Record<string, PluginConfig>;
}

/** The manifest `plugin.json` of a plugin; matches `pluginManifest.schema.json`. */
export interface PluginManifest {
	/** Ids of the plugins this plugin needs. */
	requires: string[];
}

/** Lazy import of a page; its default export is the component. */
export type PageLoader = () => Promise<{ default: ComponentType }>;

interface ContributionBase {
	/** Kebab-case; unique per owner and slot; part of the URL and of the test id. */
	name: string;
	/** Translation key in the namespace of the owner. */
	title: string;
	/** Icon component of the owner's choice (MUI icon or own SVG). */
	icon: ComponentType;
}

/** The areas of the sub layout a main route asks for; each defaults to `false`. */
export interface MainLayout {
	/** A header area above the content, filled by the page with `usePageHeader`. */
	header?: boolean;
	/** A sidebar at the left, filled with the sections of the slot `core.sidebar-sections`. */
	sidebar?: boolean;
	/** A detail column at the right, filled by the page with `usePageDetail`; shown only while it has content. */
	detail?: boolean;
}

/**
 * A main route: a tab of the app bar and the page behind it.
 * Reachable at `/<owner id>/<name>` (architecture rule 4).
 */
export interface MainContribution extends ContributionBase {
	slot: "core.main";
	page: PageLoader;
	layout?: MainLayout;
}

/**
 * A component hung into a slot that an owner provides (`<owner id>.<name>`), for example a section of the
 * settings page or a counter in the header. The owner of the slot decides where it is drawn.
 */
export interface WidgetContribution {
	slot: string;
	/** Kebab-case; unique per owner and slot; part of the test id the owner gives it. */
	name: string;
	component: ComponentType;
	/** Position among the widgets of the slot; smaller first, 0 by default. */
	order?: number;
	/** Show the widget only on these main routes (`<owner id>/<name>`); on every route if missing. */
	when?: readonly string[];
	title?: undefined;
	page?: undefined;
}

/** What a plugin or the core adds to a slot. */
export type Contribution = MainContribution | WidgetContribution;

/** A slot a plugin provides. Only widget slots exist so far; the owner draws the components with `useSlot`. */
export interface SlotDeclaration {
	/** English, for developers: what belongs into the slot. */
	description: string;
}

/** What the core hands to a handler of a server event. */
export interface EventContext {
	/** The store's `dispatch`, e.g. to invalidate tags of the plugin's own API. */
	dispatch: (action: UnknownAction) => unknown;
	/** The plugin's own API (`createPluginApi`), if it has one. */
	api: (PluginApi & { util?: { invalidateTags: (tags: string[]) => UnknownAction } }) | undefined;
}

/** Reacts to one server event (`event: <topic>`, JSON payload). */
export type EventHandler = (payload: unknown, context: EventContext) => void;

/** What the frame component of the layout plugin gets. */
export interface FrameProps {
	/** The tabs of the main routes, ready to put into the app bar. */
	tabs: ReactNode;
	/** The route's page and the notice about failed plugins. */
	children: ReactNode;
}

/**
 * What a plugin contributes, exported as `plugin` from its `index.ts`.
 */
export interface PluginDefinition {
	/** Texts per language; registered in the namespace `<plugin id>`. */
	i18n: Record<SupportedLanguage, Record<string, unknown>>;
	/** Contributions to slots, e.g. tabs; any number. */
	contributions?: readonly Contribution[];
	/**
	 * The reducer of the plugin's compartment in the global store, usually the
	 * `reducer` of its `createSlice`. At most one; a plugin that needs several
	 * combines them itself. The core puts it under the plugin id, whatever the
	 * slice is called.
	 */
	reducer?: Reducer;
	/**
	 * The plugin's own API with its cache, built with `createPluginApi` on the
	 * connection of the core. At most one. The core puts its cache and
	 * middleware into the store under `<plugin id>.api` when the plugin is
	 * active; a key that is not exactly that makes the plugin `failed`.
	 */
	api?: PluginApi;
	/** The slots this plugin provides, by name (kebab-case); contributions use `<plugin id>.<name>`. */
	slots?: Record<string, SlotDeclaration>;
	/** Reactions to server events, by topic (`<owner>.<name>`; `core.reconnected` after a reconnect). */
	eventHandlers?: Record<string, EventHandler>;
	/** The frame around the routes (app bar, sidebar); at most one active plugin provides it. */
	frame?: ComponentType<FrameProps>;
}

/** One plugin as `src/app` finds it: the raw manifest and the loader of its `index.ts`. */
export interface PluginCatalogueEntry {
	/** Content of `plugin.json`; `undefined` if the file is missing. */
	manifest: unknown;
	/** Imports `index.ts`; missing if the file is missing. */
	load?: () => Promise<unknown>;
}

/** All plugins of the build, keyed by plugin id (the folder name). */
export type PluginCatalogue = Record<string, PluginCatalogueEntry>;

export type PluginStatusCode =
	/** The folder name is not kebab-case or is reserved (`core`, `dev`). */
	| "id-invalid"
	/** `plugin.json` is missing or violates its schema. */
	| "manifest-invalid"
	/** `index.ts` is missing. */
	| "definition-missing"
	/** `requires` names a plugin that does not exist. */
	| "requires-unknown"
	/** The plugin is part of a cycle in `requires`. */
	| "requires-cycle"
	/** Importing `index.ts` failed. */
	| "import-failed"
	/** The export `plugin` is missing or invalid (including a bad `reducer`, `api`, or contribution). */
	| "definition-invalid"
	/** An entry hangs into a sidebar that does not exist, or whose host the plugin does not require. */
	| "contribution-invalid"
	/** A required plugin failed, directly or indirectly. */
	| "requires-failed"
	/** A required plugin is switched off, directly or indirectly. */
	| "requires-disabled";

export interface PluginStatus {
	id: string;
	status: "active" | "disabled" | "blocked" | "failed";
	code?: PluginStatusCode;
	/** For log and diagnosis; English. */
	message?: string;
	/** With `blocked`: the required plugins down to the cause, e.g. `["b", "c"]`. */
	cause?: string[];
	/** With `failed`: the original error, if there is one. */
	error?: unknown;
	/** With `failed` and `requires-failed`: the log entry of the report; its id lets support find it. */
	logEntry?: LogEntry;
}

export interface ActivePlugin {
	id: string;
	definition: PluginDefinition;
}

/** The plugins of this start; unchangeable once created. */
export interface PluginRegistry {
	/** Active plugins in topological order of `requires`. */
	active(): readonly ActivePlugin[];
	/** Status of every plugin, sorted by id. */
	statuses(): readonly PluginStatus[];
}
