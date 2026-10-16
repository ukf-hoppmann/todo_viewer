import ExtensionIcon from "@mui/icons-material/Extension";
import { definePlugin } from "../../core";
import de from "./locales/de.json";
import en from "./locales/en.json";
import fr from "./locales/fr.json";

/**
 * Second example plugin without business logic: it hangs the entry `panel`
 * into the sidebar of the tab `hub` of the plugin `example`. It requires
 * `example` (see `plugin.json`), so it is inactive whenever `example` is.
 * Texts are used with `useTranslation("example-addon")`.
 */
export const plugin = definePlugin({
	i18n: { de, en, fr },
	contributions: [
		{
			slot: "example.hub",
			name: "panel",
			title: "entry.panel",
			icon: ExtensionIcon,
			page: () => import("./pages/PanelPage"),
		},
	],
});
