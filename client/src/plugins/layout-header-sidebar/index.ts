import LooksOneIcon from "@mui/icons-material/LooksOne";
import LooksTwoIcon from "@mui/icons-material/LooksTwo";
import VerticalSplitIcon from "@mui/icons-material/VerticalSplit";
import { definePlugin } from "../../core";
import de from "./locales/de.json";
import en from "./locales/en.json";

/**
 * Example plugin for one variant of the base layout: global header, sub header and sidebar.
 * It contains no business logic. Texts are used with `useTranslation("layout-header-sidebar")`.
 */
export const plugin = definePlugin({
	i18n: { de, en },
	contributions: [
		{
			slot: "core.main",
			name: "main",
			title: "tab.main",
			icon: VerticalSplitIcon,
			layout: { header: true, sidebar: true },
		},
		{
			slot: "layout-header-sidebar.main",
			name: "first",
			title: "entry.first",
			icon: LooksOneIcon,
			page: () => import("./pages/FirstPage"),
		},
		{
			slot: "layout-header-sidebar.main",
			name: "second",
			title: "entry.second",
			icon: LooksTwoIcon,
			page: () => import("./pages/SecondPage"),
		},
	],
});
