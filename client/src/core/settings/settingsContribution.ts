import SettingsIcon from "@mui/icons-material/Settings";
import type { MainContribution } from "../plugins/types";

/** The main route `core/settings` (a tab): its page lists the sections of the slot `core.settings-sections`. */
export const settingsContribution: MainContribution = {
	slot: "core.main",
	name: "settings",
	title: "settings.tab",
	icon: SettingsIcon,
	page: () => import("./SettingsPage"),
	layout: { header: true },
};
