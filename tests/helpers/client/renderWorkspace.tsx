import { render } from "@testing-library/react";
import type { ComponentType, ReactElement } from "react";
import { I18nextProvider } from "react-i18next";
import { MemoryRouter } from "react-router";
import { initI18n, PluginRegistryProvider, StoreProvider } from "../../../client/src/core";
import type { ActivePlugin, PluginRegistry, WidgetContribution } from "../../../client/src/core/plugins/types";
import alarmsDe from "../../../client/src/plugins/alarms/locales/de.json";
import alarmsEn from "../../../client/src/plugins/alarms/locales/en.json";
import backlogDe from "../../../client/src/plugins/backlog/locales/de.json";
import backlogEn from "../../../client/src/plugins/backlog/locales/en.json";
import notesDe from "../../../client/src/plugins/notes/locales/de.json";
import notesEn from "../../../client/src/plugins/notes/locales/en.json";
import de from "../../../client/src/plugins/workspace/locales/de.json";
import en from "../../../client/src/plugins/workspace/locales/en.json";
import { fakeWorkspaceBackend } from "./fakeWorkspaceBackend";

/** A plugin of the test that hangs a create form into `workspace.create-types`; its title is `create.<name>`. */
export interface CreateType {
	ownerId: string;
	name: string;
	title: string;
	form: ComponentType;
}

/** Renders a component of the workspace plugin with store, texts, router and the widgets of the test plugins. */
export async function renderWorkspace(
	ui: ReactElement,
	options: {
		backend?: ReturnType<typeof fakeWorkspaceBackend>;
		createTypes?: CreateType[];
		/** Widgets of other slots, e.g. `backlog.item-detail`. */
		widgets?: Array<{ ownerId: string; slot: string; name: string; component: ComponentType }>;
	} = {},
) {
	const backend = options.backend ?? fakeWorkspaceBackend();
	const i18n = await initI18n({ lng: "de" });
	i18n.addResourceBundle("de", "workspace", de);
	i18n.addResourceBundle("en", "workspace", en);
	i18n.addResourceBundle("de", "backlog", backlogDe);
	i18n.addResourceBundle("en", "backlog", backlogEn);
	i18n.addResourceBundle("de", "alarms", alarmsDe);
	i18n.addResourceBundle("en", "alarms", alarmsEn);
	i18n.addResourceBundle("de", "notes", notesDe);
	i18n.addResourceBundle("en", "notes", notesEn);
	const active: ActivePlugin[] = [];
	for (const type of options.createTypes ?? []) {
		i18n.addResourceBundle("de", type.ownerId, { create: { [type.name]: type.title } });
		const widget: WidgetContribution = { slot: "workspace.create-types", name: type.name, component: type.form };
		active.push({ id: type.ownerId, definition: { i18n: { de: {}, en: {} }, contributions: [widget] } });
	}
	for (const widget of options.widgets ?? []) {
		const contribution: WidgetContribution = { slot: widget.slot, name: widget.name, component: widget.component } as WidgetContribution;
		active.push({ id: widget.ownerId, definition: { i18n: { de: {}, en: {} }, contributions: [contribution] } });
	}
	const registry = { active: () => active, statuses: () => [] } as unknown as PluginRegistry;
	const result = render(
		<I18nextProvider i18n={i18n}>
			<StoreProvider store={backend.store}>
				<PluginRegistryProvider registry={registry}>
					<MemoryRouter>{ui}</MemoryRouter>
				</PluginRegistryProvider>
			</StoreProvider>
		</I18nextProvider>,
	);
	return { backend, i18n, ...result };
}
