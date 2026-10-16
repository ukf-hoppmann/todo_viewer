import type { Reducer } from "@reduxjs/toolkit";
import type { ComponentType } from "react";
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

/**
 * A main route with a page: a tab of the app bar and the page behind it.
 * Reachable at `/<owner id>/<name>` (architecture rule 4).
 */
export interface MainPageContribution extends ContributionBase {
	slot: "core.main";
	page: PageLoader;
	/** Areas of the sub layout the main route asks for; each defaults to `false`. */
	layout?: { header?: boolean; sidebar?: false };
}

/**
 * A main route with a sidebar instead of a page: it opens the slot
 * `<owner id>.<name>`, into which the owner and plugins that require the owner
 * hang entries. The page shown is that of the selected entry.
 */
export interface MainSidebarContribution extends ContributionBase {
	slot: "core.main";
	page?: undefined;
	layout: { header?: boolean; sidebar: true };
}

export type MainContribution = MainPageContribution | MainSidebarContribution;

/**
 * An entry of a sidebar: a sub-route of the main route that opens the slot
 * `<host id>.<host name>`. Reachable at `/<host id>/<host name>/<owner id>/<name>`.
 */
export interface SidebarContribution extends ContributionBase {
	slot: string;
	page: PageLoader;
	layout?: undefined;
}

/** What a plugin or the core adds to a slot. */
export type Contribution = MainContribution | SidebarContribution;

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
